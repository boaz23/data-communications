import socket
import threading
import sys

from socket_address import SocketAddress

ACCEPT_ADDR = SocketAddress(('127.0.0.1', 12000))

def main():
    print(f"dummy server started, listening on {ACCEPT_ADDR}")
    server_socket = None
    recv_thread = None
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 12000))
        server_socket.listen()
        client_socket, client_addr = server_socket.accept()
        client_socket.settimeout(1)
        print(f"accepted connection from {client_addr[0]}:{client_addr[1]}")
        print("--------------------\n")
        e_end_recv = threading.Event()
        e_client_closed_conn = threading.Event()
        recv_thread = threading.Thread(name="recv thread", target=recv_client_data, args=(e_end_recv, e_client_closed_conn, client_socket))
        recv_thread.start()
        send_data_from_stdin(e_client_closed_conn, client_socket)
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    except Exception as err:
        print(f"error: {err}")
    finally:
        print("\n--------------------")
        print("dummy server shutting down...")
        if recv_thread is not None:
            e_end_recv.set()
            recv_thread.join()
        if len(sys.argv) > 1 and sys.argv[1] == "-c" and client_socket is not None:
            client_socket.close()
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
                print("press enter to shutdown")
                break
            print(msg_bytes.decode())
        except socket.timeout:
            pass

if __name__ == "__main__":
    main()