class Group:
    """Represents a group in the server
    """
    def __init__(self, num):
        self.num = num
        self.pressed_keys_counter = 0
        self.connected_clients = {}