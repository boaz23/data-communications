import socket

import config
import network
import coder
import util

def main():
    print("Client started, listening for offer requests...")
    while True:
        game_offer = look_for_game()
        game_socket = establish_game_connection(game_offer)

def look_for_game():
    print(f"waiting for game offer, listening on {network.my_addr()}:{config.GAME_OFFER_PORT}")
    game_offer_socket = None
    try:
        game_offer_socket = init_game_offer_socket()
        game_offer = recv_game_offer(game_offer_socket)
        while game_offer is None:
            util.wait_retry()
            game_offer = recv_game_offer(game_offer_socket)
    finally:
        if game_offer_socket is not None:
            game_offer_socket.close()
    return game_offer

def init_game_offer_socket():
    game_offer_socket = create_game_offer_socket()
    bind_game_offer_socket(game_offer_socket)
    return game_offer_socket

def create_game_offer_socket():
    game_offer_socket = None
    while game_offer_socket is None:
        try:
            game_offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except OSError as e:
            print_err(f"error creating the game offer socket {e}")
            game_offer_socket = None
            util.wait_retry()
    return game_offer_socket

def bind_game_offer_socket(game_offer_socket):
    while True:
        try:
            game_offer_socket.bind((network.my_addr(), config.GAME_OFFER_PORT))
            break
        except OSError as e:
            print_err(f"error binding the game offer socket: {e}")
            util.wait_retry()

def recv_game_offer(game_offer_socket):
    try:
        message_bytes, server = game_offer_socket.recvfrom(config.GAME_OFFER_RECV_BUFFER_SIZE)
        print(f"received data from {server[0]}:{server[1]}")
        if len(message_bytes) != config.GAME_OFFER_MSG_SIZE:
            print_err("invalid game offer: length")
            return None
        magic_coockie = coder.decode_int(message_bytes[0:4])
        if magic_coockie != config.MAGIC_COOKIE:
            print_err("invalid game offer: cookie")
            return None
        msg_type = coder.decode_int(message_bytes[4:5])
        if msg_type != config.MSG_TYPE_OFFER:
            print_err("invalid game offer: message type")
            return None
        port = coder.decode_int(message_bytes[5:7])
        return (server[0], port)
    except OSError as e:
        print_err(f"error while receiving data from game offer socket: {e}")
        return None

def establish_game_connection(game_offer):
    server_addr = game_offer[0]
    port = game_offer[1]
    print(f"Received offer from {server_addr}, attempting to connect...")
    print(f"got offer from {server_addr}:{port}")


if __name__ == "__main__":
    main()