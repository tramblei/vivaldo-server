def all_packets():
    PACKET = {}
    PACKET['SONG_LIST'] =   "\x01".encode('ascii')
    PACKET['SHEET'] =       "\x02".encode('ascii')
    PACKET['START'] =       "\x03".encode('ascii')
    PACKET['START_ACK'] =   "\x04".encode('ascii')
    PACKET['NEXT'] =        "\x05".encode('ascii')
    PACKET['STOP'] =        "\x06".encode('ascii')
    PACKET['STOP_ACK'] =    "\x07".encode('ascii')
    PACKET['RCVD'] =        "\x08".encode('ascii')
    PACKET['ERR'] =         "\x09".encode('ascii')
    PACKET['BAD_MESSAGE'] = "\x0a".encode('ascii')
    return PACKET
