"""Inital game connection setup and exchanges logic

Contains logic to establish a TCP game connection with the server,
exchange pre-game preparation data (team name) and wait for the game
to start
"""

import socket

import config
import coder

def prepare_for_game(server_addr):
    game_socket = _establish_game_connection(server_addr)
    _send_team_name(game_socket)
    return game_socket, _wait_for_game(game_socket)

def _establish_game_connection(server_addr):
    print(f"Received offer from {server_addr.host}, attempting to connect...")
    print(f"got offer from {server_addr}")
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_socket.connect(server_addr.to_tuple())
    return game_socket

def _send_team_name(game_socket):
    game_socket.send(coder.encode_string(f"{config.TEAM_NAME}\n"))

def _wait_for_game(game_socket):
    message_bytes = game_socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
    return coder.decode_string(message_bytes)

if __name__ == "__main__":
    import sys
    import argparse
    from socket_address import SocketAddress

    def do_nothing():
        pass

    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--host", default="127.0.0.1", required=False, dest="host")
    args_parser.add_argument("-p, --port", default=12000, required=False, type=int, dest="port")
    args = args_parser.parse_args()
    try:
        game_socket, msg = prepare_for_game(SocketAddress(args.host, args.port), do_nothing)
        print(msg)
    except KeyboardInterrupt:
        pass