""" Simple Server Example

This script creates a socket and listens for connections
on any IPv4 interface on port 9090. When a connection is
established, the server waits for a GET or POST command.

Endpoint Codes: 

Code 

Message Type 

0x1 SONG_LIST 

0x2 SHEET 

0x3 START 

0x4 START_ACK (from server) 

0x5 NEXT 

0x6 STOP 

0x7 STOP_ACK (from server) 

0x8 RCVD (from FPGA) 

"""
import socket
import wav_to_fft
import glob
import struct
import packets
import sys
import time
import os.path

PORT = 9091
BUFFER_SIZE = 1024
PACKET = packets.all_packets()
SONG_DIRECTORY = "sample_wav_files"
FILE_EXT = ".wav"

DEBUG_ALL = 0
DEBUG_RCV = DEBUG_ALL | 0
DEBUG_ARGS = DEBUG_ALL | 0
DEBUG_CMD = DEBUG_ALL | 0

def set_debug_modes():
    global DEBUG_ALL
    global DEBUG_RCV
    global DEBUG_ARGS
    global DEBUG_CMDS
    DEBUG_RCV = DEBUG_ALL 
    DEBUG_ARGS = DEBUG_ALL
    DEBUG_CMD = DEBUG_ALL

# define different streaming modes
# Stream mode 1: Streams frames in separate TCP connections
# stream mode 2: Streams a batch of frames in one connection
# stream mode 3: Streams all frames of song at once
STRM_SEPARATE = 1
STRM_BATCH = 2 #expects the number to be streamed to follow in two bytes after it
STRM_SONG = 3
STREAM_MODE = STRM_SEPARATE

# RCVD  = 1 - expects a RCVD packet after each frame
# RCVD  = 0 - packets are sent out, no need for acknowledgement
RCVD_ACK = 1

# global song information
current_song = None
current_frame_size = 1024
song_buffer = []
current_frame = -1
fft_bits = 32
ffts_actual_bits = 16 # need to pad out to 32 bits
fft_size = 1024

def reinit_current_song():
    global current_song
    global current_frame_size
    global song_buffer
    global current_frame
    current_song = None
    current_frame_size = 0
    song_buffer = []
    current_frame = -1

def debug_printf(debug, string):
    if debug:
        print(string)

def close_connection(conn, message):
    if message != None:
        conn.send(message)

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()

def initialize_song():
    # get the current song
    global current_song
    global current_frame_size
    global song_buffer
    global current_frame
    global fft_bits
    global fft_size
    global ffts_actual_bits
    if current_song:
        # note that fft_size is the size of the FFT
        # whereas frame size is the number of bytes packed in each frame
        # thus, with fft_bits/8 (2bytes per point if fft_bits = 16):
        #       current_frame_size/(fft_bits/8*fft_size) = number of fft frames per TCP frame
        # note that the FFT is actually divided in two (symmetrical), so need
        # to request twice as many points
        ffts = wav_to_fft.convert_wav_to_fft(current_song, fft_size, ffts_actual_bits)
        # these need to be byte arrays
        bytes_per_point = 0

        print(len(ffts[0]))

        # determines number of bytes in each point
        # and pads as necessary
        # treat all as unsigned

        if fft_bits <= 8:
            struct_pack = 'B'
            bytes_per_point = 1
        elif fft_bits <= 16:
            struct_pack = 'H'
            bytes_per_point = 2
        elif fft_bits <=32:
            struct_pack = 'I'
            bytes_per_point = 4
        else:
            struct_pack = 'Q'
            bytes_per_point = 8
        
        print("Current frame size: " + str(current_frame_size))
        print("Bytes per point: " + str(bytes_per_point))
        print("FFT size: " + str(fft_size))
        tcp_frames_per_fft = int((bytes_per_point*fft_size)/current_frame_size)
        print("FFT frames/TCP: " + str(tcp_frames_per_fft))
        i = 0
        # over all ffts
        song_buffer=[]

        while i < len(ffts):
            # need to consume ${fft_frames_per_tcp} in a single TCP frame
            for j in range(tcp_frames_per_fft):
                ba = b""
                so_far = j*int(current_frame_size/bytes_per_point)
                for k in range(so_far, so_far + int(current_frame_size/bytes_per_point)):
                    a = struct.pack(struct_pack, int(ffts[i][k]))
                    ba += a

                # move to next frame
                song_buffer.append(ba)
            i=i+1
                

        print(len(song_buffer))
        # pad last with 0s
#        for i in range(len(song_buffer[0]) -  len(song_buffer[-1])):
#            song_buffer[-1] += b"\x00"
        current_frame = 0
    else:
        debug_printf(DEBUG_ALL, "No song selected - cannot initialize song")

# all songs in system
# songs = glob.glob(SONG_DIRECTORY + "/" + FILE_EXT)
songs = []
for file in os.listdir(SONG_DIRECTORY):
    if file.endswith(FILE_EXT):
        songs.append(os.path.join(SONG_DIRECTORY, file))

if __name__ == '__main__':
    DEBUG_ALL = 1
    DEBUG_RCV = DEBUG_ALL | 0
    DEBUG_ARGS = DEBUG_ALL | 0
    DEBUG_CMD = DEBUG_ALL | 0
    start = 0
    end = 0
    for i in range(1,len(sys.argv)):
        if sys.argv[i] == '--rcvd-off':
            debug_printf(DEBUG_CMD, "Turning NEXT RCVD handshake off")
            RCVD_ACK = 0
        elif sys.argv[i] == '--stream-batch':
            debug_printf(DEBUG_CMD, "Streaming in batch")
            STREAM_MODE = STRM_BATCH
        elif sys.argv[i] == '--stream-song':
            debug_printf(DEBUG_CMD, "Streaming full song")
            STREAM_MODE = STRM_SONG
        elif sys.argv[i] == '--stream-sep':
            debug_printf(DEBUG_CMD, "Streaming in individual packets")
            STREAM_MODE = STRM_SEPARATE
        elif sys.argv[i] == '--debug-all':
            DEBUG_ALL = 1
            set_debug_modes()
            debug_printf(DEBUG_CMD, "Turning on full debugging")
        elif sys.argv[i] == '--debug-rcv':
            DEBUG_RCV = 1
            debug_printf(DEBUG_CMD, "Turning on receive debugging")
        elif sys.argv[i] == '--debug-cmd':
            DEBUG_CMD = 1
            debug_printf(DEBUG_CMD, "Turning on command-line argument debugging")
        elif sys.argv[i] == '--debug-args':
            DEBUG_ARGS = 1
            debug_printf(DEBUG_CMD, "Turning on endpoint-argument debugging")
        else:
            debug_printf(DEBUG_CMD, "Skipping invalid argument: " + sys.argv[i])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Allow re-binding the same port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.TCP_MAXSEG, 8196)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16392)
        # Bind to port on any interface
        sock.bind(('0.0.0.0', PORT))
        sock.listen(100) # allow backlog of 1
    
        print("BEGIN LISTENING ON PORT", PORT)
        # Begin listening for connections
        while(True):
            conn, addr = sock.accept()
            with conn:
#                print("\nCONNECTION:", addr)
                # Receive and handle command
                while(True):
                    data = conn.recv(BUFFER_SIZE)
                    debug_printf(DEBUG_RCV, "Received: " + str(data))
                    if data[0] == PACKET['SONG_LIST'][0]:
                        debug_printf(DEBUG_RCV, "Requesting song list")
                        song_string = ""
                        for s in songs:
                            song_string += s
                            song_string += "\x03"
                        song_string += '\x04'
                        close_connection(conn, song_string.encode('ascii'))
                        break
                    elif data[0] == PACKET['SHEET'][0]:
                        debug_printf(DEBUG_RCV, "Requesting sheet music")
                        close_connection(conn, None)
                        break
                    elif data[0] == PACKET['START'][0]:
                        # receiving a song name, ending with 0x3, with 2bytes following
                        # forming the size of the frame for this stream
                        debug_printf(DEBUG_RCV, "Requesting start of stream")
                        start = time.clock()

                        # split the song from it
                        song_name_actual = data[1:-3].decode('ascii').split('\x03')[0]
                        song_name = os.path.join(SONG_DIRECTORY, song_name_actual)
                        debug_printf(DEBUG_RCV, "Song stripped: " + str(song_name))
                        if not song_name in songs:
                            # send back error - song doesnt exist
                            debug_printf(DEBUG_ARGS, "Song not found. Received: " + song_name)
                            close_connection(conn, PACKET['ERR'])
        
                        current_song = song_name
                        
                        # get number of bytes for frames
                        # assume big endian
                        bytes_len = int.from_bytes(data[1 + len(song_name_actual) + 1:], byteorder='big')
                        current_frame_size = bytes_len
                        #initializes the song
                        # opens file, converts to FFT, stores frames, and 
                        # puts cursor in start position
                        debug_printf(DEBUG_ARGS, "Frame size: " + str(current_frame_size))
                        debug_printf(DEBUG_ARGS, "Requested song: " + current_song)
                        initialize_song()
                        close_connection(conn, PACKET['START_ACK'])
                        break
        
                    elif data[0] == PACKET['NEXT'][0]:
        
                        # streams it in batch mode - expects a number of requests to follow
                        num_to_follow = 0
                        if STREAM_MODE == STRM_BATCH:
                            num_to_follow = int.from_bytes(data[-2:], byteorder='big')
                            if num_to_follow > len(song_buffer) - current_frame:
                                num_to_follow = len(song_buffer) - current_frame # limit near end of song
                        elif STREAM_MODE == STRM_SEPARATE:
                            num_to_follow = 1
                        elif STREAM_MODE == STRM_SONG:
                            num_to_follow = len(song_buffer) - current_frame # rest of song
        
                        debug_printf(DEBUG_RCV, "Requesting next frame")
                        ending = b""
                        if current_frame == -1:
                            # stream is not open
                            debug_printf(DEBUG_RCV, "Asked for frame with no stream open")
                            close_connection(conn, PACKET['ERR'])
                        elif current_frame == len(song_buffer):
                            # cannot request
                            debug_printf(DEBUG_RCV, "Asked for frame beyond stream end")
                            reinit_current_song()
                            close_connection(conn, PACKET['ERR'])
                            break
        
                        # stream loop now
                        frame_to_send = 0
                        while frame_to_send < num_to_follow:
                            debug_printf(DEBUG_RCV, "Length of song_buffer: " + str(len(song_buffer)))
                            # start it with frame position
                            beginning = b"\xFF\xFF\xFF\xFF"
                            ending = b"\x04"
                            if current_frame < len(song_buffer) - 1:
                                # should end with 0x03
                                ending = b"\x03"
                                beginning = struct.pack('i', current_frame)
                                debug_printf(DEBUG_RCV, "Frame bytes: " + str(beginning))
                            else:
                                end = time.clock()
                                print("Time to download song: " + str(end - start))
                            ba = beginning + song_buffer[current_frame]
        
    #                        ba += ending
                            conn.send(ba)
                             
                            if None:
                                while data[0] != PACKET['RCVD'][0] and data[0] != PACKET['STOP'][0]:
                                    data = conn.recv(BUFFER_SIZE)
                                
                                # might need fix - since connection will be closed twice
                                if data[0] == PACKET['STOP'][0]:
                                        #reinit_current_song()
                                    close_connection(conn, PACKET['STOP_ACK'])
                                debug_printf(DEBUG_RCV, "Got a RCVD")
        
                            current_frame += 1
                            frame_to_send += 1

                        # reached the end time to leave
                        #reinit_current_song()
                        close_connection(conn, None)
                        break
                        
                    elif data[0] == PACKET['STOP'][0]:
                        debug_printf(DEBUG_RCV, "Requesting stop frame")
                        reinit_current_song()
                        close_connection(conn, PACKET['STOP_ACK'])
                        break
                    elif data[0] == PACKET['RCVD'][0]:
                        debug_printf(DEBUG_RCV, "Receive frame ACK")
                        current_frame += 1 # increase frame counter 
                        close_connection(conn, None)
                        break
                    else:
                        debug_printf(DEBUG_RCV, "BAD COMMAND SENT")
                        close_connection(conn, PACKET['BAD_MESSAGE'])
                        break


