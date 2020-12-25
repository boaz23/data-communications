import socket

import config
import network
import coder

def main():
    while True:
        game_offer = look_for_game()
        while game_offer is None:
            game_offer = look_for_game()
        server_addr = game_offer[0]
        port = game_offer[1]
        #print(f"offer from {server_addr}:{port}")


def look_for_game():
    #print(f"looking for game, listening on {network.my_addr()}:{config.GAME_OFFER_PORT}")
    game_offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    game_offer_socket.bind((network.my_addr(), config.GAME_OFFER_PORT))
    message_bytes, server = game_offer_socket.recvfrom(config.GAME_OFFER_RECV_BUFFER_SIZE)
    if len(message_bytes) != config.GAME_OFFER_MSG_SIZE:
        return None
    magic_coockie = coder.decode_int(message_bytes[0:4])
    if magic_coockie != config.MAGIC_COOKIE:
        return None
    msg_type = coder.decode_int(message_bytes[4:5])
    if msg_type != config.MSG_TYPE_OFFER:
        return None
    port = coder.decode_int(message_bytes[5:7])
    return (server[0], port)

if __name__ == "__main__":
    main()