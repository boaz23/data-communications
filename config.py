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
ENCODING_INTEGER_ENDIANNESS = 'little'
INT_SIZE_8 = 8
INT_SIZE_16 = 16
INT_SIZE_32 = 32

#**************************************************
#************** Announcement Message **************
#**************************************************
ANNOUNCEMENT_PORT = 13117
ANNOUNCEMENT_PROTOCOL = socket.SOCK_DGRAM

MAGIC_COOKIE = 0xfeedbeef
MAGIC_COOCKIE_SIZE = INT_SIZE_32
MSG_TYPE_OFFER = 0x2
MSG_TYPE_OFFER_SIZE = INT_SIZE_8
PORT_NUM_SIZE = INT_SIZE_16
