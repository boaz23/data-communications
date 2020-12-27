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