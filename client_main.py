"""Main client module

Client running logic,
run this if you would like to run the entire client
"""

import fcntl
import os
import selectors
import socket
import sys
import termios

import coder
import config
import util
from client_game_connection import prepare_for_game
from client_game_looker import look_for_game

selector: selectors.BaseSelector
game_socket_selector_events: int
has_stdin_been_registered: bool
input_strings_buffer = []


def main():
    """Entry function for the client
    """
    # see the code from https://docs.python.org/2/faq/library.html#how-do-i-get-a-single-keypress-at-a-time

    # Allows us to read one key at a time from stdin instead of
    # waiting for a newline (\n)
    oldterm = termios.tcgetattr(sys.stdin)
    newattr = termios.tcgetattr(sys.stdin)
    newattr[3] = newattr[3] & ~termios.ICANON
    termios.tcsetattr(sys.stdin, termios.TCSANOW, newattr)

    # Makes reading from stdin a non-blocking operation
    oldflags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    try:
        main_logic_loop()
    except KeyboardInterrupt:
        print("")
    finally:
        # Restore the old settings
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags)


def main_logic_loop():
    """Game lookup and play loop

    Looks for a game, joins in, and when the game ends,
    starts it all over again
    """
    global selector

    print("Client started, listening for offer requests...")
    selector = None
    try:
        selector = selectors.DefaultSelector()
        while True:
            set_terminal_echo(False)
            main_logic_iter()
    finally:
        if selector is not None:
            selector.close()


def main_logic_iter():
    """Game lookup and play, one time exactly

    Looks for a game, joins in, and when the game ends, return
    """

    global selector
    global game_socket_selector_events
    global has_stdin_been_registered
    global input_strings_buffer

    game_socket = None
    game_started = False
    try:
        input_strings_buffer = []
        game_socket_selector_events = None
        has_stdin_been_registered = False
        game_server_addr = look_for_game()
        try:
            game_socket, welcome_msg = prepare_for_game(game_server_addr)
            if welcome_msg is None:
                print("Server disconnected, listening for offer requests...")
                return
        except OSError:
            # error while connection/sending team name,
            # just look for another server
            print("error connecting to the server, looking for game offers...")
            return

        # clears the stdin from input so what the user
        # typed before the game won't be sent
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        set_terminal_echo(True)
        register_io_for_select(game_socket)
        print(welcome_msg)
        start_game(game_socket)
        game_started = True
    finally:
        if game_socket_selector_events is not None:
            selector.unregister(game_socket)
        if has_stdin_been_registered:
            selector.unregister(sys.stdin)
        if game_socket is not None:
            try:
                game_socket.close()
            except OSError:
                # just ignore, no idea how to handle it anyway
                # shouldn't be a problem to ignore
                pass
        if game_started:
            print("Server disconnected, listening for offer requests...")


def register_io_for_select(game_socket):
    """Register IO files for selection

    Registers the needed IO files for selection (stdin and the game socket)
    """

    global selector
    global game_socket_selector_events
    global has_stdin_been_registered

    game_socket.setblocking(False)
    selector.register(game_socket, selectors.EVENT_READ)
    game_socket_selector_events = selectors.EVENT_READ
    selector.register(sys.stdin, selectors.EVENT_READ)
    has_stdin_been_registered = True


def start_game(game_socket):
    """Plays the game

    Plays the game, and returns when the server closes the connection
    """
    global selector

    while True:
        for (selection_key, events) in selector.select():
            if selection_key.fileobj is sys.stdin:
                if (events & selectors.EVENT_READ) != 0:
                    buffer_data_from_stdin(game_socket)
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
    """Send keys to the server

    Send all the characters in the buffer saved from earlier
    to the server one character at a time (each in a different message)
    """

    global input_strings_buffer
    global game_socket_selector_events
    global selector
    # TODO: figure out whether it's ok to send whole strings
    # or we need to send individual characters only
    while len(input_strings_buffer) > 0:
        s = input_strings_buffer.pop(0)
        for c in s:
            for i in range(1):
                try:
                    game_socket.send(coder.encode_string(str(c)))
                except OSError:
                    # some error while sending the data, retry
                    util.wait_retry_sleep()
    if (game_socket_selector_events & selectors.EVENT_WRITE) != 0:
        game_socket_selector_events &= ~selectors.EVENT_WRITE
        selector.modify(game_socket, game_socket_selector_events)


def print_data_from_server(game_socket: socket.socket):
    """Prints data from the server

    Receives data from the server and prints it.
    Returns whether the server closed the game.
    """
    try:
        message_bytes = game_socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
        if len(message_bytes) == 0:
            # server closed the connection, return to look for game offers
            return True
    except OSError:
        return True
    message = coder.decode_string(message_bytes)
    print("\n" + message)
    return False


def buffer_data_from_stdin(game_socket: socket.socket):
    """Saves input from the user

    Buffers input from the user to be used later in order to send it
    to the server when the socket is ready for write
    """
    global selector
    global game_socket_selector_events
    global input_strings_buffer

    s = sys.stdin.read()
    input_strings_buffer.append(s)
    if (game_socket_selector_events & selectors.EVENT_WRITE) == 0:
        game_socket_selector_events |= selectors.EVENT_WRITE
        selector.modify(game_socket, game_socket_selector_events)


def set_terminal_echo(is_on):
    newattr = termios.tcgetattr(sys.stdin)
    c_lflags = newattr[3]
    if is_on != ((c_lflags & termios.ECHO) != 0):
        if is_on:
            c_lflags |= termios.ECHO
        else:
            c_lflags &= ~termios.ECHO
        newattr[3] = c_lflags
        termios.tcsetattr(sys.stdin, termios.TCSANOW, newattr)


if __name__ == "__main__":
    main()
