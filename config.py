import socket
import network

#**************************************************
#****************** Team Related ******************
#**************************************************
TEAM_NAME = 'NightcodeZakum'

#**************************************************
#**************** Network Interface ***************
#**************************************************
IF_LOCALHOST = network.NetIf('lo', '127.0.0.1')
IF_DEV = network.NetIf('eth1', '172.1.255.255')
IF_TEST = network.NetIf('eth2', '172.99.255.255')

active_network_interface = IF_LOCALHOST

#**************************************************
#******************** Encodings *******************
#**************************************************
STRING_ENCODING = 'utf-8'
INTEGER_ENDIANNESS = 'little'
INT_SIZE_8 = 1
INT_SIZE_16 = 2
INT_SIZE_32 = 4

#**************************************************
#******************* Game Offers *******************
#**************************************************
GAME_OFFER_PORT = 13117
GAME_OFFER_PROTOCOL = socket.SOCK_DGRAM
GAME_OFFER_MSG_SIZE = 7
GAME_OFFER_RECV_BUFFER_SIZE = 1 << 4 #16

MAGIC_COOKIE = 0xfeedbeef
MAGIC_COOKIE_SIZE = INT_SIZE_32
MSG_TYPE_OFFER = 0x2
MSG_TYPE_OFFER_SIZE = INT_SIZE_8

SERVER_OFFER_SENDING_DURATION = 10
GAME_OFFER_WAIT_TIME = 0.5

#**************************************************
#****************** General Stuff *****************
#**************************************************
PORT_NUM_SIZE = INT_SIZE_16
SERVER_GAME_PORT = 54432
SERVER_RECV_BUFFER_SIZE = 1 << 11 #2048
RETRY_TIME = 0.1
