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

game_server_socket: socket.socket
selector: selectors.BaseSelector

invite_socket: socket.socket
client_invitation_thread: threading.Thread
start_game_event: threading.Event
send_game_offer_event: threading.Event
in_game_select_event = threading.Event

groups = []


def main():
    global game_server_socket
    global selector

    signal.signal(signal.SIGINT, signal.default_int_handler)
    selector = selectors.DefaultSelector()
    init_game_server_socket()
    game_server_socket.listen()

    # TODO: remove this line
    # config.SERVER_OFFER_SENDING_DURATION = 5

    try:
        print(f"Server started, listening on IP address {network.my_addr()}")
        main_loop()
    except KeyboardInterrupt:
        print("")
    finally:
        if send_game_offer_event is not None and client_invitation_thread is not None:
            send_game_offer_event.set()
            client_invitation_thread.join()
        if in_game_select_event is not None:
            in_game_select_event.set()
        if game_server_socket is not None:
            game_server_socket.shutdown(socket.SHUT_RDWR)
            game_server_socket.close()
        if selector is not None:
            selector.close()


def main_loop():
    global game_server_socket
    global selector

    global invite_socket
    global client_invitation_thread
    global start_game_event
    global send_game_offer_event
    global in_game_select_event

    while True:
        invite_socket = None
        client_invitation_thread = None
        start_game_event = None
        send_game_offer_event = None
        in_game_select_event = None

        game_started = False
        try:
            selector.register(game_server_socket, selectors.EVENT_READ)

            print("preparing for new game")
            new_game()
            game_started = True
        finally:
            disconnect_all_clients()
            if game_started:
                print('Game over, sending out offer requests...')


def disconnect_all_clients():
    global groups
    for group in groups:
        for client in group.connected_clients.values():
            disconnect_client(client)


def init_game_server_socket():
    global game_server_socket_addr
    global game_server_socket

    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind(game_server_socket_addr.to_tuple())
    game_server_socket_addr = SocketAddress(game_server_socket.getsockname())
    print(game_server_socket_addr)
    game_server_socket.setblocking(False)
    game_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


def new_game():
    init_game_vars()
    invite_clients()
    handle_game_accepts()
    print('starting a new game')
    start_game()


def init_game_vars():
    global groups
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
        for (selection_key, events) in selector.select(config.SERVER_GAME_ACCEPT_SELECT_TIMEOUT):
            if start_game_event.is_set():
                break
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
    util.run_and_wait_for_timed_task(game_do_select, config.GAME_DURATION, args=(welcome_message,),
                                     name='in-game select')
    print_winner()


def prep_clients_to_selector_pre_game():
    global groups

    for group in groups:
        # shallow copy the values because we might some of them
        # and it will be updated in the values while we are iterating it
        # an opening for trouble
        clients = [x for x in group.connected_clients.values()]
        for client in clients:
            if client.team_name is None:
                # TODO: make sure we actually remove those with no team name so far
                remove_client(client)
            else:
                register_client_to_selector(client, selectors.EVENT_READ | selectors.EVENT_WRITE)


def make_welcome_message():
    global groups
    welcome_message = ""
    welcome_message += "Welcome to Keyboard Spamming Battle Royale.\n"
    welcome_message += get_groups_team_names_with_title_formatted_string(groups)
    welcome_message += "Start pressing keys on your keyboard as fast as you can!!"
    return welcome_message


def get_groups_team_names_with_title_formatted_string(groups):
    return "".join(map(get_group_team_names_with_title_formatted_string, groups))


def get_group_team_names_with_title_formatted_string(group: Group):
    s = ""
    s += f"{group}:\n"
    s += get_group_team_names_formatted_string(group)
    s += "\n"
    return s


def get_group_team_names_formatted_string(group):
    s = ""
    s += "==\n"
    for client in group.connected_clients.values():
        s += f"{client.team_name}\n"
    return s


def game_do_select(e, welcome_message):
    global selector
    global in_game_select_event

    in_game_select_event = e
    while not e.is_set():
        for (selection_key, events) in selector.select(config.SERVER_IN_GAME_SELECT_TIMEOUT):
            if e.is_set():
                break
            client = selection_key.data
            if (events & selectors.EVENT_READ) != 0:
                game_started_read_client_data(client)
            if (events & selectors.EVENT_WRITE) != 0:
                game_started_send_data_to_client(client, welcome_message)


def game_started_read_client_data(client):
    try:
        message_bytes = client.socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
    except OSError:
        return
    # check if the client disconnected
    if len(message_bytes) == 0:
        remove_client(client)
    elif client.sent_welcome_message:
        in_game_client_read(client, message_bytes)
    else:
        # eat up characters from the client before the game begins since
        # the client can't already be sending characters before he even
        # got the welcome message...
        pass


def game_started_send_data_to_client(client, welcome_message):
    if not client.sent_welcome_message:
        try:
            send_welcome_message(client, welcome_message)
        except OSError:
            return
        client.sent_welcome_message = True
        register_client_to_selector(client, selectors.EVENT_READ)


def print_winner():
    global groups
    winner_groups = find_winner_groups(groups)
    print(make_game_over_message(winner_groups))


def find_winner_groups(groups):
    winner_groups = []
    max_score = -1
    for group in groups:
        score = group.pressed_keys_counter
        if max_score < score:
            winner_groups = [group]
            max_score = score
        elif max_score == score:
            winner_groups.append(group)
    return winner_groups


def make_game_over_message(winner_groups):
    global groups

    s = ""
    s += "Game over!\n"
    s += " ".join(map(lambda group: f"{group} typed in {group.pressed_keys_counter} characters.", groups))
    if len(winner_groups) == 1:
        # no ties
        winner_group = winner_groups[0]
        s += f"\n{winner_group} wins!\n\n"
        s += "Congratulations to the winners:\n"
        s += get_group_team_names_formatted_string(winner_group)
    else:
        s += "\nTie between "
        s += ", ".join(map(lambda group: f"{group}", winner_groups[:-1]))
        s += f" and {winner_groups[-1]}\n\n"
        s += "Tied groups:\n\n"
        s += get_groups_team_names_with_title_formatted_string(winner_groups)
    return s


def send_welcome_message(client, welcome_message):
    client.socket.send(coder.encode_string(welcome_message))


def in_game_client_read(client, message_bytes):
    message = coder.decode_string(message_bytes)
    client.group.pressed_keys_counter += len(message)


def invite_clients_target():
    global invite_socket
    global start_game_event

    invite_socket = socket.socket(socket.AF_INET, config.GAME_OFFER_PROTOCOL)
    invite_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    util.run_and_wait_for_timed_task(send_game_offers_loop, config.GAME_OFFER_SENDING_DURATION,
                                     name='send game offers loop')
    invite_socket.close()
    invite_socket = None
    start_game_event.set()


def send_game_offers_loop(e):
    global game_offer_send_addr
    global send_game_offer_event

    send_game_offer_event = e
    print(f"broadcasting game offer to {game_offer_send_addr}")
    while not e.is_set():
        try:
            send_game_offer()
        except OSError:
            # just ignore send errors of offer requests
            pass
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
    try:
        client_socket = game_server_socket.accept()
    except OSError:
        # error accepting the client, just drop him
        return
    client = GameClient(client_socket)
    client.socket.setblocking(False)
    register_client_to_selector(client, selectors.EVENT_READ)


def game_intermission_client_read(selection_key):
    # TODO: figure out whether if the first client is not in the correct
    # format, should we keep looking for his team name or just ignore
    # the client completely
    client = selection_key.data
    should_remove_client = game_intermissions_admit_to_game_lobby(client)
    if should_remove_client:
        remove_client(client)


def game_intermissions_admit_to_game_lobby(client: GameClient):
    global selector
    # We don't want further data from the client to be
    # carried over to the game, so just read it regardless
    # if we got his team name
    try:
        message_bytes = client.socket.recv(config.DEFAULT_RECV_BUFFER_SIZE)
    except OSError:
        return
    if len(message_bytes) == 0:
        return True
    if client.team_name is None:
        team_name = read_team_name_from_bytes(message_bytes)
        client.team_name = team_name
        if team_name is not None:
            print(f"team '{team_name}' connected")
            assign_client_to_group(client)

    return False


def register_client_to_selector(client, events):
    global selector
    if client.is_registered_in_selector():
        client.modify_in_selector(selector, events)
    else:
        client.register_to_selector(selector, events)


def unregister_client_from_selector(client):
    global selector
    client.unregister_from_selector(selector)


def remove_client(client):
    disconnect_client(client)
    if client.group is not None:
        del client.group.connected_clients[client.addr]


def disconnect_client(client):
    if client.is_registered_in_selector():
        unregister_client_from_selector(client)
    try:
        client.socket.close()
    except OSError:
        # what go wrong anyway? KEKW
        # ignore
        pass


def assign_client_to_group(client):
    global groups

    min_group = min(groups, key=lambda group: len(group.connected_clients))
    client.group = min_group
    min_group.connected_clients[client.addr] = client


def read_team_name_from_bytes(message_bytes):
    message_string = coder.decode_string(message_bytes)
    regex_match = re.match(r'^(\w+)\n$', message_string)
    if not regex_match:
        return None
    return regex_match.group(1)


if __name__ == "__main__":
    main()
