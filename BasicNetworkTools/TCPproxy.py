import sys
import socket
import threading


#region hexdump
# Sockets send information in bytes. In north america, almost all data transfered should be decoded to UTF-8 on arrival.
# This hex filter will convert byte or string inputs to hex. If the byte can be represented as an ASCII character, it will be displayed. Otherwise it will be shown as a '.'
HEX_FILTER = ''.join(
    [(len(repr(chr(i)))==3) and chr(i) or '.' for i in range(256)]
)

def hexdump(src, length=16, show=True):
    # Check if 'src' is of the type 'bytes'. If so, convert the bytes to UTF-8.
    if isinstance(src, bytes):
        src = src.decode()

    results = list()
    # Take the decoded info and separate it out into chunks of 16 characters.
    for i in range(0, len(src), length):
        word = str(src[i:i+length])

        # Start a hex block with a space and then two characters
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        hexwidth = length*3
        printable = word.translate(HEX_FILTER)

        # Formatting notes: 04X displays i in capital hex, <{hexwidth} displays hexa left aligned and takes up width of hexwidth.
        results.append(f'{i:04X} {hexa:<{hexwidth}} {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results
#endregion


#region buildBuffer
# Receive data from remote connection and local connection. Adds the bytecode to a buffer. Within a loop, the socket will continuously check for received information and 
# will wait a max of 5 seconds before ending the connection. Increase timeout as necessary, especially if communicating with distant targets.
def receive_from(connection):
    buffer = b''
    connection.settimeout(5)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer
#endregion


#region proxyHandler
# This section performs the logic of the proxy. It is already connected to the local socket, so it starts by connecting to the remote host.
# The rest of the logic fosuses on modifying the incoming and outgoing buffers and switching back and forth as necessary.
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # This checks if we need to forward any information from the remote host to the local host upon connecting. For example, an FTP server
    # will send a banner when a connection is made.
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

    remote_buffer = response_handler(remote_buffer)
    if len(remote_buffer):
        print(f'[<=] Sending {len(remote_buffer)} bytes to localhost.')
        client_socket.send(remote_buffer)

    # This section alternates back and forth between the local connection and the remote connection to add data to the buffer.
    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print(f'[<=] Sending {len(local_buffer)} bytes from localhost.')
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print('[=>] Sent to remote.')

        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print(f'[<=] Received {len(remote_buffer)} bytes from remote.')
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print('[=>] Sent to localhost.')

        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print('[*] No more data. Closing connections.')
            break

def request_handler(buffer):
    # modify buffer here
    return buffer

def response_handler(buffer):
    # modify buffer here
    return buffer
#endregion


#region serverLoop
# Start the proxy server by binding to a local address. After confirming success, create a thread to connect to the remote host.
def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print(f'Problem on bind: {e}')
        print(f'[!!] Failed to listen on {local_host}:{local_port}')
        print('[!!] Check for other listening sockets or correct permissions.')
        sys.exit(0)

    print(f'[*] Listening on {local_host}:{local_port}')
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        print(f'> Received incoming connection from {addr[0]}:{addr[1]}')
        proxy_thread = threading.Thread(target=proxy_handler, args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()
#endregion


#region main
def main():
    if len(sys.argv[1:]) != 5:
        print('Usage: ./TCPproxy.py [localhost] [localport]', end='')
        print('[remotehost] [remoteport] [receivefirst]')
        print('Example: ./TCPproxy.py 127.0.0.1 9000 10.12.132.1 9000 True')
        sys.exit(0)
    local_host = sys.argv[1]
    local_port = sys.argv[2]
    remote_host = sys.argv[3]
    remote_port = sys.argv[4]
    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
    
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

if __name__ == '__main__':
    main()
#endregion