class SocketAddress:
    def __init__(self, addr):
        self.host = addr[0]
        self.port = addr[1]

    def __eq__(self, other):
        return other and self.host == other.host and self.port == other.port

    def __hash__(self):
        return hash((host, port))

    def __str__(self):
        return f"{host}:{port}"