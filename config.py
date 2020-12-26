"""Various configuraions of both the client and the server
"""

import socket
import network

#**************************************************
#****************** Team Related ******************
#**************************************************
TEAM_NAME = 'NightcodeZakum'

#**************************************************
#**************** Network Interface ***************
#**************************************************
# The various network interfaces we can connect to
IF_LOCALHOST = network.NetIf('lo', '127.0.0.1')
IF_DEV = network.NetIf('eth1', '172.1.255.255')
IF_TEST = network.NetIf('eth2', '172.99.255.255')

# The active network interface that will actually be used
# by the client and the server to create sockets and connect to the
# network
active_network_interface = IF_LOCALHOST

#**************************************************
#******************** Encodings *******************
#**************************************************
# Controls how to encode and decode various data
STRING_ENCODING = 'utf-8'
INTEGER_ENDIANNESS = 'little'

# Sizes of integer fields of structs in bytes
INT_SIZE_8 = 1
INT_SIZE_16 = 2
INT_SIZE_32 = 4

#**************************************************
#******************* Game Offers *******************
#**************************************************
# Constants related to game offers
GAME_OFFER_PORT = 13117
GAME_OFFER_PROTOCOL = socket.SOCK_DGRAM
GAME_OFFER_MSG_SIZE = 7
# The size of the client's buffer when receiving game offer packets
# (sent to 'recv' as a parameter)
GAME_OFFER_RECV_BUFFER_SIZE = 1 << 4 #16

MAGIC_COOKIE = 0xfeedbeef
MAGIC_COOKIE_SIZE = INT_SIZE_32
MSG_TYPE_OFFER = 0x2
MSG_TYPE_OFFER_SIZE = INT_SIZE_8

# The duration for which the server keeps sending (broadcasting) game offers to clients
SERVER_OFFER_SENDING_DURATION = 10
# The amount of time the server waits between sending two consecutive game offers packets
GAME_OFFER_WAIT_TIME = 0.5

#**************************************************
#****************** General Stuff *****************
#**************************************************

# The size of port number fields in various structs
PORT_NUM_SIZE = INT_SIZE_16
# The port which the server will accept game connections
SERVER_GAME_PORT = 54432
# The size of the buffer of the server when reading clients data from
# the socket connection with the client
SERVER_RECV_BUFFER_SIZE = 1 << 11 #2048
RETRY_TIME = 0.1
