"""Inital game connection setup and exchanges logic

Contains logic to establish a TCP game connection with the server,
exchange pre-game preparation data (team name) and wait for the game
to start
"""

import socket
import selectors
import sys

import coder
import config
from socket_address import SocketAddress


def prepare_for_game(selector: selectors.BaseSelector, server_addr: SocketAddress):
    """Creates a game connection with the server

    Creates a TCP connection with the server,
    sends the team name and waits for the game to begin.
    Returns the welcome message from the server.
    """

    game_socket_registered = False
    try:
        game_socket = _init_game_socket(server_addr)
        game_socket.connect(server_addr.to_tuple())
        game_socket.setblocking(False)
        selector.register(game_socket, selectors.EVENT_WRITE)
        game_socket_registered = True
        _send_team_name(selector, game_socket)
        return game_socket, _wait_for_game(game_socket), game_socket_registered
    except OSError:
        # error while connection/sending team name,
        # just look for another server
        return None, None, game_socket_registered


def _init_game_socket(server_addr):
    """Initiates the socket used for the TCP connection with the server
    """
    print(f"Received offer from {server_addr.host}, attempting to connect...")
    print(f"port {server_addr.port}")
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #game_socket.setblocking(False)
    return game_socket


def _send_team_name(selector, game_socket):
    """Sends the team name
    """
    while True:
        for (selection_key, events) in selector.select():
            if selection_key.fileobj is sys.stdin:
                # read everything so it won't be sent in the game
                sys.stdin.read()
            else:
                print("sending team name")
                game_socket.send(coder.encode_string(f"{config.TEAM_NAME}\n"))


def _wait_for_game(game_socket):
    """Waits for the game to start

    Returns the welcome message from the server.
    """
    print("waiting for game...")
    message_bytes = game_socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
    if len(message_bytes) == 0:
        # server disconnected
        return None
    return coder.decode_string(message_bytes)


if __name__ == "__main__":
    def main():
        import argparse
        from socket_address import SocketAddress

        args_parser = argparse.ArgumentParser()
        args_parser.add_argument("--host", default="127.0.0.1", required=False, dest="host")
        args_parser.add_argument("-p, --port", default=12000, required=False, type=int, dest="port")
        args = args_parser.parse_args()
        try:
            game_socket, msg = prepare_for_game(SocketAddress(args.host, args.port))
            print(msg)
        except KeyboardInterrupt:
            pass


    main()
