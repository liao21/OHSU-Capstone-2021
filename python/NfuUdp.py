## NfuUdp.py
# Interface class for RP2009 NFU board
#
# Interface is via TCP and UDP messages to instruct the NFU to set limb mode
# and begin streaming data

import time
import socket

VERBOSE = 2

def main():
    """ 
    Run NFU interface
    """
    h = NfuUdp(Hostname="127.0.0.1")
    
    NUM_ARM_JOINTS = 7;
    NUM_HAND_JOINTS = 20;
    armPosition = [0.0]*NUM_ARM_JOINTS
    armVelocity = [0.0]*NUM_ARM_JOINTS
    handPosition = [0.0]*NUM_HAND_JOINTS
    handVelocity = [0.0]*NUM_HAND_JOINTS

    sendJointAngles(self,armPosition+armVelocity+handPosition+handVelocity)
    time.sleep(3)
    
    armPosition[3] = 0.1
    sendJointAngles(self,armPosition+armVelocity+handPosition+handVelocity)
    time.sleep(3)
    
    h.close()
    
  

class NfuUdp:
    """ 
    Python Class for NFU connections 
    
    Hostname is the IP of the NFU
    UdpTelemPort is where percepts and EMG from NFU are received locally
    UdpCommandPort
    TcpCommandPort

    These correspond on the NFU to files:
    % /fs/etfs/telem_port defaults to 9027
    % /fs/etfs/cmd_port defaults to 6200
    % /fs/etfs/cmd_udp_port defaults to 6201
    
    
    
    """

    def __init__(self, Hostname="192.168.1.111", UdpTelemPort=9027, TcpCommandPort=6200, UdpCommandPort=6201):
        self.Hostname = Hostname
        self.UdpTelemPort = UdpTelemPort
        #self.TcpCommandPort = TcpCommandPort
        self.UdpCommandPort = UdpCommandPort
        
        self.__UdpSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.__UdpSock.bind((Hostname, UdpTelemPort))

        # connect to TCP
        #self.__TcpSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #self.__TcpSock.bind((Hostname, UDP_PORT))

        # Enable Streaming
        #type = 5; NFU PERCEPTS
        msg = bytes([150, 9, 1, 0, 0, 0, 0, 0, 0, 0])
        self.sendUdpCommand(msg)
        
        # wait
        time.sleep(0.1)
        
        # TODO: Properly encode NFU Algorithm Messages. For now these are just hard coded
        
        # Set NFU Algorithm State
        val = 0
        # [NfuUdp] Setting NFU parameter NFU_run_algorithm to 0
        msg = bytes([    4,   78,   70,   85,   95,  114,  117,  110,   95,   97,  108,  103,  111,  114,  105,  116,  104,  109,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    8,    0,    0,    0,    1,    0,    0,    0,    1,    0,    0,    0,    0,    0,    0,    0])
        self.sendUdpCommand(msg)

        # wait
        time.sleep(0.1)
        
        # Set NFU output state
        val = 2
        #[NfuUdp] Setting NFU parameter NFU_output_to_MPL to 2
        msg = bytes([    4,   78,   70,   85,   95,  111,  117,  116,  112,  117,  116,   95,  116,  111,   95,   77,   80,   76,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    8,    0,    0,    0,    1,    0,    0,    0,    1,    0,    0,    0,    0,    0,    0,   64   ])
        self.sendUdpCommand(msg)
        
        # wait
        time.sleep(0.1)
        

    def sendJointAngles(self,values):
        
        MSG_ID = 1
        
        # Send data
        # size is 7 + 20 + 7 + 20
        # packing is one uint8 by 54 singles
        packer = struct.Struct('54f')
        msg = bytearray(MSG_ID)        
        msg.extend(packer.pack(*values))
        if VERBOSE > 1:
            print('Sending "%s"' % binascii.hexlify(packed_data), values)
        sendUdpCommand(self,msg)
        
    def sendUdpCommand(self,msg):
        self.__UdpSock.sendto(msg, (self.Hostname, self.UdpCommandPort))
        
        

    def close(self):
        """ Cleanup socket """
        print("\n\nClosing NfuUdp Socket IP={} Port={}".format(self.Hostname,self.UdpTelemPort) )
        self.__UdpSock.close()
        
        



    
    
    

if __name__ == "__main__":
    main()
