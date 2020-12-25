import scapy.all

class NetIf:
    def __init__(self, name, broadcast_address):
        self.name = name
        self.broadcast_address = broadcast_address

    def addr(self):
        return scapy.all.get_if_addr(self.name)

#--------------------
import config

def my_addr():
    return config.active_network_interface.addr()

def broadcast_addr():
    return config.active_network_interface.broadcast_address