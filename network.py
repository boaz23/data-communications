"""Provides network layer level functions
"""

import scapy.all


class NetIf:
    """Network Interface

    Represents a network interface we can use.
    Has a name for the interface and the address it uses for broadcasting.
    """

    def __init__(self, name, broadcast_address):
        self.name = name
        self.broadcast_address = broadcast_address

    def addr(self):
        return scapy.all.get_if_addr(self.name)


# --------------------
import config


def my_addr():
    """Current network interface IP address

    Returns the IP address for the currently active network address.
    """
    return config.active_network_interface.addr()


def broadcast_addr():
    """Current broadcast IP address

    Returns broadcast IP address for the currently active network address.
    """
    return config.active_network_interface.broadcast_address
