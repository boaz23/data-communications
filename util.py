import config
import time

def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def wait_retry():
    time.sleep(config.RETRY_TIME)