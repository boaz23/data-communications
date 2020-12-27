"""Various general stuff
"""
import sys

import config

# see code form https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def print_err(*args, **kwargs):
    """Prints to stderr
    """
    print(*args, file=sys.stderr, **kwargs)
