class SocketAddress:
    """Reprsents a TCP address

    Reprsents an address used for TCP connections:
    IP address of the host and port number
    """
    def __init__(self, addr, port=None):
        host = ''
        if isinstance(addr, tuple):
            if len(addr) != 2:
                raise ValueError("if addr is a tuple, it must be of len 2")
            host = addr[0]
            if not isinstance(host, str):
                raise ValueError("the first value of the tuple must a string of the host address")
            port = addr[1]
            if not isinstance(port, int):
                raise ValueError("the second value of the tuple must an int of the host port")
        else:
            host = addr
            if not isinstance(host, str):
                raise ValueError("the addr must a string of the host address")
            if not isinstance(port, int):
                raise ValueError("port must an int of the host port")
        self.host = host
        self.port = port

    def __eq__(self, other):
        return other and self.host == other.host and self.port == other.port

    def __hash__(self):
        return hash(self.to_tuple())

    def __str__(self):
        return f"{self.host}:{self.port}"

    def to_tuple(self):
        return (self.host, self.port)