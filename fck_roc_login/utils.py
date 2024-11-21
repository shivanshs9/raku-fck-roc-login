# import logging

class TooManyTriesException(BaseException):
    pass

def tries(times):
    def func_wrapper(f):
        async def wrapper(*args, **kwargs):
            for time in range(times):
                # logging.debug('times:', time + 1)
                # noinspection PyBroadException
                try:
                    return await f(*args, **kwargs)
                except Exception as exc:
                    pass
            raise TooManyTriesException() from exc
        return wrapper
    return func_wrapper
