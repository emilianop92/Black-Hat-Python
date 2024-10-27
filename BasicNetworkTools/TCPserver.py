import socket
import threading

ip = '0.0.0.0'
port = 9998

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    # backlog number below is the number of connections the server will accept
    server.listen(5)

    while True:
        # save server connections to the client and address veriables
        client, address = server.accept()
        # create a multi-threading object based on handle_client(client)
        client_handler = threading.Thread(target=handle_client, args=(client,), )
        client_handler.start()

def handle_client(client_socket):
    with client_socket as sock:
        request = sock.recv(4096)
