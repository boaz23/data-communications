import config
from scapy.all import *

def my_addr():
    return config.active_network_interface.addr()

def broadcast_addr():
    return config.active_network_interface.broadcast_address

class NetIf:
    def __init__(self, name, broadcast_address):
        self.if_name = name
        self.broadcast_address = broadcast_address

    def addr(self):
        return get_if_addr(config.name)