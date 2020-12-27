import socket
import threading
import selectors
import signal
import re

import config
import network
import coder
import util
from socket_address import SocketAddress
from game_client import GameClient

game_server_socket_addr = SocketAddress((network.my_addr(), config.SERVER_GAME_PORT))
game_offer_send_addr = SocketAddress((network.broadcast_addr(), config.GAME_OFFER_PORT))
invite_socket = None
game_server_socket = None
selector = None
client_invitation_thread = None
start_game_event = None

def main():
    global game_server_socket
    global selector

    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        print(f"Server started, listening on IP address {network.my_addr()}")
        main_loop()
    except KeyboardInterrupt:
        pass
    finally:
        if game_server_socket is not None:
            game_server_socket.close()
        if selector is not None:
            selector.close()

def main_loop():
    global game_server_socket
    global selector

    while True:
        try:
            has_socket_been_registered = False
            selector = selectors.DefaultSelector()
            game_server_socket = init_game_server_socket()
            selector.register(game_server_socket, selectors.EVENT_READ)
            has_socket_been_registered = True
            game_server_socket.listen()

            print('starting a new game')
            new_game()
            print('game ended')
        finally:
            if has_socket_been_registered:
                selector.unregister(game_server_socket)
            if game_server_socket is not None:
                game_server_socket.shutdown(socket.SHUT_RDWR)
                game_server_socket.close()
                game_server_socket = None
            if selector is not None:
                selector.close()
                selector = None

def init_game_server_socket():
    global game_server_socket_addr
    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind(game_server_socket_addr.to_tuple())
    game_server_socket.setblocking(False)
    game_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return game_server_socket

def new_game():
    invite_clients()
    handle_game_accepts()

def invite_clients():
    global client_invitation_thread
    global start_game_event

    start_game_event = threading.Event()
    client_invitation_thread = threading.Thread(name='invite clients', target=invite_clients_target)
    client_invitation_thread.start()

def handle_game_accepts():
    global game_server_socket
    global selector
    global start_game_event

    while not start_game_event.is_set():
        for (selection_key, events) in selector.select():
            if selection_key.fileobj is game_server_socket:
                accept_client(selection_key)
            elif (events & selectors.EVENT_READ) != 0:
                accept_client_read(selection_key)

def invite_clients_target():
    global invite_socket
    global start_game_event

    invite_socket = socket.socket(socket.AF_INET, config.GAME_OFFER_PROTOCOL)
    invite_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    e = threading.Event()
    thread = threading.Thread(name='send game offers loop', target=send_game_offers_loop, args=(e,))
    thread.start()
    thread.join(config.SERVER_OFFER_SENDING_DURATION)
    e.set()
    thread.join()
    invite_socket.close()
    invite_socket = None
    start_game_event.set()

def send_game_offers_loop(e):
    global game_offer_send_addr
    print(f"broadcasting game offer to {game_offer_send_addr}")
    while not e.is_set():
        send_game_offer()
        e.wait(config.GAME_OFFER_WAIT_TIME)

def send_game_offer():
    global invite_socket
    global game_server_socket_addr
    global game_offer_send_addr

    print(f"sending game offers")
    message_bytes = bytearray()
    message_bytes += coder.encode_int(config.MAGIC_COOKIE, config.MAGIC_COOKIE_SIZE)
    message_bytes += coder.encode_int(config.MSG_TYPE_OFFER, config.MSG_TYPE_OFFER_SIZE)
    message_bytes += coder.encode_int(game_server_socket_addr.port, config.PORT_NUM_SIZE)
    invite_socket.sendto(message_bytes, game_offer_send_addr.to_tuple())

def accept_client(selection_key):
    global game_server_socket
    global selector
    client = GameClient(game_server_socket.accept())
    client.socket.setblocking(False)
    selector.register(client.socket, selectors.EVENT_READ, client)


def accept_client_read(selection_key):
    #TODO: add to group and set team name
    client = selection_key.data
    if client.team_name is None:
        message_bytes = client.socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
        client.team_name = read_team_name(message_bytes)
        # discard any bytes after the newline

        if client.team_name is not None:
            print(f"team '{client.team_name}' connected")
    else:
        # already got data from this client
        pass

def read_team_name(message_bytes):
    if len(message_bytes) == 0:
        return None
    message_string = coder.decode_string(message_bytes)
    regex_match = re.match(r'^(\w+)\n$', message_string)
    if not regex_match:
        return None
    return regex_match.group(1)

if __name__ == "__main__":
    main()