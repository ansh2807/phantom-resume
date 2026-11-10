import logging
from functools import wraps


class SilentFailure:
    @staticmethod
    def wrap(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                logging.getLogger("phantom").debug("channel_failed silently")
                return None
        return inner
