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
from client_game_connection import prepare_for_game

fd_stdin = sys.stdin.fileno()
selector = None
has_socket_been_registered = False
has_stdin_been_registered = False

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
    except KeyboardInterrupt:
        pass
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
    global selector
    global has_socket_been_registered
    global has_stdin_been_registered

    game_socket = None
    try:
        has_socket_been_registered = False
        has_stdin_been_registered = False
        game_server_addr = look_for_game()
        game_socket, welcome_msg = prepare_for_game(game_server_addr)
        register_io_for_select(game_socket)
        print(welcome_msg)
    finally:
        if has_socket_been_registered:
            selector.unregister(game_socket)
        if has_stdin_been_registered:
            selector.unregister(sys.stdin)
        if game_socket is not None:
            game_socket.close()

def register_io_for_select(game_socket):
    global selector
    global has_socket_been_registered

    game_socket.setblocking(False)
    selector.register(game_socket, selectors.EVENT_READ | selectors.EVENT_WRITE)
    has_socket_been_registered = True
    selector.register(sys.stdin, selectors.EVENT_READ)
    has_stdin_been_registered = True

if __name__ == "__main__":
    main()