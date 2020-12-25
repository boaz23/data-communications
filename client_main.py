import socket

import config
import network
import coder
import util
from socket_address import SocketAddress

game_offer_recv_addr = SocketAddress((network.my_addr(), config.GAME_OFFER_PORT))

def main():
    print("Client started, listening for offer requests...")
    while True:
        game_offer_addr = look_for_game()
        game_socket = establish_game_connection(game_offer_addr)

def look_for_game():
    print(f"waiting for game offer, listening on {game_offer_recv_addr}")
    try:
        game_offer_socket = init_game_offer_socket()
        game_offer = recv_game_offer(game_offer_socket)
        while game_offer is None:
            util.wait_retry()
            game_offer = recv_game_offer(game_offer_socket)
    finally:
        if game_offer_socket is not None:
            game_offer_socket.close()
        game_offer_socket = None
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
            util.print_err(f"error creating the game offer socket {e}")
            game_offer_socket = None
            util.wait_retry()
    return game_offer_socket

def bind_game_offer_socket(game_offer_socket):
    global game_offer_recv_addr

    while True:
        try:
            game_offer_socket.bind(game_offer_recv_addr.to_tuple())
            break
        except OSError as e:
            util.print_err(f"error binding the game offer socket: {e}")
            util.wait_retry()

def recv_game_offer(game_offer_socket):
    try:
        message_bytes, server = game_offer_socket.recvfrom(config.GAME_OFFER_RECV_BUFFER_SIZE)
        print(f"received data from {server[0]}:{server[1]}")
        if len(message_bytes) != config.GAME_OFFER_MSG_SIZE:
            util.print_err("invalid game offer: length")
            return None
        magic_coockie = coder.decode_int(message_bytes[0:4])
        if magic_coockie != config.MAGIC_COOKIE:
            util.print_err("invalid game offer: cookie")
            return None
        msg_type = coder.decode_int(message_bytes[4:5])
        if msg_type != config.MSG_TYPE_OFFER:
            util.print_err("invalid game offer: message type")
            return None
        port = coder.decode_int(message_bytes[5:7])
        return SocketAddress((server[0], port))
    except OSError as e:
        util.print_err(f"error while receiving data from game offer socket: {e}")
        return None

def establish_game_connection(game_offer_addr):
    print(f"Received offer from {game_offer_addr.host}, attempting to connect...")
    print(f"got offer from {game_offer_addr}")


if __name__ == "__main__":
    main()