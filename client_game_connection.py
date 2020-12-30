"""Inital game connection setup and exchanges logic

Contains logic to establish a TCP game connection with the server,
exchange pre-game preparation data (team name) and wait for the game
to start
"""

import socket

import coder
import config
from socket_address import SocketAddress
from terminal_colors import *


def prepare_for_game(server_addr: SocketAddress):
    """Creates a game connection with the server

    Creates a TCP connection with the server,
    sends the team name and waits for the game to begin.
    Returns the welcome message from the server.
    """
    game_socket = _establish_game_connection(server_addr)
    _send_team_name(game_socket)
    return game_socket, _wait_for_game(game_socket)


def _establish_game_connection(server_addr):
    """Creates a TCP connection with the server
    """
    print(f"{TC_FG_BRIGHT_BLUE}Received offer from {server_addr.host}, attempting to connect...")
    print(f"port {server_addr.port}{TC_FG_ENDC}")
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_socket.connect(server_addr.to_tuple())
    return game_socket


def _send_team_name(game_socket):
    """Sends the team name
    """
    print(f"{TC_FG_BRIGHT_BLUE}sending team name{TC_FG_ENDC}")
    game_socket.send(coder.encode_string(f"{config.TEAM_NAME}\n"))


def _wait_for_game(game_socket):
    """Waits for the game to start

    Returns the welcome message from the server.
    """
    print(f"{TC_FG_BRIGHT_BLUE}waiting for game...{TC_FG_ENDC}")
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
