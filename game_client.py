from socket_address import SocketAddress

class GameClient:
    def __init__(self, accpected_client):
        self.socket = accpected_client[0]
        self.addr = SocketAddress(accpected_client[1])
        self.team_name = None
        self.is_invalid = False