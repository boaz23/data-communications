import socket
import threading
import selectors
import signal

import config
import network
import coder
import util
from socket_address import SocketAddress
from game_client import GameClient

game_port = -1
game_offer_send_addr = None
invite_socket = None
game_server_socket = None
selector = None
client_invitation_thread = None
start_game_event = None

def main():
    global game_server_socket
    global game_port
    global selector
    global client_invitation_thread
    global start_game_event

    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        game_offer_send_addr = SocketAddress((network.broadcast_addr(), config.GAME_OFFER_PORT))
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
    global game_port
    global selector
    global client_invitation_thread
    global start_game_event

    while True:
        selector = selectors.DefaultSelector()
        game_server_socket, game_port = init_game_server_socket()
        selector.register(game_server_socket, selectors.EVENT_READ)
        game_server_socket.listen()

        new_game()

        selector.unregister(game_server_socket)
        game_server_socket.close()
        selector.close()
        game_server_socket = None
        selector = None

def init_game_server_socket():
    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind((network.my_addr(), config.SERVER_GAME_PORT))
    game_server_socket.setblocking(False)
    #game_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    game_port = game_server_socket.getsockname()[1]
    return game_server_socket, game_port

def new_game():
    client_invitation_thread, start_game_event = invite_clients()
    handle_game_accepts()

def invite_clients():
    start_game_event = threading.Event()
    thread = threading.Thread(name='invite clients', target=invite_clients_target, args=(start_game_event))
    thread.start()
    return thread, start_game_event

def handle_game_accepts():
    global game_server_socket
    global selector
    global start_game_event

    while not start_game_event.is_set():
        for (selection_key, events) in selector.select():
            if selection_key.fileobj is game_server_socket:
                accept_client(selection_key)
            elif events & selectors.EVENT_READ != 0:
                accept_client_read(selection_key)

def invite_clients_target(start_game_event):
    global invite_socket

    invite_socket = socket.socket(socket.AF_INET, config.GAME_OFFER_PROTOCOL)
    invite_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    e = threading.Event()
    thread = threading.Thread(name='send game offers loop', target=send_game_offers_loop, args=(e))
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

    print(f"sending game offers")
    message_bytes = bytearray()
    message_bytes += coder.encode_int(config.MAGIC_COOKIE, config.MAGIC_COOKIE_SIZE)
    message_bytes += coder.encode_int(config.MSG_TYPE_OFFER, config.MSG_TYPE_OFFER_SIZE)
    message_bytes += coder.encode_int(game_port, config.PORT_NUM_SIZE)
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
    if client.team_name is None and client.is_invalid == False:
        message_bytes = client.socket.recv(config.SERVER_RECV_BUFFER_SIZE)
        client.team_name = read_team_name(message_bytes)
        client.is_invalid = client.team_name is None
        # discard any bytes after the newline
    else:
        # already got data from this client
        pass

def read_team_name(message_bytes):
    name_bytes = bytearray()
    for byte in message_bytes:
        c = chr(byte)
        if c.isalpha():
            name_bytes += byte
        elif c == '\n':
            return coder.decode_string(name_bytes)
        else:
            return None

if __name__ == "__main__":
    main()