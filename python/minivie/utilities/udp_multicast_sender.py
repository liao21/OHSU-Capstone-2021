import socket

ANY = "0.0.0.0"
SENDERPORT = 32000
MCAST_ADDR = "239.255.1.1"
MCAST_PORT = 1600

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
    socket.IPPROTO_UDP)
sock.bind((ANY, SENDERPORT))
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.sendto(b'Okay', (MCAST_ADDR, MCAST_PORT))
