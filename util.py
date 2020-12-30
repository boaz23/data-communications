"""Various general stuff
"""
import sys
import threading
import time

import config


# see code form https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def print_err(*args, **kwargs):
    """Prints to stderr
    """
    print(*args, file=sys.stderr, **kwargs)


def run_and_wait_for_timed_task(task, duration, args=(), name=None):
    e = threading.Event()
    target_args = (e,) + args
    thread = threading.Thread(name=name, target=task, args=target_args)
    thread.start()
    thread.join(duration)
    e.set()
    thread.join()


def wait_retry_sleep():
    time.sleep(config.RETRY_WAIT_TIME)


def bytes_to_string(bytes):
    return bytes.hex(' ', 1).upper()


def is_printable_char(c):
    return ord(c) >= 0x20 and c != 0xFF


def char_to_string(c):
    if is_printable_char(c):
        return c
    else:
        return hex(ord(c)).upper()
