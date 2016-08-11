import socket
import sys
import Run_Servo
import time

udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientAddress = ('10.113.64.96', 12001)
udpSocket.bind(clientAddress)
serverAddress = ('10.113.65.152', 12001)

while (True):
    try:
        print >>sys.stdout, 'Waiting to receive'
        data, server = udpSocket.recvfrom(12001)
        print >>sys.stdout, data
        newData = data.split(" ")
        #newDataOne = newData[0::2]
        #newDataTwo = newData[1::2]
        #Run_Servo.setAngles(newDataOne, newDataTwo)
        .setAngles(newData)
    except KeyboardInterrupt:
        Run_Servo.originalPos([0, 1, 2, 3, 4])
        udpSocket.close()
        sys.exit()

        
#else:
    #print >>sys.stdout, 'closing socket'
    #udpSocket.close()
    #sys.exit()