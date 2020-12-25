import socket

import config
import network
import coder

def main():
    while True:
        server = look_for_game()
        while server is None:
            server = look_for_game()
        server_addr = server[0]
        port = server[1]
        print(f"offer from {server_addr}:{port}")


def look_for_game():
    game_offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    game_offer_socket.bind((network.my_addr(), config.GAME_OFFER_PORT))
    message_bytes, server_addr = game_offer_socket.recvfrom(config.MSG_TYPE_OFFER_SIZE + 1)
    if len(message_bytes) != config.GAME_OFFER_MSG_SIZE:
        return None
    magic_coockie = coder.decode_int(message_bytes[0:4])
    if magic_coockie != config.MAGIC_COOKIE:
        return None
    msg_type = coder.decode_int(message_bytes[4:5])
    if msg_type != config.MSG_TYPE_OFFER:
        return None
    port = coder.decode_int(message_bytes[5:7])
    return (server_addr, port)

if __name__ == "__main__":
    main()