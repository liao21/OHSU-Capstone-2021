## NfuUdp.py
# Interface class for RP2009 NFU board
#
# Interface is via TCP and UDP messages to instruct the NFU to set limb mode
# and begin streaming data

import time
import socket
import binascii
import struct
import numpy as np

VERBOSE = 2

def main():
    """ 
    Run NFU interface
    """    
    
    # Establish netork inferface to MPL at address below
    h = NfuUdp(Hostname="192.168.1.111")
    
    # Run a quick motion test to vreify joints are working
    NUM_ARM_JOINTS = 7;
    NUM_HAND_JOINTS = 20;
    armPosition = [0.0]*NUM_ARM_JOINTS
    armVelocity = [0.0]*NUM_ARM_JOINTS
    handPosition = [0.0]*NUM_HAND_JOINTS
    handVelocity = [0.0]*NUM_HAND_JOINTS

    # goto zero position
    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
    time.sleep(3)

    # goto elbow bent position
    armPosition[3] = 0.3
    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
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
        #self.__UdpSock.bind((Hostname, UdpTelemPort))

        # connect to TCP
        #self.__TcpSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #self.__TcpSock.bind((Hostname, UDP_PORT))

        # Enable Streaming
        #type = 5; NFU PERCEPTS
        msg1 = bytearray([150, 9, 1, 0, 0, 0, 0, 0, 0, 0])
        self.sendUdpCommand(msg1)
        
        # wait
        time.sleep(0.1)
        
        # TODO: Properly encode NFU Algorithm Messages. For now these are just hard coded
        
        # Set NFU Algorithm State
        # [NfuUdp] Setting NFU parameter NFU_run_algorithm to 0
        self.sendUdpCommand(self.msgUpdateParam('NFU_run_algorithm',0))

        # wait
        time.sleep(0.1)
        
        # Set NFU output state
        #[NfuUdp] Setting NFU parameter NFU_output_to_MPL to 2
        self.sendUdpCommand(self.msgUpdateParam('NFU_output_to_MPL',2))
        
        # wait
        time.sleep(0.1)
        

    def sendJointAngles(self,values):
        
        MSG_ID = 1
        
        # Send data
        # size is 7 + 20 + 7 + 20
        # packing is one uint8 by 54 singles
        # total message is 221 bytes [uint16 MSD_ID_FIELD_BYTES]
        # (61) NFU ID + uint16 MSG_LENGTH + uint8 MSG_TYPE + 1 MSG_ID + Payload + Checksum
        packer = struct.Struct('54f')
        msg = bytearray([219, 0, 5, 1])
        msg.extend(packer.pack(*values))
        if VERBOSE >= 2:
            print('Sending "%s"' % binascii.hexlify(msg), values)
        #print(sum(msg) % 256)
        chksum = bytearray([sum(msg) % 256])
        out = bytearray([61])
        out.extend(msg)
        out.extend( chksum )

        self.sendUdpCommand(out)
        #print('Out "%s"' % binascii.hexlify(out))
        
    def sendUdpCommand(self,msg):
    
        if VERBOSE >= 2:
            print(msg)
        self.__UdpSock.sendto(msg, (self.Hostname, self.UdpCommandPort))
        
    
    
    def msgUpdateParam(self,paramName, paramValue):
        #update_param Summary of this function goes here
        #Translated from MATLAB to Python by David Samson on 9/23/16
        #Armiger simplified and tested 9/27/16
        
        if VERBOSE >= 1:
            print('Converting bytes from parameter: ' + paramName)

        if len( paramName ) > 127 :
            print('Trimming Name to max 127 characters')
            paramName = paramName[:127]
        
        
        # convert to numpy matrix        
        A = np.matrix(paramValue, dtype=np.dtype('<f4'))  # little-endian single-precision float
        
        # calculate dimensions
        dimA = A.shape

        # convert to byte array
        bval = A.tobytes()

        # format message
        msgId = 4
        write_cfg_Nfu = bytearray([msgId]) +  bytearray(paramName,'utf-8') + bytearray(128-len(paramName)) + bytearray([8, 0, 0, 0]) + bytearray(dimA[0]) + bytearray(dimA[1]) + bval[:]
        
        msg = write_cfg_Nfu
        return msg
    

    
    
    def close(self):
        """ Cleanup socket """
        print("\n\nClosing NfuUdp Socket IP={} Port={}".format(self.Hostname,self.UdpTelemPort) )
        self.__UdpSock.close()
    

if __name__ == "__main__":
    main()
