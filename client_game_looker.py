"""Client logic for game lookup

Contains the logic of the client needed to look for game offers.

Functions:
    * look_for_game():
        Looks for a game offers from a server and returns its
        address and port
"""

import socket

import config
import network
import coder
import util
from socket_address import SocketAddress

# This is the address which we will listen for packets
_game_offer_recv_addr = SocketAddress(network.my_addr(), config.GAME_OFFER_PORT)

def look_for_game():
    """Looks for a game offer and returns the server with the port

    Initiates a UDP socket and listens for a game offer and
    returns the server with the port.
    """

    print(f"waiting for game offer, listening on {_game_offer_recv_addr}")
    try:
        game_offer_socket = _init_game_offer_socket()
        server_addr = _recv_game_offer(game_offer_socket)
        while server_addr is None:
            server_addr = _recv_game_offer(game_offer_socket)
    finally:
        if game_offer_socket is not None:
            game_offer_socket.close()
        game_offer_socket = None
    return server_addr

def _init_game_offer_socket():
    """Initiates the socket

    Initiates the UDP socket used to listen for packets.
    """
    game_offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    game_offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    game_offer_socket.bind(_game_offer_recv_addr.to_tuple())
    return game_offer_socket

def _recv_game_offer(game_offer_socket):
    """Receive game offer and return it

    Blocks to receive UDP packets.
    Checks if they represent a proper game offer, and if so,
    returns the server which sent the offer toghether with the port it
    said we should connected to (the port in the message)
    """
    message_bytes, server_addr = game_offer_socket.recvfrom(config.GAME_OFFER_RECV_BUFFER_SIZE)
    server_addr = SocketAddress(server_addr)
    print(f"received data from {server_addr}")
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
    return SocketAddress(server_addr.host, port)

if __name__ == "__main__":
    try:
        while True:
            server_addr = look_for_game()
            print(f"received offer from {server_addr}")
    except KeyboardInterrupt:
        pass