import subprocess
import os
import asyncio
import re
import logging
from pathlib import Path

import dotenv
import typer
import colorlog
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webelement import WebElement

from .ui import AsyncWebDriverWait
from .utils import tries

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
handler = colorlog.StreamHandler()

# Create a formatter with a timestamp and color
formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = typer.Typer()

async def build_driver(headless=True, user_data_dir=None):
    # service = ChromeService('/Users/ts-shivansh.saini/projects/chromedriver-mac-arm64/chromedriver')

    # Selenium internally use Selenium manager to manage web drivers if none provided
    # docs: https://www.selenium.dev/documentation/selenium_manager/#getting-selenium-manager
    service = ChromeService()
    options = webdriver.ChromeOptions()
    # default_user_data_dir = (
    #     Path.home() / ".cache" / "fck_roc_login" / "user_data"
    # )
    # _user_data_dir = user_data_dir or default_user_data_dir
    # options.add_argument(f"user-data-dir={_user_data_dir}")
    if headless:
        options.add_argument("headless")
    return webdriver.Chrome(service=service, options=options)

class RocLoginMethod(object):
    def __init__(self, driver, login_url, username, password):
        self.login_url = login_url
        self.username = username
        self.password = password
        self.driver: webdriver.Chrome = driver

    async def fill_creds(self):
        input_username: WebElement = await AsyncWebDriverWait(self.driver).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        logger.debug("sel: found username")
        input_password = await asyncio.to_thread(self.driver.find_element, By.ID, "password")
        await asyncio.to_thread(input_username.send_keys, self.username)
        await asyncio.to_thread(input_password.send_keys, self.password)
        await asyncio.sleep(0.5)
        await asyncio.to_thread(input_password.send_keys, Keys.ENTER)

    async def authorize_sso(self):
        await asyncio.to_thread(self.driver.get, self.login_url)
        # await asyncio.sleep(2)
        try:
            logger.debug("opening...")
            try:
                is_auth = await AsyncWebDriverWait(self.driver).until(
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Authenticated")
                )
                logger.info("already logged in...")
                return is_auth
            except TimeoutException:
                # not logged in
                logger.info("trying to login for the first time...")
                await self.fill_creds()
                is_auth = await AsyncWebDriverWait(self.driver).until(
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Authenticated")
                )
                
        except Exception as e:
            logger.error(e)

URL_REGEX = r'https?://[^\s\]]+'

@tries(3)
async def find_url_in_roc_output(output_stream: asyncio.StreamReader) -> str:
    await asyncio.sleep(1) # it takes time for stream to collect
    content = (await asyncio.wait_for(output_stream.read(1000), 5.0)).decode('utf-8')
    logger.debug(f'{content}')
    urls = re.findall(URL_REGEX, content)
    # logger.info(urls)
    return urls[0]

CMD_ROC = 'roc'
async def login(cluster, callback_port=None):
    logger.info(f'Logging in {cluster}...')
    driver = await build_driver()
    username = os.getenv("username")
    password = os.getenv("password")
    args = ['login', '-c', cluster, '--disable-browser'] + (['--callback-port', str(callback_port)] if callback_port else [])
    try:
        process = await asyncio.create_subprocess_exec(CMD_ROC, *args, stdout=asyncio.subprocess.PIPE)
        url = await find_url_in_roc_output(process.stdout)
        login_method = RocLoginMethod(driver, url, username, password)
        await login_method.authorize_sso()
        await process.wait()
    except subprocess.CalledProcessError as e:
        logger.error('Failed to call roc login', exc_info=True)
    except asyncio.TimeoutError as e:
        logger.fatal("Unable to read IAM login URL, maybe connection issue. Ensure VPN is connected!", exc_info=False)
    finally:
        try:
            process.terminate()
            await asyncio.to_thread(driver.quit)
        except ProcessLookupError:
            pass
        except Exception as e:
            logger.warning('Failed to terminate process', exc_info=True)

@app.command()
def main(cluster: str):
    """
    To fuck ROC login and automatically configure kubeconfig without opening the damn browser!!
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(login(cluster))
