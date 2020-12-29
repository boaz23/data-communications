import argparse
import os
import signal
import socket
import threading

from socket_address import SocketAddress


def main(accept_addr, should_close_client_socket_on_connection_close):
    print(f"dummy server started")
    server_socket = None
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 12000))
        server_socket.listen(1)

        recv_thread = None
        e_end_recv = None
        e_client_closed_conn = None
        client_socket = None
        while True:
            try:
                print("--------------------")
                print(f"listening on {accept_addr}")
                client_socket, client_addr = server_socket.accept()
                client_socket.settimeout(1)
                print(f"accepted connection from {client_addr[0]}:{client_addr[1]}\n")
                e_end_recv = threading.Event()
                e_client_closed_conn = threading.Event()
                recv_thread = threading.Thread(
                    name="recv thread",
                    target=recv_client_data,
                    args=(e_end_recv, e_client_closed_conn, client_socket)
                )
                recv_thread.start()
                send_data_from_stdin(e_client_closed_conn, client_socket)
            except KeyboardInterrupt:
                pass
            finally:
                if recv_thread is not None:
                    e_end_recv.set()
                    recv_thread.join()
                    e_end_recv = None
                    recv_thread = None

                if should_close_client_socket_on_connection_close and client_socket is not None:
                    client_socket.close()
                    client_socket = None

                if e_client_closed_conn is None:
                    break
                if e_client_closed_conn.is_set():
                    print("\nclient closed the connection")
                else:
                    break
                e_client_closed_conn = None
    except EOFError:
        pass
    except Exception as err:
        print(f"error: {err}")
    finally:
        print("\n--------------------")
        print("dummy server shutting down...")
        if server_socket is not None:
            server_socket.shutdown(socket.SHUT_RDWR)
            server_socket.close()


def send_data_from_stdin(e_client_closed_conn, client_socket):
    while not e_client_closed_conn.is_set():
        client_socket.send(input().encode())


def recv_client_data(e_end_recv, e_client_closed_conn, client_socket):
    while not e_end_recv.is_set():
        try:
            msg_bytes = client_socket.recv(2048)
            if len(msg_bytes) == 0:
                e_client_closed_conn.set()
                os.kill(os.getpid(), signal.SIGINT)
                break
            print(msg_bytes.decode())
        except socket.timeout:
            pass


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser("dummy server",
                                          description="A server which accpets a single client, prints every message "
                                                      "it receive and allows sending message from the input to the "
                                                      "client")
    args_parser.add_argument("--host", default="127.0.0.1", required=False, dest="host")
    args_parser.add_argument("-p, --port", default=12000, required=False, type=int, dest="port")
    args_parser.add_argument("-c", required=False, action='store_const', const=True, default=False, dest="c")
    args = args_parser.parse_args()
    main(SocketAddress(args.host, args.port), args.c)
