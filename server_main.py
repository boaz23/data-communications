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
from group import Group

game_server_socket_addr = SocketAddress(network.my_addr(), config.SERVER_GAME_PORT)
game_offer_send_addr = SocketAddress(network.broadcast_addr(), config.GAME_OFFER_PORT)
invite_socket = None
game_server_socket: socket.socket = None
selector: selectors.BaseSelector = None
client_invitation_thread = None
start_game_event = None
groups = []
next_group_index = 0

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
        game_started = False
        try:
            has_socket_been_registered = False
            selector = selectors.DefaultSelector()
            game_server_socket = init_game_server_socket()
            selector.register(game_server_socket, selectors.EVENT_READ)
            has_socket_been_registered = True
            game_server_socket.listen()

            print("preparing for new game")
            new_game()
            game_started = True
        finally:
            if has_socket_been_registered:
                selector.unregister(game_server_socket)
            disconnect_all_clients()
            if game_server_socket is not None:
                game_server_socket.shutdown(socket.SHUT_RDWR)
                game_server_socket.close()
                game_server_socket = None
            if selector is not None:
                selector.close()
                selector = None
            if game_started:
                print('Game over, sending out offer requests...')

def disconnect_all_clients():
    global groups
    for group in groups:
        for client in group.connected_clients.values():
            disconnect_client(client)

def init_game_server_socket():
    global game_server_socket_addr
    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind(game_server_socket_addr.to_tuple())
    game_server_socket_addr = SocketAddress(game_server_socket.getsockname())
    print(game_server_socket_addr)
    game_server_socket.setblocking(False)
    game_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return game_server_socket

def new_game():
    init_game_vars()
    invite_clients()
    handle_game_accepts()
    print('starting a new game')
    start_game()

def init_game_vars():
    global groups
    global next_group_index
    next_group_index = 0
    groups = []
    for i in range(config.MAX_GROUPS_COUNT):
        groups.append(Group(i + 1))

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
                game_intermission_client_read(selection_key)

def start_game():
    global game_server_socket
    global selector
    selector.unregister(game_server_socket)
    prep_clients_to_selector_pre_game()
    welcome_message = make_welcome_message()
    util.run_and_wait_for_timed_task(game_started_do_select, config.GAME_DURAION, args=(welcome_message,), name='in-game select')
    print_winner()

def prep_clients_to_selector_pre_game():
    global selector
    global groups

    for group in groups:
        for client in group.connected_clients.values():
            if client.team_name is None:
                # TODO: make sure we actually remove those with no team name so far
                remove_client()
            else:
                selector.modify(client.socket, selectors.EVENT_READ | selectors.EVENT_WRITE)

def make_welcome_message():
    global groups
    welcome_message = ""
    welcome_message += "Welcome to Keyboard Spamming Battle Royale.\n"
    welcome_message += "".join(map(make_welcome_message_group, groups))
    welcome_message += "Start pressing keys on your keyboard as fast as you can!!"
    return welcome_message

def make_welcome_message_group(group: Group):
    s = ""
    s += f"Group {group.num}:\n"
    s += get_group_team_names_formatted_string(group)
    s += "\n"
    return s

def get_group_team_names_formatted_string(group):
    s = ""
    s += "==\n"
    for client in group.connected_clients.values():
        s += f"{client.team_name}\n"
    return s

def game_started_do_select(e, welcome_message):
    global selector
    while not e.is_set():
        for (selection_key, events) in selector.select():
            if e.is_set():
                break
            client = selection_key.data
            if (events & selectors.EVENT_WRITE) != 0:
                if client.sent_welcome_message == False:
                    send_welcome_message(client, welcome_message)
                    client.sent_welcome_message = True
                    selector.modify(client, selectors.EVENT_READ)
            if (events & selectors.EVENT_READ) != 0:
                in_game_client_read(client)

def print_winner():
    global groups

    winner_group = max(groups, key=lambda group : group.pressed_keys_counter)
    print(make_game_over_message(winner_group))

def make_game_over_message(winner_group):
    global groups

    s = ""
    s += "Game over!\n"
    s += " ".join(map(lambda group : f"Group {group.num} typed in {group.pressed_keys_counter} characters.", groups))
    s += f"\nGroup {winner_group.num} wins!\n\n"
    s += "Congratulations to the winners:\n"
    s += get_group_team_names_formatted_string(winner_group)
    return s

def send_welcome_message(client, welcome_message):
    client.socket.send(coder.encode_string(welcome_message))

def in_game_client_read(client):
    while True:
        try:
            message_bytes = client.socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
            if len(message_bytes) == 0:
                return
            message = coder.decode_string(message_bytes)
            client.group.pressed_keys_counter += len(message)
        except BlockingIOError:
            return

def invite_clients_target():
    global invite_socket
    global start_game_event

    invite_socket = socket.socket(socket.AF_INET, config.GAME_OFFER_PROTOCOL)
    invite_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    util.run_and_wait_for_timed_task(send_game_offers_loop, config.SERVER_OFFER_SENDING_DURATION, name='send game offers loop')
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

def game_intermission_client_read(selection_key):
    #TODO: add to group and set team name
    #TODO: figure out whether if the first client is not in the correct
    # format, should we keep looking for his team name or just ignore
    # the client completely
    client = selection_key.data
    should_remove_client = game_intermissions_admit_to_game_lobby(client)
    if should_remove_client:
        remove_client(client)

def remove_client(client):
    global selector

    disconnect_client(client)
    if client.group is not None:
        del client.group.connected_clients[client.addr]

def disconnect_client(client):
    selector.unregister(client.socket)
    client.socket.close()

def game_intermissions_admit_to_game_lobby(client: GameClient):
    if client.team_name is None:
        team_name, should_remove_client = game_intermission_read_team_name_core(client)
        if should_remove_client:
            return True
        else:
            client.team_name = team_name
            if client.team_name is not None:
                print(f"team '{client.team_name}' connected")
                assign_client_to_group(client)
                client.group.connected_clients[client.addr] = client
        return False

    # read everything left from the client so that it won't be read
    # when the game starts, it should be carried over.
    # also, check to see if the client closed the connection
    return ignore_client_data(client.socket)

def assign_client_to_group(client):
    global next_group_index
    global groups

    client.group = groups[next_group_index]
    next_group_index = (next_group_index + 1) % len(groups)

def game_intermission_read_team_name_core(client):
    team_name = None
    while team_name is None:
        try:
            message_bytes = client.socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
            if len(message_bytes) == 0:
                return None, True
            team_name = read_team_name_from_bytes(message_bytes)
        except BlockingIOError:
            return None, False
    return team_name, False

def read_team_name_from_bytes(message_bytes):
    message_string = coder.decode_string(message_bytes)
    regex_match = re.match(r'^(\w+)\n$', message_string)
    if not regex_match:
        return None
    return regex_match.group(1)

def ignore_client_data(client_socket):
    try:
        while True:
            message_bytes = client_socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
            if len(message_bytes) == 0:
                # peer closed the connection
                return True
            if len(message_bytes) < config.DEFAULT_RECV_BUFFER_SIZE:
                # we read everything, nothing is left to read
                break
    except BlockingIOError:
        # we tried to read data even though there was none
        pass
    return False

if __name__ == "__main__":
    main()