"""Data struct for game clients in the server

A class to store client related data in the server
(e.g. team name, the connection socket, etc.)
"""

from socket_address import SocketAddress

class GameClient:
    def __init__(self, accpected_client):
        self.socket = accpected_client[0]
        self.addr = SocketAddress(accpected_client[1])
        self.team_name = None
        self.group = None
        self.sent_welcome_message = False
        self.selector_events = None

    def is_registered_in_selector(self):
        return self.selector_events is not None

    def register_to_selector(self, selector, events):
        selector.register(self.socket, events, self)
        self.selector_events = events

    def modify_in_selector(self, selector, events):
        selector.modify(self.socket, events, self)
        self.selector_events = events

    def unregister_from_selector(self, selector):
        selector.unregister(self.socket)
        self.selector_events = None