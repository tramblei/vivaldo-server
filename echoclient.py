""" Simple Client Example

This script makes three separate connections to a sever
located on the same computer on port 9090. During the
first connection a 'GET' command is issued to receive the
current value in the server. A subsequent connection updates
the value to 0xBAADF00D and this value is read back during
the final connection.
"""

import socket
import packets
import time

PACKET = packets.all_packets()

REQUEST_SIZE = 8192
BUFFER_SIZE = REQUEST_SIZE*2 + 1
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 9091

# GET current value
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((SERVER_ADDR, SERVER_PORT))
    sock.send(PACKET['SONG_LIST'])
    data = sock.recv(BUFFER_SIZE)
    # split by the special character, 0x3
    vals = data.decode('ascii').split('\x03')
    print("Songs list from server is: ", )
    assert(vals[-1] == "\x04")
    for i in range(len(vals) - 1):
        print(vals[i])
    sock.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # request first song
    print("Requesting a song to start: " + vals[0])
    sock.connect((SERVER_ADDR, SERVER_PORT))
    byte_string = PACKET['START'].decode('ascii')
    byte_string += vals[0]
    byte_string += "\x03"
    # want 1024 size frames
    byte_string += "\x20\x00"
    sock.send(byte_string.encode('ascii'))

    # need to receive START_ACK
    data = sock.recv(BUFFER_SIZE)
    if data[0] != PACKET['START_ACK'][0]:
        print("No START_ACK RECEIVED")


end_of_song = False
start = time.time()
counter = 0
while not end_of_song:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # request first song
        print("Streaming frames from song: " + vals[0])
        sock.connect((SERVER_ADDR, SERVER_PORT))
        sock.send(PACKET['NEXT'])
        data = sock.recv(BUFFER_SIZE)
        counter += 1
    
        if data[-1] == 0x04:
            end_of_song = True
        sock.send(PACKET['RCVD']) # acknowledge

end = time.time()
print("Number of packets: " + str(counter))
print("Time elapsed: " + str(end - start))

