# When in a network locally, there may not exist any tools (like browsers) to connect to the internet like a browser.
# A TCP client would let you connect to a website to download the html and extract the data you need.

import socket

targetHost = 'www.google.com'
targetPort = 80

# Create a socket object. AF_INET and SOCK_STREAM are parameters for the type of socket wanted.
# AF_INET indicates the socket is of Address Family - Internet IPv4.
# SOCK_STREAM indicates the connection is of TCP type.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((targetHost, targetPort))

# send data. 
# Data sent over a network must be in byte data type. Use b'' to send data in byte type, not string.
client.send(b'GET HTTP/1.1\r\nHost: google.com\r\n\r\n')

# data is automatically received. Save to variable. 4096 is the buffer size.
response = client.recv(4096)

print(response)
print()
print(response.decode())

# close connection so google server doesn't continue to wait
client.close()