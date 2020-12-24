import socket
import struct

import config
import network

def main():
    print(f"Server started listening on IP address {network.my_addr()}")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(b'hello\n', ('172.1.255.255', config.ANNOUNCMENT_PORT))
    s.close()

if __name__ == "__main__":
    main()