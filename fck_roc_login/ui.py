import time
import asyncio
from collections.abc import Callable, Awaitable
from selenium.webdriver.support.wait import IGNORED_EXCEPTIONS
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.common.exceptions import TimeoutException

class AsyncWebDriverWait:
    def __init__(self,
                 driver: BaseWebDriver,
                 timeout: float = 3, poll: float = 0.5):
        self._driver = driver
        self._timeout = timeout
        self._poll = poll

    async def until(self, method: Callable[[BaseWebDriver], any], message: str = ""):
        screen = None
        stacktrace = None
        end_time = time.monotonic() + self._timeout
        while True:
            try:
                value = method(self._driver)
                if value:
                    return value
            except IGNORED_EXCEPTIONS as exc:
                screen = getattr(exc, "screen", None)
                stacktrace = getattr(exc, "stacktrace", None)
            await asyncio.sleep(self._poll)
            if time.monotonic() > end_time:
                break
        raise TimeoutException(message, screen, stacktrace)
    
    async def until_not(self, method: Callable[[BaseWebDriver], any], message: str = ""):
        screen = None
        stacktrace = None
        end_time = time.monotonic() + self._timeout
        while True:
            try:
                value = method(self._driver)
                if not value:
                    return value
            except IGNORED_EXCEPTIONS as exc:
                screen = getattr(exc, "screen", None)
                stacktrace = getattr(exc, "stacktrace", None)
            await asyncio.sleep(self._poll)
            if time.monotonic() > end_time:
                break
        raise TimeoutException(message, screen, stacktrace)
