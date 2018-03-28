import socket

# Socket part
ANY = "0.0.0.0"
MCAST_ADDR = "239.255.1.1"
MCAST_PORT = 1600
#create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#allow multiple sockets to use the same PORT number
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#Bind to the port that we know will receive multicast data
sock.bind((ANY, MCAST_PORT))
#tell the kernel that we are a multicast socket
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
#Tell the kernel that we want to add ourselves to a multicast group
#The address for the multicast group is the third param
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
    socket.inet_aton(MCAST_ADDR) + socket.inet_aton(ANY))

while True:
    try:
        data, addr = sock.recvfrom(1024)
        print("Data, addr", data, addr)
    except socket.error:
        pass

