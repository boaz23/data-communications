import socket
import network

TEAM_NAME = 'NightcodeZakum'

IF_LOCALHOST = network.NetIf('lo', '127.0.0.1')
IF_DEV = network.NetIf('eth1', '172.1.255.255')
IF_TEST = network.NetIf('eth2', '172.99.255.255')

active_network_interface = IF_LOCALHOST

ANNOUNCMENT_PORT = 13117
ANNOUNCMENT_PROTOCOL = socket.SOCK_DGRAM