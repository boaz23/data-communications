class SocketAddress:
    def __init__(self, addr):
        self.host = addr[0]
        self.port = addr[1]

    def __eq__(self, other):
        return other and self.host == other.host and self.port == other.port

    def __hash__(self):
        return hash(self.to_tuple())

    def __str__(self):
        return f"{self.host}:{self.port}"

    def to_tuple(self):
        return (self.host, self.port)