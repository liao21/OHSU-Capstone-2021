## NfuUdp.py
# Interface class for RP2009 NFU board
#
# Interface is via TCP and UDP messages to instruct the NFU to set limb mode
# and begin streaming data
#
# Usage: python NfuUdp.py
# Help: python NfuUdp.py -h


import argparse
import sys
from datetime import datetime
import time
import socket
import logging
import binascii
import struct
import numpy as np
import os
import struct

VERBOSE = 2

def main():
    """ 
    Run NFU interface as standalone test function
    """
    # Establish network inferface to MPL at address below
    #h = NfuUdp(Hostname="192.168.1.111")
    h = NfuUdp(Hostname="localhost")
    
    # Run a quick motion test to verify joints are working
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

    # test percept decoding
    f = open(os.path.join(os.path.dirname(__file__), "tests\\heartbeat.bin"), "r")
    uint8_heartbeat = np.fromfile(f, dtype=np.uint8)
    print('Testing heartbeat uint8 decoding...')
    h.decode_heartbeat_msg(uint8_heartbeat)
    print('Testing heartbeat byte decoding...')
    bytes_heartbeat = uint8_heartbeat.tobytes()
    h.decode_heartbeat_msg(bytes_heartbeat)

    h.close()
    logging.info('Ending NfuUdp')
    logging.info('-----------------------------------------------')
    
  

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

    def __init__(self, Hostname="192.168.1.111", UdpTelemPort=9027, UdpCommandPort=6201):
        self.Hostname = Hostname
        self.UdpTelemPort = UdpTelemPort
        self.UdpCommandPort = UdpCommandPort
        
        self.__UdpSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        #self.__UdpSock.bind((Hostname, UdpTelemPort))

        # Enable Streaming
        #type = 5; NFU PERCEPTS
        msg1 = bytearray([150, 9, 1, 0, 0, 0, 0, 0, 0, 0])
        self.sendUdpCommand(msg1)
        
        # wait
        time.sleep(0.1)
        
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
        # Transmit joint angle command in radians

        logging.info('Joint Command:')
        logging.info(["{0:0.2f}".format(i) for i in values[0:27]])
        
        MSG_ID = 1
        
        # Send data
        # size is 7 + 20 + 7 + 20
        # packing is one uint8 by 54 singles
        # total message is 221 bytes [uint16 MSD_ID_FIELD_BYTES]
        # (61) NFU ID + uint16 MSG_LENGTH + uint8 MSG_TYPE + 1 MSG_ID + Payload + Checksum
        packer = struct.Struct('54f')
        msg = bytearray([219, 0, 5, 1])
        msg.extend(packer.pack(*values))
        chksum = bytearray([sum(msg) % 256])

        # add on the NFU routing code '61' and checksum
        out = bytearray([61])
        out.extend(msg)
        out.extend( chksum )

        self.sendUdpCommand(out)
        
    def sendUdpCommand(self,msg):
        # transmit packets (and optinally write to log for DEBUG)
        
        logging.debug('Sending "%s"' % binascii.hexlify(msg))
        self.__UdpSock.sendto(msg, (self.Hostname, self.UdpCommandPort))
    
    def msgUpdateParam(self,paramName, paramValue):
        #msgUpdateParam - Create encoded byte array for parameter message to OpenNFU
        #
        # Function supports a parameter name up to 127 characters and a matrix variable
        #   as a single precision floating point variable.  Matrix dimentions are calculated
        #   internally and transmited as part of message
        #
        #Translated from MATLAB to Python by David Samson on 9/23/16
        #Armiger simplified and tested 9/27/16
        
        logging.info('Setting parameter %s, %f', paramName, paramValue)

        if len( paramName ) > 127 :
            logging.warn('msgUpdateParam:Trimming Name to max 127 characters')
            paramName = paramName[:127]
        
        # convert to numpy matrix        
        A = np.matrix(paramValue, dtype=np.dtype('<f4'))  # little-endian single-precision float
        
        # calculate dimensions
        dimA = np.array(A.shape,dtype=np.uint32)

        # convert to byte array
        #bval = A.tobytes()
        bval = A.tostring() # compatibility alias for tobytes

        # format message
        msgId = 4
        msg = bytearray([msgId]) +  bytearray(paramName,'utf-8') + bytearray(128-len(paramName)) \
                        + bytearray([8, 0, 0, 0]) + bytearray(dimA) + bval[:]
        
        return msg
    
    def close(self):
        """ Cleanup socket """
        logging.info("Closing NfuUdp Socket IP={} Port={}".format(self.Hostname,self.UdpTelemPort) )
        self.__UdpSock.close()

    def decode_heartbeat_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B'*36, b[0:36])
            b = np.array(b, np.uint8)

        # List of software states
        nfuStates = [
                    'SW_STATE_INIT',
                    'SW_STATE_PRG',
                    'SW_STATE_FS',
                    'SW_STATE_NOS_CONTROL_STIMULATION',
                    'SW_STATE_NOS_IDLE',
                    'SW_STATE_NOS_SLEEP',
                    'SW_STATE_NOS_CONFIGURATION',
                    'SW_STATE_NOS_HOMING',
                    'SW_STATE_NOS_DATA_ACQUISITION',
                    'SW_STATE_NOS_DIAGNOSTICS',
                    'SW_STATE_NUM_STATES',
                    ]

        msg = {}
        # Recast from uint8 to correct format
        msg['SW_STATE'] = b[0:4].view(np.uint32)[0]
        msg['strState'] = nfuStates[msg['SW_STATE']]
        msg['numMsgs'] = b[4:8].view(np.uint32)[0]
        msg['nfuStreaming'] = b[8:16].view(np.uint64)[0]
        msg['lcStreaming'] = b[16:24].view(np.uint64)[0]
        msg['cpchStreaming'] = b[24:32].view(np.uint64)[0]
        msg['busVoltageCounts'] = b[32:34].view(np.uint16)[0]
        msg['busVoltage'] = msg['busVoltageCounts'].astype(float)/148.95

        print("NFU: V = ", msg['busVoltage'], ", State = ", msg['strState'], ", CPC msgs = ", msg['numMsgs'],  ", Streaming NFU = ", msg['nfuStreaming'], ", LC = ", msg['lcStreaming'], ", CPCH = ", msg['cpchStreaming'])

        return msg

if __name__ == "__main__":
    main()
