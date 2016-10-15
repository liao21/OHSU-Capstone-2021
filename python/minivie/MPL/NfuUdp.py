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
import threading
import socket
import logging
import binascii
import struct
import numpy as np
import os
import struct

# set logging to DEBUG for diagnostics/development
logging.basicConfig(level=logging.DEBUG)

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
    #time.sleep(3)

    # goto elbow bent position
    armPosition[3] = 0.3
    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
    #time.sleep(3)

    # test percept decoding
    f = open(os.path.join(os.path.dirname(__file__), "../../tests/heartbeat.bin"), "r")

    print('Testing heartbeat uint8 decoding...')
    uint8_heartbeat = np.fromfile(f, dtype=np.uint8)
    h.decode_heartbeat_msg(uint8_heartbeat)

    print('Testing heartbeat byte decoding...')
    bytes_heartbeat = uint8_heartbeat.tostring()
    h.decode_heartbeat_msg(bytes_heartbeat)

    f = open(os.path.join(os.path.dirname(__file__), "../../tests/percepts.bin"), "r")
    u = np.fromfile(f, dtype=np.uint8)

    print('Testing cpch uint8 decoding...')
    uint8_cpch = u[0:1366]
    h.decode_cpch_msg(uint8_cpch)

    print('Testing cpch byte decoding...')
    bytes_cpch = uint8_cpch.tostring()
    h.decode_cpch_msg(bytes_cpch)

    print('Testing percept uint8 decoding...')
    uint8_percept = u[1366:]
    h.decode_percept_msg(uint8_percept)

    print('Testing percept byte decoding...')
    bytes_percept = uint8_percept.tostring()
    h.decode_percept_msg(uint8_percept)

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

    def __init__(self, Hostname="192.168.1.111", UdpTelemPort=6300, UdpCommandPort=6201):
                
        self.udp = {'Hostname': Hostname,'TelemPort': UdpTelemPort, 'CommandPort': UdpCommandPort}
        self.param = {'echoHeartbeat': 1, 'echoPercepts': 1, 'echoCpch': 0}
        self.__sock = None
        self.__lock = None
        self.__thread = None
        
    def connect(self):
    
        logging.info('Setting up UDP coms on port {}. Default destination is {}:{}:'.format(\
            self.udp['TelemPort'],self.udp['Hostname'],self.udp['CommandPort']))
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.__sock.bind(('0.0.0.0', self.udp['TelemPort']))

        # Create a receive thread
        self.__thread = threading.Thread(target=self.messageHandler)

        # Create threadsafe lock
        self.__lock = threading.Lock()
    
        # wait
        time.sleep(0.5)

        # Enable Streaming
        #type = 5; NFU PERCEPTS
        msg1 = bytearray([150, 9, 1, 0, 0, 0, 0, 0, 0, 0])
        self.sendUdpCommand(msg1)
        
        # wait
        time.sleep(0.5)
        
        # Set NFU Algorithm State
        # [NfuUdp] Setting NFU parameter NFU_run_algorithm to 0
        self.sendUdpCommand(self.msgUpdateParam('NFU_run_algorithm',0))

        # wait
        time.sleep(0.5)
        
        # Set NFU output state
        #[NfuUdp] Setting NFU parameter NFU_output_to_MPL to 2
        self.sendUdpCommand(self.msgUpdateParam('NFU_output_to_MPL',2))
        
        # wait
        time.sleep(0.5)

        # Create a thread for processing new data
        self.__thread.start()
        
    def close(self):
        """ Cleanup socket """
        if self.__sock is not None:
            logging.info("Closing NfuUdp Socket IP={} Port={}".format(self.udp['Hostname'],self.udp['TelemPort']))
            self.__sock.close()

    def messageHandler(self):
        # Loop forever to recv data
        #
        # This is a thread to receive data as soon as it arrives.  
        # Note that the recvfrom() function is blocking 
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
                data, address = self.__sock.recvfrom(8192)
                
                #logging.debug('New data of length {} received'.format(len(data)))
                
            except socket.error as e:
                logging.warn("Socket read error. Socket Closed?")
                logging.warn(e)
                return
                
            if len(data) == 36: 
                with self.__lock:
                    self.decode_heartbeat_msg(data)
            elif len(data) == 2190:
                with self.__lock:
                    # cpch data bytes
                    self.decode_cpch_msg(data[:1366])
                    # percept bytes
                    self.decode_percept_msg(data[1366:])
            else:
                pass
                #logging.warn('Unhandled data received')
        

    def sendJointAngles(self,values):
        # Transmit joint angle command in radians

        # TODO: currently this is 7pos+7vel+20pos+20vel
        if len(values) == 27:
            pass
        elif len(values) == 7:
            values = values + 47 * [0.0]
        else:
            return


        logging.info('Joint Command:')
        logging.info(["{0:0.2f}".format(i) for i in values[0:27]])
        
        # TODO: TEMP fix to lock middle finger and prevent drift
        values[12] = 0.35
        values[13] = 0.35
        values[14] = 0.35    
        
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
        #logging.info('Setting up UDP coms on port {}. Default destination is {}:{}:'.format(\
        #    self.udp['TelemPort'],self.udp['Hostname'],self.udp['CommandPort']))
            
        self.__sock.sendto(msg, (self.udp['Hostname'], self.udp['CommandPort']))
    
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

    def decode_heartbeat_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B' * b.__len__(), b)
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
        
        
        if self.param['echoHeartbeat']:
            print("NFU: V = ", msg['busVoltage'], ", State = ", msg['strState'], ", CPC msgs = ", msg['numMsgs'],  ", Streaming NFU = ", msg['nfuStreaming'], ", LC = ", msg['lcStreaming'], ", CPCH = ", msg['cpchStreaming'])

        return msg

    def decode_cpch_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B' * b.__len__(), b)
            b = np.array(b, np.uint8)

        # Determine expected packet size
        numPacketHeaderBytes = 6
        numSamplesPerPacket = 20
        numSampleHeaderBytes = 4
        numChannelsPerPacket = 32
        numBytesPerChannel = 2
        numBytesPerSample = numChannelsPerPacket * numBytesPerChannel + numSampleHeaderBytes
        cpchpacketSize = numPacketHeaderBytes + numBytesPerSample * numSamplesPerPacket

        # First 6 bytes of message are global header
        data = b[numPacketHeaderBytes:cpchpacketSize].reshape(numBytesPerSample, numSamplesPerPacket, order='F')

        # First 5 bytes per sample are header
        databytes = data[numSampleHeaderBytes:, :]

        # Reshape into vector and then convert to int16
        s = databytes.reshape(1, databytes.size, order='F')[0, :].view(np.int16).reshape(numChannelsPerPacket, numSamplesPerPacket, order='F')

        sequenceNumber = data[2, :].astype('int16')
        s[-1, :] = sequenceNumber

        if self.param['echoCpch']:
            print('CPCH data {} '.format(s[17,0]) )
        
        signalDict = {'s': s, 'sequenceNumber': sequenceNumber}
        return signalDict

    def decode_percept_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        tlm = {}
        # Enable Flags
        PERCEPT_ENABLE_ACTUATED_PERCEPTS = 1
        PERCEPT_ENABLE_UNACTUATED_PERCEPTS = 2
        PERCEPT_ENABLE_INDEX_FTSN = 3
        PERCEPT_ENABLE_MIDDLE_FTSN = 4
        PERCEPT_ENABLE_RING_FTSN = 5
        PERCEPT_ENABLE_LITTLE_FTSN = 6
        PERCEPT_ENABLE_THUMB_FTSN = 7
        PERCEPT_ENABLE_CONTACT = 8
        PERCEPT_ENABLE_NUM_IDS = 8

        # Actuated
        PERCEPTID_INDEX_AB_AD = 1
        PERCEPTID_INDEX_MCP = 2
        PERCEPTID_MIDDLE_MCP = 3
        PERCEPTID_RING_MCP = 4
        PERCEPTID_LITTLE_AB_AD = 5
        PERCEPTID_LITTLE_MCP = 6
        PERCEPTID_THUMB_CMC_AD_AB = 7
        PERCEPTID_THUMB_CMC_FE = 8
        PERCEPTID_THUMB_MCP = 9
        PERCEPTID_THUMB_DIP = 10
        PERCEPT_NUM_IDS = 10

        # UnActuated
        PERCEPTID_INDEX_PIP = 1
        PERCEPTID_INDEX_DIP = 2
        PERCEPTID_MIDDLE_PIP = 3
        PERCEPTID_MIDDLE_DIP = 4
        PERCEPTID_RING_PIP = 5
        PERCEPTID_RING_DIP = 6
        PERCEPTID_LITTLE_PIP = 7
        PERCEPTID_LITTLE_DIP = 8
        UNACTUATED_PERCEPT_NUM_IDS = 8

        # FTSN
        PERCEPTID_INDEX_FTSN = 1
        PERCEPTID_MIDDLE_FTSN = 2
        PERCEPTID_RING_FTSN = 3
        PERCEPTID_LITTLE_FTSN = 4
        PERCEPTID_THUMB_FTSN = 5
        FTSN_PERCEPT_NUM_IDS = 5

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B' * b.__len__(), b)
            b = np.array(b, np.uint8)

        data_bytes = b[0:4].view(np.uint32)
        data = b[4:]

        percepts_config = np.fliplr([np.unpackbits(data[0])[8 - PERCEPT_ENABLE_NUM_IDS:]])[0]
        ftsn_config = np.fliplr([np.unpackbits(data[1])[8 - FTSN_PERCEPT_NUM_IDS:]])[0]

        index_size = data[0]

        data_index = int(2)

        tlm['Percept'] = []
        if percepts_config[PERCEPT_ENABLE_ACTUATED_PERCEPTS-1]:
            for i in np.linspace(0, PERCEPT_NUM_IDS-1, PERCEPT_NUM_IDS):
                i = int(i)
                d = {}
                posStartIdx = data_index + i*7
                d['Position'] = data[posStartIdx: posStartIdx+2].view(np.int16)[0]
                velStartIdx = data_index + 2 + i*7
                d['Velocity'] = data[velStartIdx: velStartIdx+2].view(np.int16)[0]
                torqStartIdx = data_index + 4 + i*7
                d['Torque'] = data[torqStartIdx: torqStartIdx + 2].view(np.int16)[0]
                d['Temperature'] = data[data_index + 6 + i*7]
                tlm['Percept'].append(d)

            data_index = data_index + 70

        tlm['UnactuatedPercept'] = []
        if percepts_config[PERCEPT_ENABLE_UNACTUATED_PERCEPTS-1]:
            for i in np.linspace(0, UNACTUATED_PERCEPT_NUM_IDS-1, UNACTUATED_PERCEPT_NUM_IDS):
                i = int(i)
                d = {}
                posStartIdx = data_index + i*2
                d['Position'] = data[posStartIdx: posStartIdx + 2].view(np.int16)[0]
                tlm['UnactuatedPercept'].append(d)

            data_index = data_index + 16

        tlm['FtsnPercept'] = []
        for i in np.linspace(0, FTSN_PERCEPT_NUM_IDS - 1, FTSN_PERCEPT_NUM_IDS):
            i = int(i)
            if percepts_config[i+1]:
                d = {}
                d['forceConfig'] = ftsn_config[i]

                if ftsn_config[i]: # new style
                    force = []
                    for j in np.linspace(0,13,14):
                        force.append(data[data_index])
                        data_index = data_index + 1
                    d['force'] = force

                    d['acceleration_x'] = data[data_index]
                    data_index = data_index + 1
                    d['acceleration_y'] = data[data_index]
                    data_index = data_index + 1
                    d['acceleration_z'] = data[data_index]
                    data_index = data_index + 1

                else: # old style
                    d['force_pressure'] = data[data_index: data_index + 2].view(np.int16)[0]
                    data_index = data_index + 2
                    d['force_shear'] = data[data_index: data_index + 2].view(np.int16)[0]
                    data_index = data_index + 2
                    d['force_axial'] = data[data_index: data_index + 2].view(np.int16)[0]
                    data_index = data_index + 2

                    d['acceleration_x'] = data[data_index]
                    data_index = data_index + 1
                    d['acceleration_y'] = data[data_index]
                    data_index = data_index + 1
                    d['acceleration_z'] = data[data_index]
                    data_index = data_index + 1

                tlm['FtsnPercept'].append(d)

        if percepts_config[PERCEPT_ENABLE_CONTACT-1]:
            contact_data = data[data_index:data_index+12]

            tlm['ContactSensorPercept'] = []
            d = {}

            d['index_contact_sensor'] = contact_data[0]
            d['middle_contact_sensor'] = contact_data[1]
            d['ring_contact_sensor'] = contact_data[2]
            d['little_contact_sensor'] = contact_data[3]

            d['index_abad_contact_sensor_1'] = contact_data[4]
            d['index_abad_contact_sensor_2'] = contact_data[5]

            d['little_abad_contact_sensor_1'] = contact_data[6]
            d['little_abad_contact_sensor_2'] = contact_data[7]

            tlm['ContactSensorPercept'].append(d)

        if b.__len__() > 518:
            lmc = b[-308:].reshape(44, 7, order='F')
        else:
            lmc = []

        tlm['LMC'] = lmc


        if self.param['echoPercepts']:
            torque = np.array(lmc[20:22,:]).view(dtype=np.int16)
            pos = np.array(lmc[22:24,:]).view(dtype=np.int16)
            print('LMC POS = {} LMC TORQUE = {} '.format(pos,torque))
            #print(lmc)
        return tlm

if __name__ == "__main__":
    main()
