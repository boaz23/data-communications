"""Inital game connection setup and exchanges logic

Contains logic to establish a TCP game connection with the server,
exchange pre-game preparation data (team name) and wait for the game
to start
"""

import socket

import config
import coder

game_socket = None

def prepare_for_game(server_addr, before_wait_callback):
    _establish_game_connection(server_addr)
    _send_team_name()
    before_wait_callback()
    return _wait_for_game()

def _establish_game_connection(server_addr):
    global game_socket
    print(f"Received offer from {server_addr.host}, attempting to connect...")
    print(f"got offer from {server_addr}")
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_socket.connect(server_addr.to_tuple())

def _send_team_name():
    global game_socket
    game_socket.send(coder.encode_string(f"{config.TEAM_NAME}\n"))

def _wait_for_game():
    global game_socket
    message_bytes = game_socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
    return coder.decode_string(message_bytes)

if __name__ == "__main__":
    import sys
    from socket_address import SocketAddress

    def do_nothing():
        pass

    try:
        msg = prepare_for_game(SocketAddress((sys.argv[1], int(sys.argv[2]))), do_nothing)
        print(msg)
    except KeyboardInterrupt:
        pass