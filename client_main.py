import socket
import time
import selectors
import termios, fcntl, sys, os

import config
import network
import coder
import util
from socket_address import SocketAddress

from client_game_looker import look_for_game

game_offer_recv_addr = SocketAddress((network.my_addr(), config.GAME_OFFER_PORT))
fd_stdin = sys.stdin.fileno()
game_socket = None
selector = None

def main():
    #see the code from https://docs.python.org/2/faq/library.html#how-do-i-get-a-single-keypress-at-a-time
    global fd_stdin

    oldterm = termios.tcgetattr(fd_stdin)
    newattr = termios.tcgetattr(fd_stdin)
    newattr[3] = newattr[3] & ~termios.ICANON
    termios.tcsetattr(fd_stdin, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd_stdin, fcntl.F_GETFL)
    fcntl.fcntl(fd_stdin, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    try:
        main_logic_loop()
    finally:
        termios.tcsetattr(fd_stdin, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd_stdin, fcntl.F_SETFL, oldflags)

def main_logic_loop():
    global selector

    print("Client started, listening for offer requests...")
    selector = None
    try:
        selector = selectors.DefaultSelector()
        while True:
            main_logic_iter()
    finally:
        if selector is not None:
            selector.close()

def main_logic_iter():
    global game_socket
    global selector

    try:
        has_socket_been_registered = False
        game_offer_addr = look_for_game()
        establish_game_connection(game_offer_addr)
        send_team_name()

        game_socket.setblocking(False)
        has_socket_been_registered = True
    finally:
        if has_socket_been_registered:
            selector.unregister(game_socket)
        if game_socket is not None:
            game_socket.close()

def establish_game_connection(game_offer_addr):
    global game_socket
    global selector

    print(f"Received offer from {game_offer_addr.host}, attempting to connect...")
    print(f"got offer from {game_offer_addr}")
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_socket.connect(game_offer_addr.to_tuple())

def send_team_name():
    game_socket.send(coder.encode_string(f"{config.TEAM_NAME}\n"))

if __name__ == "__main__":
    main()