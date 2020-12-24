import socket

import config

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', config.ANNOUNCMENT_PORT))

    msg, addr = s.recvfrom(2048)
    print(f"{msg}\n{addr}")

if __name__ == "__main__":
    main()