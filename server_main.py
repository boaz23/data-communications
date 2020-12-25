import socket
import threading
import selectors
import signal

import config
import network
import coder
import util

invite_socket = None
game_server_socket = None
game_port = -1
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
        print(f"Server started, listening on IP address {network.my_addr()}")
        selector = selectors.DefaultSelector()
        game_server_socket, game_port = init_game_server_socket()
        selector.register(game_server_socket, selectors.EVENT_READ)

        while True:
            game_server_socket.listen()
            client_invitation_thread, start_game_event = invite_clients()
            handle_game_accepts()

    except KeyboardInterrupt:
        pass
    finally:
        if game_server_socket is not None:
            game_server_socket.close()
        if selector is not None:
            selector.close()

def init_game_server_socket():
    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind((network.my_addr(), config.SERVER_GAME_PORT))
    game_server_socket.setblocking(False)
    game_port = game_server_socket.getsockname()[1]
    return game_server_socket, game_port

def invite_clients():
    start_game_event = threading.Event()
    thread = threading.Thread(name='invite clients', target=invite_clients_target, args=(start_game_event))
    thread.start()
    return thread, start_game_event

def handle_game_accepts():
    global selector
    pass

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
    print(f"broadcasting game offer to {network.broadcast_addr()}:{config.GAME_OFFER_PORT}")
    while not e.isSet():
        send_game_offer()
        e.wait(config.GAME_OFFER_WAIT_TIME)

def send_game_offer():
    global invite_socket

    print(f"sending game offers")
    message_bytes = bytearray()
    message_bytes += coder.encode_int(config.MAGIC_COOKIE, config.MAGIC_COOKIE_SIZE)
    message_bytes += coder.encode_int(config.MSG_TYPE_OFFER, config.MSG_TYPE_OFFER_SIZE)
    message_bytes += coder.encode_int(game_port, config.PORT_NUM_SIZE)
    invite_socket.sendto(message_bytes, (network.broadcast_addr(), config.GAME_OFFER_PORT))

if __name__ == "__main__":
    main()