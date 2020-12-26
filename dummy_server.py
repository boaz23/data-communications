import socket

def main():
    print("dummy server on")
    server_socket = None
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('127.0.0.1', 12000))
        server_socket.listen()
        client_socket, client_addr = server_socket.accept()
        print(f"accepted connection from {client_addr[0]}:{client_addr[1]}")
        print("--------------------\n")
        while True:
            print(client_socket.recv(2048).decode())
    except KeyboardInterrupt:
        pass
    finally:
        print("\n--------------------")
        print("dummy server shutting down...")
        if server_socket is not None:
            server_socket.shutdown(socket.SHUT_RDWR)
            server_socket.close()


if __name__ == "__main__":
    main()