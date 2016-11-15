# NfuUdp.py
# Interface class for RP2009 NFU board
#
# Interface is via TCP and UDP messages to instruct the NFU to set limb mode
# and begin streaming data
#
# Usage: python NfuUdp.py
# Help: python NfuUdp.py -h

import time
import threading
import socket
import logging
import binascii
import os
import struct
import numpy as np

# set logging to DEBUG for diagnostics/development
# Note this will override planned logging setting on import!!!
# logging.basicConfig(level=logging.DEBUG)


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

    def __init__(self, hostname="192.168.1.111", udp_telem_port=6300, udp_command_port=6201):

        self.udp = {'Hostname': hostname, 'TelemPort': udp_telem_port, 'CommandPort': udp_command_port}
        self.param = {'echoHeartbeat': 1, 'echoPercepts': 1, 'echoCpch': 0}
        self.__sock = None
        self.__lock = None
        self.__thread = None

    def connect(self):

        logging.info('Setting up UDP coms on port {}. Default destination is {}:{}:'.format(
            self.udp['TelemPort'], self.udp['Hostname'], self.udp['CommandPort']))
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(('0.0.0.0', self.udp['TelemPort']))
        self.__sock.settimeout(3.0)
        
        # Create a receive thread
        self.__thread = threading.Thread(target=self.message_handler)
        self.__thread.name = 'NfuUdpRcv'

        # Create threadsafe lock
        self.__lock = threading.Lock()

        # wait
        time.sleep(0.5)

        # Enable Streaming
        # type = 5 NFU PERCEPTS
        msg1 = bytearray([150, 9, 1, 0, 0, 0, 0, 0, 0, 0])
        self.send_udp_command(msg1)

        # wait
        time.sleep(0.5)

        # Set NFU Algorithm State
        # [NfuUdp] Setting NFU parameter NFU_run_algorithm to 0
        self.send_udp_command(self.msg_update_param('NFU_run_algorithm', 0))

        # wait
        time.sleep(0.5)

        # Set NFU output state
        # [NfuUdp] Setting NFU parameter NFU_output_to_MPL to 2
        self.send_udp_command(self.msg_update_param('NFU_output_to_MPL', 2))

        # wait
        time.sleep(0.5)

        # Create a thread for processing new data
        self.__thread.start()

    def close(self):
        """ Cleanup socket """
        if self.__sock is not None:
            logging.info("Closing NfuUdp Socket IP={} Port={}".format(self.udp['Hostname'], self.udp['TelemPort']))
            self.__sock.close()
        self.__thread.join()

    def message_handler(self):
        # Loop forever to recv data
        #
        # This is a thread to receive data as soon as it arrives.  
        # Note that the recvfrom() function is blocking 
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
                data, address = self.__sock.recvfrom(8192)

                # logging.debug('New data of length {} received'.format(len(data)))

            except socket.error as e:
                msg = "NfuUdp Socket Error during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.udp['Hostname'], self.udp['TelemPort'], e)
                logging.warning(msg)
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
                # logging.warning('Unhandled data received')

    def send_joint_angles(self, values):
        # Transmit joint angle command in radians
        #
        # Inputs:
        #
        # values -
        #    joint angles in radians of size 7 for arm joints
        #    joint angles in radians of size 27 for all arm joints

        if len(values) == 7:
            # append hand angles
            # TODO: consider keeping hand in current position
            values = np.append(values, 20 * [0.0])

        logging.info('Joint Command:')
        logging.info(["{0:0.2f}".format(i) for i in values[0:27]])

        # TODO: TEMP fix to lock middle finger and prevent drift
        values[12] = 0.35
        values[13] = 0.35
        values[14] = 0.35

        # msg_id = 1

        payload = np.append(values, 27 * [0.0])

        # Send data
        # size is 7 + 20 + 7 + 20
        # packing is one uint8 by 54 singles
        # total message is 221 bytes [uint16 MSD_ID_FIELD_BYTES]
        # (61) NFU ID + uint16 MSG_LENGTH + uint8 MSG_TYPE + 1 msg_id + payload + checksum
        packer = struct.Struct('54f')
        msg = bytearray([219, 0, 5, 1])
        msg.extend(packer.pack(*payload))
        checksum = bytearray([sum(msg) % 256])

        # add on the NFU routing code '61' and checksum
        out = bytearray([61])
        out.extend(msg)
        out.extend(checksum)

        self.send_udp_command(out)

    def send_udp_command(self, msg):
        # transmit packets (and optionally write to log for DEBUG)

        logging.debug('Sending "%s"' % binascii.hexlify(msg))
        # logging.info('Setting up UDP comms on port {}. Default destination is {}:{}:'.format(\
        #    self.udp['TelemPort'],self.udp['Hostname'],self.udp['CommandPort']))

        self.__sock.sendto(msg, (self.udp['Hostname'], self.udp['CommandPort']))

    def msg_update_param(self, name, value):
        # msgUpdateParam - Create encoded byte array for parameter message to OpenNFU
        #
        # Function supports a parameter name up to 127 characters and a matrix variable
        #   as a single precision floating point variable.  Matrix dimentions are calculated
        #   internally and transmited as part of message
        #
        # Translated from MATLAB to Python by David Samson on 9/23/16
        # Armiger simplified and tested 9/27/16

        logging.info('Setting parameter %s, %f', name, value)

        if len(name) > 127:
            logging.warning('msgUpdateParam:Trimming Name to max 127 characters')
            name = name[:127]

        # convert to numpy matrix        
        mat = np.matrix(value, dtype=np.dtype('<f4'))  # little-endian single-precision float

        # calculate dimensions
        dim = np.array(mat.shape, dtype=np.uint32)

        # convert to byte array
        # bytes = mat.tobytes()
        data_bytes = mat.tostring()  # compatibility alias for tobytes

        # format message
        msg_id = 4
        msg = bytearray([msg_id]) + bytearray(name, 'utf-8') + bytearray(128 - len(name)) + bytearray([8, 0, 0, 0]) + \
              bytearray(dim) + data_bytes[:]

        return msg

    def decode_heartbeat_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B' * b.__len__(), b)
            b = np.array(b, np.uint8)

        # List of software states
        nfu_states = [
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

        msg = {
            'SW_STATE': b[0:4].view(np.uint32)[0],
            'strState': '',
            'numMsgs': b[4:8].view(np.uint32)[0],
            'nfuStreaming': b[8:16].view(np.uint64)[0],
            'lcStreaming': b[16:24].view(np.uint64)[0],
            'cpchStreaming': b[24:32].view(np.uint64)[0],
            'busVoltageCounts': b[32:34].view(np.uint16)[0],
            'busVoltage': 0.0,
        }
        msg['strState'] = nfu_states[msg['SW_STATE']]
        msg['busVoltage'] = msg['busVoltageCounts'].astype(float) / 148.95

        if self.param['echoHeartbeat']:
            logging.debug('NFU: V = {:6.2f} State= {} Msgs: CPC={:4d} Stream: NFU={} LC={} CPC={}'.format(
                msg['busVoltage'], msg['strState'], msg['numMsgs'], msg['nfuStreaming'], msg['lcStreaming'],
                msg['cpchStreaming']))

        return msg

    def decode_cpch_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B' * b.__len__(), b)
            b = np.array(b, np.uint8)

        # Determine expected packet size
        num_packet_header_bytes = 6
        num_samples_per_packet = 20
        num_sample_header_bytes = 4
        num_channels_per_packet = 32
        num_bytes_per_channel = 2
        num_bytes_per_sample = num_channels_per_packet * num_bytes_per_channel + num_sample_header_bytes
        cpch_packet_size = num_packet_header_bytes + num_bytes_per_sample * num_samples_per_packet

        # First 6 bytes of message are global header
        data = b[num_packet_header_bytes:cpch_packet_size].reshape(
            num_bytes_per_sample, num_samples_per_packet, order='F')

        # First 5 bytes per sample are header
        data_bytes = data[num_sample_header_bytes:, :]

        # Reshape into vector and then convert to int16
        s = data_bytes.reshape(1, data_bytes.size, order='F')[0, :].view(np.int16).reshape(
            num_channels_per_packet, num_samples_per_packet, order='F')

        sequence_number = data[2, :].astype('int16')
        s[-1, :] = sequence_number

        if self.param['echoCpch']:
            logging.debug('CPCH data {} '.format(s[17, 0]))

        signal_dict = {'s': s, 'sequence_number': sequence_number}
        return signal_dict

    def decode_percept_msg(self, b):
        # Log: Translated to Python by COP on 12OCT2016

        tlm = {}
        # Enable Flags
        percept_enable_actuated_percepts = 1
        percept_enable_unactuated_percepts = 2
        # percept_enable_index_ftsn = 3
        # percept_enable_middle_ftsn = 4
        # percept_enable_ring_ftsn = 5
        # percept_enable_little_ftsn = 6
        # percept_enable_thumb_ftsn = 7
        percept_enable_contact = 8
        percept_enable_num_ids = 8

        # Actuated
        # perceptid_index_ab_ad = 1
        # perceptid_index_mcp = 2
        # perceptid_middle_mcp = 3
        # perceptid_ring_mcp = 4
        # perceptid_little_ab_ad = 5
        # perceptid_little_mcp = 6
        # perceptid_thumb_cmc_ad_ab = 7
        # perceptid_thumb_cmc_fe = 8
        # perceptid_thumb_mcp = 9
        # perceptid_thumb_dip = 10
        percept_num_ids = 10

        # UnActuated
        # perceptid_index_pip = 1
        # perceptid_index_dip = 2
        # perceptid_middle_pip = 3
        # perceptid_middle_dip = 4
        # perceptid_ring_pip = 5
        # perceptid_ring_dip = 6
        # perceptid_little_pip = 7
        # perceptid_little_dip = 8
        unactuated_percept_num_ids = 8

        # FTSN
        # perceptid_index_ftsn = 1
        # perceptid_middle_ftsn = 2
        # perceptid_ring_ftsn = 3
        # perceptid_little_ftsn = 4
        # perceptid_thumb_ftsn = 5
        ftsn_percept_num_ids = 5

        # Check if b is input as bytes, if so, convert to uint8
        if isinstance(b, (bytes, bytearray)):
            b = struct.unpack('B' * b.__len__(), b)
            b = np.array(b, np.uint8)

        data = b[4:]
        # data_bytes = b[0:4].view(np.uint32)

        percepts_config = np.fliplr([np.unpackbits(data[0])[8 - percept_enable_num_ids:]])[0]
        ftsn_config = np.fliplr([np.unpackbits(data[1])[8 - ftsn_percept_num_ids:]])[0]

        # index_size = data[0]

        data_index = int(2)

        tlm['Percept'] = []
        if percepts_config[percept_enable_actuated_percepts - 1]:
            for i in np.linspace(0, percept_num_ids - 1, percept_num_ids):
                i = int(i)
                d = {}
                pos_start_idx = data_index + i * 7
                d['Position'] = data[pos_start_idx: pos_start_idx + 2].view(np.int16)[0]
                vel_start_idx = data_index + 2 + i * 7
                d['Velocity'] = data[vel_start_idx: vel_start_idx + 2].view(np.int16)[0]
                torq_start_idx = data_index + 4 + i * 7
                d['Torque'] = data[torq_start_idx: torq_start_idx + 2].view(np.int16)[0]
                d['Temperature'] = data[data_index + 6 + i * 7]
                tlm['Percept'].append(d)

            data_index += 70

        tlm['UnactuatedPercept'] = []
        if percepts_config[percept_enable_unactuated_percepts - 1]:
            for i in np.linspace(0, unactuated_percept_num_ids - 1, unactuated_percept_num_ids):
                i = int(i)
                d = {}
                pos_start_idx = data_index + i * 2
                d['Position'] = data[pos_start_idx: pos_start_idx + 2].view(np.int16)[0]
                tlm['UnactuatedPercept'].append(d)

            data_index += 16

        tlm['FtsnPercept'] = []
        for i in np.linspace(0, ftsn_percept_num_ids - 1, ftsn_percept_num_ids):
            i = int(i)
            if percepts_config[i + 1]:
                d = {'forceConfig': ftsn_config[i]}

                if ftsn_config[i]:  # new style
                    force = []
                    for j in np.linspace(0, 13, 14):
                        force.append(data[data_index])
                        data_index += 1
                    d['force'] = force

                    d['acceleration_x'] = data[data_index]
                    data_index += 1
                    d['acceleration_y'] = data[data_index]
                    data_index += 1
                    d['acceleration_z'] = data[data_index]
                    data_index += 1

                else:  # old style
                    d['force_pressure'] = data[data_index: data_index + 2].view(np.int16)[0]
                    data_index += 2
                    d['force_shear'] = data[data_index: data_index + 2].view(np.int16)[0]
                    data_index += 2
                    d['force_axial'] = data[data_index: data_index + 2].view(np.int16)[0]
                    data_index += 2

                    d['acceleration_x'] = data[data_index]
                    data_index += 1
                    d['acceleration_y'] = data[data_index]
                    data_index += 1
                    d['acceleration_z'] = data[data_index]
                    data_index += 1

                tlm['FtsnPercept'].append(d)

        if percepts_config[percept_enable_contact - 1]:
            contact_data = data[data_index:data_index + 12]

            tlm['ContactSensorPercept'] = []
            d = {'index_contact_sensor': contact_data[0], 'middle_contact_sensor': contact_data[1],
                 'ring_contact_sensor': contact_data[2], 'little_contact_sensor': contact_data[3],
                 'index_abad_contact_sensor_1': contact_data[4], 'index_abad_contact_sensor_2': contact_data[5],
                 'little_abad_contact_sensor_1': contact_data[6], 'little_abad_contact_sensor_2': contact_data[7]}

            tlm['ContactSensorPercept'].append(d)

        if b.__len__() > 518:
            lmc = b[-308:].reshape(44, 7, order='F')
        else:
            lmc = []

        tlm['LMC'] = lmc

        if self.param['echoPercepts']:
            torque = np.array(lmc[20:22, :]).view(dtype=np.int16)
            pos = np.array(lmc[22:24, :]).view(dtype=np.int16)
            logging.debug('LMC POS = {} LMC TORQUE = {} '.format(pos, torque))
        return tlm


def main():
    """ 
    Run NFU interface as standalone test function
    """

    # Establish network inferface to MPL at address below
    # h = NfuUdp(Hostname="192.168.1.111")
    h = NfuUdp(hostname="localhost")
    h.connect()

    # Run a quick motion test to verify joints are working
    num_arm_joints = 7
    num_hand_joints = 20
    arm_position = [0.0] * num_arm_joints
    hand_position = [0.0] * num_hand_joints

    # goto zero position
    h.send_joint_angles(arm_position + hand_position)
    # time.sleep(3)

    # goto elbow bent position
    arm_position[3] = 0.3
    h.send_joint_angles(arm_position + hand_position)
    # time.sleep(3)

    # test percept decoding
    f = open(os.path.join(os.path.dirname(__file__), "../../tests/heartbeat.bin"), "r")

    print('Testing heartbeat uint8 decoding...')
    heartbeat = np.fromfile(f, dtype=np.uint8)
    h.decode_heartbeat_msg(heartbeat)

    print('Testing heartbeat byte decoding...')
    bytes_heartbeat = heartbeat.tostring()
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
    h.decode_percept_msg(bytes_percept)

    h.close()
    logging.info('Ending NfuUdp')
    logging.info('-----------------------------------------------')


if __name__ == "__main__":
    main()