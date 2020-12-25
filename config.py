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
#************** Announcement Message **************
#**************************************************
GAME_OFFER_PORT = 13117
GAME_OFFER_PROTOCOL = socket.SOCK_DGRAM
GAME_OFFER_MSG_SIZE = 7

MAGIC_COOKIE = 0xfeedbeef
MAGIC_COOKIE_SIZE = INT_SIZE_32
MSG_TYPE_OFFER = 0x2
MSG_TYPE_OFFER_SIZE = INT_SIZE_8
PORT_NUM_SIZE = INT_SIZE_16

#**************************************************
#********************* Server *********************
#**************************************************
PORT_INT_SIZE = INT_SIZE_16
SERVER_GAME_PORT = 12000
