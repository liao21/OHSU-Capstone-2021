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
import time
import socket
import logging
import binascii
import struct
import numpy as np

VERBOSE = 2

def main():
    """ 
    Run NFU interface
    """    
    # start message log
    fileName = 'OpenNFU.log'
    logPath = '.'
    # assuming loglevel is bound to the string value obtained from the
    # command line argument. Convert to upper case to allow the user to
    # specify --log=DEBUG or --log=debug
    parser = argparse.ArgumentParser(description='Main OpenNFU function')
    parser.add_argument('--log', dest='loglevel',
                        default='INFO',
                        help='Set loglevel as DEBUG INFO WARNING ERROR CRITICAL (default is INFO)')
    args = parser.parse_args()
    
    loglevel = args.loglevel
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    
    #logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(loglevel)

    fileHandler = logging.FileHandler("{0}/{1}".format(logPath, fileName))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)



    #logging.basicConfig(filename='OpenNFU.log',format='%(asctime)s:%(levelname)s:%(message)s', \
    #                    level=numeric_level, datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('-----------------------------------------------')
    logging.info('Starting OpenNFU with log level ' + loglevel)
    logging.info('-----------------------------------------------')

    # Logging info
    # Level 	When it’s used
    # ------    ---------------
    # DEBUG 	Detailed information, typically of interest only when diagnosing problems.
    # INFO 	Confirmation that things are working as expected.
    # WARNING 	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
    # ERROR 	Due to a more serious problem, the software has not been able to perform some function.
    # CRITICAL 	A serious error, indicating that the program itself may be unable to continue running.

    
    # Establish netork inferface to MPL at address below
    #h = NfuUdp(Hostname="192.168.1.111")
    h = NfuUdp(Hostname="localhost")
    
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
    logging.info('Ending OpenNFU')
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
        bval = A.tobytes()

        # format message
        msgId = 4
        msg = bytearray([msgId]) +  bytearray(paramName,'utf-8') + bytearray(128-len(paramName)) \
                        + bytearray([8, 0, 0, 0]) + bytearray(dimA) + bval[:]
        
        return msg
    
    def close(self):
        """ Cleanup socket """
        logging.info("Closing NfuUdp Socket IP={} Port={}".format(self.Hostname,self.UdpTelemPort) )
        self.__UdpSock.close()
    

if __name__ == "__main__":
    main()
