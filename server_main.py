import socket

import config
import network
import coder

game_server_socket = None

def main():
    print(f"Server started listening on IP address {network.my_addr()}")
    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind((network.my_addr(), config.SERVER_GAME_PORT))
    game_server_socket.listen()

    while True:
        invite_clients()

def invite_clients():
    invite_socket = socket.socket(socket.AF_INET, config.GAME_OFFER_PROTOCOL)
    invite_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message_bytes = bytearray()
    message_bytes += coder.encode_int(config.MAGIC_COOKIE, config.MAGIC_COOCKIE_SIZE)
    message_bytes += coder.encode_int(config.MSG_TYPE_OFFER, config.MSG_TYPE_OFFER_SIZE)
    message_bytes += coder.encode_int(game_server_socket.getsockname()[1], config.PORT_INT_SIZE)
    invite_socket.sendto(message_bytes, (network.broadcast_addr(), config.GAME_OFFER_PORT))
    invite_socket.close()

if __name__ == "__main__":
    main()