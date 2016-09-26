## NfuUdp.py
# Interface class for RP2009 NFU board
#
# Interface is via TCP and UDP messages to instruct the NFU to set limb mode
# and begin streaming data

import time
import socket
import binascii
import struct

VERBOSE = 2

def main():
    """ 
    Run NFU interface
    """
    

    
    h = NfuUdp(Hostname="192.168.1.111")
    
    NUM_ARM_JOINTS = 7;
    NUM_HAND_JOINTS = 20;
    armPosition = [0.0]*NUM_ARM_JOINTS
    armVelocity = [0.0]*NUM_ARM_JOINTS
    handPosition = [0.0]*NUM_HAND_JOINTS
    handVelocity = [0.0]*NUM_HAND_JOINTS

    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
    time.sleep(3)
    
    armPosition[3] = 0.3
    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
    time.sleep(3)
    
    
    #quick output of test for msgUpdateParam
    print('\n\n\nstarting test of msgUpdateParam:\n')
    a = [[i*3.1415+j for i in list(range(10))] for j in list(range(13))]    #create random 2D float array for sample class data
    
    aClass = type('param', (object,), dict(Value=a,Dimensions=[len(a),len(a[0])],Description='Generic Description of object'))  #define class in form of expected data
    
    print(aClass)
    print(aClass.Value)
    print(aClass.Dimensions)
    print('\n')
    print(h.msgUpdateParam(aClass))
    #end of output of test for msgUpdateParam
    
    
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
        val = 0
        # [NfuUdp] Setting NFU parameter NFU_run_algorithm to 0
        msg2 = bytearray([    4,   78,   70,   85,   95,  114,  117,  110,   95,   97,  108,  103,  111,  114,  105,  116,  104,  109,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    8,    0,    0,    0,    1,    0,    0,    0,    1,    0,    0,    0,    0,    0,    0,    0])
        self.sendUdpCommand(msg2)

        # wait
        time.sleep(0.1)
        
        # Set NFU output state
        val = 2
        #[NfuUdp] Setting NFU parameter NFU_output_to_MPL to 2
        msg3 = bytearray([    4,   78,   70,   85,   95,  111,  117,  116,  112,  117,  116,   95,  116,  111,   95,   77,   80,   76,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    8,    0,    0,    0,    1,    0,    0,    0,    1,    0,    0,    0,    0,    0,    0,   64   ])
        self.sendUdpCommand(msg3)
        
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
        if VERBOSE > 1:
            print('Sending "%s"' % binascii.hexlify(msg), values)
        print(sum(msg) % 256)
        chksum = bytearray([sum(msg) % 256])
        out = bytearray([61])
        out.extend(msg)
        out.extend( chksum )

        self.sendUdpCommand(out)
        print('Out "%s"' % binascii.hexlify(out))
        
    def sendUdpCommand(self,msg):
        self.__UdpSock.sendto(msg, (self.Hostname, self.UdpCommandPort))
        
    
    
    def msgUpdateParam(self,param):
        #update_param Summary of this function goes here
        #Translated from MATLAB to Python by David Samson on 9/23/16
        
        # calculate dimensions
        dim_X = bytearray(struct.pack('I',param.Dimensions[0]))
        dim_Y = bytearray(struct.pack('I',param.Dimensions[1]))
        
        
        # calculate fields
        bval = bytearray(4*param.Dimensions[0]*param.Dimensions[1])
        
        #convert 2D float32 array to 1D byte array
        for i in list(range(param.Dimensions[0])):
            for j in list(range(param.Dimensions[1])):
                #c = bytearray(struct.pack('f',param.Value[i,j])) ####May need to use this line instead of the one below ####
                c = bytearray(struct.pack('f',param.Value[i][j])) ####based on how the array param.Value is indexed      ####
                bval[((j*param.Dimensions[0] + i) * 4) : ((j*param.Dimensions[0] + i) * 4) + 4] = c
                
        
        msgId = 4
        write_cfg_Nfu = bytearray([msgId]) +  bytearray(param.Description,'utf-8') + bytearray(128-len(param.Description)) + bytearray([8, 0, 0, 0]) + dim_X + dim_Y + bval[:]
        
        msg = write_cfg_Nfu
        return msg
    

    
    
    def close(self):
        """ Cleanup socket """
        print("\n\nClosing NfuUdp Socket IP={} Port={}".format(self.Hostname,self.UdpTelemPort) )
        self.__UdpSock.close()
        
        



    
    
    

if __name__ == "__main__":
    main()
