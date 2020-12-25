import socket
import threading
import time

import config
import network
import coder
import util

def main():
    print(f"Server started, listening on IP address {network.my_addr()}")
    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind((network.my_addr(), config.SERVER_GAME_PORT))
    game_port = game_server_socket.getsockname()[1]

    while True:
        game_server_socket.listen()
        start_game_event = invite_clients(game_port)

    game_server_socket.close()


def invite_clients(game_port):
    start_game_event = threading.Event()
    thread = threading.Thread(name='invite clients', target=invite_clients_target, args=(game_port, start_game_event))
    thread.start()
    return start_game_event

def invite_clients_target(game_port, start_game_event):
    invite_socket = socket.socket(socket.AF_INET, config.GAME_OFFER_PROTOCOL)
    invite_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    e = threading.Event()
    thread = threading.Thread(name='send game offers loop', target=send_game_offers_loop, arg=(invite_socket, game_port, e))
    thread.start()
    thread.join(config.SERVER_OFFER_SENDING_DURATION)
    e.set()
    thread.join()
    invite_socket.close()
    start_game_event.set()

def send_game_offers_loop(invite_socket, game_port, e):
    print(f"broadcasting game offer to {network.broadcast_addr()}:{config.GAME_OFFER_PORT}")
    while not e.isSet():
        send_game_offer(invite_socket, game_port)
        time.sleep(config.GAME_OFFER_WAIT_TIME)

def send_game_offer(invite_socket, game_port):
    message_bytes = bytearray()
    message_bytes += coder.encode_int(config.MAGIC_COOKIE, config.MAGIC_COOKIE_SIZE)
    message_bytes += coder.encode_int(config.MSG_TYPE_OFFER, config.MSG_TYPE_OFFER_SIZE)
    message_bytes += coder.encode_int(game_port, config.PORT_NUM_SIZE)
    invite_socket.sendto(message_bytes, (network.broadcast_addr(), config.GAME_OFFER_PORT))

if __name__ == "__main__":
    main()