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

selector = None
has_socket_been_registered = False
has_stdin_been_registered = False
input_strings_buffer = []

def main():
    #see the code from https://docs.python.org/2/faq/library.html#how-do-i-get-a-single-keypress-at-a-time
    global fd_stdin

    oldterm = termios.tcgetattr(sys.stdin)
    newattr = termios.tcgetattr(sys.stdin)
    newattr[3] = newattr[3] & ~termios.ICANON
    termios.tcsetattr(fd_stdin, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

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
        first_time = True
        while True:
            main_logic_iter(first_time)
            first_time = False
    finally:
        if selector is not None:
            selector.close()

def main_logic_iter(first_time: bool):
    global selector
    global has_socket_been_registered
    global has_stdin_been_registered
    global input_strings_buffer

    game_socket = None
    try:
        input_strings_buffer = []
        has_socket_been_registered = False
        has_stdin_been_registered = False
        game_server_addr = look_for_game()
        game_socket, welcome_msg = prepare_for_game(game_server_addr)
        register_io_for_select(game_socket)
        print(welcome_msg)
        start_game(game_socket)
        print("Server disconnected, listening for offer requests...")
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

def start_game(game_socket):
    global selector

    while True:
        for (selection_key, events) in selector.select():
            if selection_key.fileobj is sys.stdin:
                if (events & selectors.EVENT_READ) != 0:
                    buffer_data_from_stdin()
                else:
                    raise Exception("improper state, events for stdin selection didn't have read")
            elif selection_key.fileobj is game_socket:
                if (events & selectors.EVENT_READ) != 0:
                    game_closed = print_data_from_server(game_socket)
                    if game_closed:
                        return
                if (events & selectors.EVENT_WRITE) != 0:
                    send_pressed_keys(game_socket)
                if (events & (selectors.EVENT_WRITE | selectors.EVENT_READ)) == 0:
                    raise Exception("improper state, events for game socket selection didn't have read nor write")
            else:
                raise Exception("impossible state, selection was not the game socket nor stdin")

def send_pressed_keys(game_socket: socket.socket):
    global input_strings_buffer
    # TODO: figure out whether it's ok to send whole strings
    # or we need to send individual characters only
    while len(input_strings_buffer) > 0:
        s = input_strings_buffer.pop(0)
        for c in s:
            game_socket.send(coder.encode_string(str(c)))

def print_data_from_server(game_socket: socket.socket):
    try:
        while True:
            message_bytes = game_socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
            if len(message_bytes) == 0:
                # server closed the connection, return to look for game offers
                return True
            message = coder.decode_string(message_bytes)
            print(message)
            if len(message_bytes) < config.DEFAULT_RECV_BUFFER_SIZE:
                break
    except BlockingIOError:
        # we tried to read data even though there was none
        pass
    return False

def buffer_data_from_stdin():
    global input_strings_buffer
    input_strings_buffer.append(sys.stdin.read(1))

if __name__ == "__main__":
    main()