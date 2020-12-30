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
from terminal_colors import *

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
num_clients: int
pressed_keys_count = {}
most_pressed_key = None
best_basher = None


def main():
    global game_server_socket
    global selector

    signal.signal(signal.SIGINT, signal.default_int_handler)
    selector = selectors.DefaultSelector()
    init_game_server_socket()
    game_server_socket.listen()

    try:
        print_color(TC_FG_BRIGHT_GREEN, f"Server started, listening on IP address {network.my_addr()}")
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

            print_color(TC_FG_BRIGHT_GREEN, "preparing for new game")
            new_game()
            game_started = True
        finally:
            disconnect_all_clients()
            if game_started:
                print_color(TC_FG_BRIGHT_MAGENTA, 'Game over, sending out offer requests...')


def disconnect_all_clients():
    global groups
    for group in groups:
        for client in group.connected_clients.values():
            if client.is_connected:
                disconnect_client(client)


def init_game_server_socket():
    global game_server_socket_addr
    global game_server_socket

    game_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_server_socket.bind(game_server_socket_addr.to_tuple())
    game_server_socket_addr = SocketAddress(game_server_socket.getsockname())
    game_server_socket.setblocking(False)
    game_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


def new_game():
    init_game_vars()
    invite_clients()
    handle_game_accepts()
    print_color(TC_FG_BRIGHT_CYAN, 'starting a new game')
    start_game()


def init_game_vars():
    global groups
    global num_clients
    global pressed_keys_count
    global most_pressed_key
    global best_basher
    num_clients = 0
    pressed_keys_count = {}
    most_pressed_key = ('', 0)
    groups = []
    best_basher = (None, 0)
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
    while is_in_game():
        for (selection_key, events) in selector.select(config.SERVER_IN_GAME_SELECT_TIMEOUT):
            if e.is_set():
                break
            client = selection_key.data
            if (events & selectors.EVENT_READ) != 0:
                game_started_read_client_data(client)
            if (events & selectors.EVENT_WRITE) != 0:
                game_started_send_data_to_client(client, welcome_message)


def is_in_game():
    global in_game_select_event
    return in_game_select_event is not None and not in_game_select_event.is_set()


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
        if not send_welcome_message(client, welcome_message):
            return
        client.sent_welcome_message = True
        register_client_to_selector(client, selectors.EVENT_READ)


def print_winner():
    global groups
    winner_groups = find_winner_groups(groups)
    game_over_message = make_game_over_message(winner_groups)
    register_clients_to_selector_write()
    print_color(TC_FG_MAGENTA, game_over_message)
    send_game_over_message_to_clients(game_over_message)


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
    s = ""
    s += "Game over!\n"
    s += make_final_groups_score_message(winner_groups)
    s += make_statistics_message()
    return s


def make_final_groups_score_message(winner_groups):
    global groups
    s = ""
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


def make_statistics_message():
    global groups
    global most_pressed_key
    global best_basher

    s = "\n"
    s += "Statistics\n"
    s += "==\n"
    times_pressed = most_pressed_key[1]
    if sum(len(group.connected_clients) for group in groups) == 0:
        s += "No team participated"
    elif times_pressed == 0:
        s += "No one typed anything, congrats, you trolls..."
    else:
        best_basher_client = best_basher[0]
        s += f"The MVP for this game is '{best_basher_client.team_name}'\n"
        s += f"They typed {best_basher_client.keys_pressed_amount} characters\n"

        s += "\n"
        s += f"Most typed character: '{util.char_to_string(most_pressed_key[0])}'\n"
        if times_pressed < 10:
            s += f"It was typed only {times_pressed} times\n"
            s += "Wow, you guys are weak"
        elif times_pressed < 30:
            s += f"It was typed {times_pressed} times"
        else:
            s += f"It was typed {times_pressed} times!"
    s += "\n"
    return s


def send_welcome_message(client, welcome_message):
    try:
        client.socket.send(coder.encode_string(welcome_message))
        return True
    except OSError:
        return False


def register_clients_to_selector_write():
    global groups
    for group in groups:
        for client in group.connected_clients.values():
            register_client_to_selector(client, selectors.EVENT_WRITE)


def send_game_over_message_to_clients(game_over_message):
    global groups
    global num_clients
    send_remaining = num_clients
    while send_remaining > 0:
        for (selection_key, events) in selector.select():
            client = selection_key.data
            try:
                client.socket.send(coder.encode_string(game_over_message))
            except OSError:
                # ignore
                pass
            send_remaining -= 1


def in_game_client_read(client, message_bytes):
    global pressed_keys_count
    global most_pressed_key
    global best_basher
    message = coder.decode_string(message_bytes)
    message_len = len(message)
    for c in message:
        if c in pressed_keys_count:
            count = pressed_keys_count[c] + 1
        else:
            count = 1
        pressed_keys_count[c] = count
        if most_pressed_key[1] < count:
            most_pressed_key = (c, count)

    client.keys_pressed_amount += message_len
    client.group.pressed_keys_counter += message_len
    if best_basher[1] < client.keys_pressed_amount:
        best_basher = (client, client.keys_pressed_amount)


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
    print_color(TC_FG_BRIGHT_BLUE, f"broadcasting game offer to {game_offer_send_addr}")
    while not e.is_set():
        send_game_offer()
        e.wait(config.GAME_OFFER_WAIT_TIME)


def send_game_offer():
    print_color(TC_FG_BRIGHT_BLUE, f"sending game offers")
    for byte_order in config.INTEGER_BYTE_ORDERS:
        for msg_type_size in config.MSG_TYPE_OFFER_SIZES:
            send_game_offer_core(byte_order, msg_type_size)


def send_game_offer_core(byte_order, msg_type_size):
    global invite_socket
    global game_server_socket_addr
    global game_offer_send_addr

    message_bytes = bytearray()
    message_bytes += coder.encode_int(config.MAGIC_COOKIE, config.MAGIC_COOKIE_SIZE, byte_order)
    message_bytes += coder.encode_int(config.MSG_TYPE_OFFER, msg_type_size, byte_order)
    message_bytes += coder.encode_int(game_server_socket_addr.port, config.PORT_NUM_SIZE, byte_order)
    try:
        invite_socket.sendto(message_bytes, game_offer_send_addr.to_tuple())
    except OSError:
        # just ignore send errors of offer requests
        pass


def accept_client(selection_key):
    global game_server_socket
    global selector
    global num_clients
    try:
        client_socket = game_server_socket.accept()
    except OSError:
        # error accepting the client, just drop him
        return
    client = GameClient(client_socket)
    client.socket.setblocking(False)
    register_client_to_selector(client, selectors.EVENT_READ)
    num_clients += 1


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
            print_color(TC_FG_BRIGHT_YELLOW, f"team '{team_name}' connected")
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
    if not is_in_game() and client.group is not None:
        del client.group.connected_clients[client.addr]
    if client.team_name is not None:
        print_color(TC_FG_BRIGHT_YELLOW, f"team '{client.team_name}' disconnected")


def disconnect_client(client):
    global num_clients
    if not client.is_connected:
        return
    if client.is_registered_in_selector():
        unregister_client_from_selector(client)
    try:
        client.socket.close()
        client.is_connected = False
        num_clients -= 1
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
