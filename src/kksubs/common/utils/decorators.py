import logging
logger = logging.getLogger(__name__)

def spacing(func):
    def _func(*args, **kwargs):
        print('')
        result = func(*args, **kwargs)
        print('')
        return result
    return _func

def deprecated(func):
    def _func(*args, **kwargs):
        logger.warning(f'This function/method {func.__name__} is deprecated.')
        result = func(*args, **kwargs)
        return result
    return _func
