# open_nfu.py
# Interface class for the JHU/APL openNFU
#
# Interface is via UDP messages to send and receive data
#
#
#
# Revisions:
#   08SEP2017 Armiger: added limb state commands


import os
import threading
import socket
import logging
import struct
import numpy as np
import mpl
from mpl.data_sink import DataSink
from utilities import extract_percepts

SHUTDOWN_VOLTAGE = 19.0  # Critical bus voltage that will trigger immediate system shutdown


class NfuUdp(DataSink):
    """
    Python Class for NFU connections

    Hostname is the IP of the NFU
    UdpTelemPort is where percepts and EMG from NFU are received locally
    UdpCommandPort
    TcpCommandPort

    """

    def __init__(self, hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027):

        # Initialize superclass
        super(NfuUdp, self).__init__()

        self.udp = {'Hostname': hostname, 'TelemPort': udp_telem_port, 'CommandPort': udp_command_port}
        self.param = {'echoHeartbeat': 1, 'echoPercepts': 1, 'echoCpch': 1}

        # Use this parameter to prevent limb commands from being transmitted by this
        # class until valid UDP are received first.  I.e. wait for valid limb state to send data
        self.wait_for_mpl = False

        self.__sock = None

        # Create thread-safe lock
        self.__lock = threading.Lock()

        # Create a receive thread
        self.__thread = threading.Thread(target=self.message_handler)
        self.__thread.name = 'NfuUdpRcv'

        # This private variable is used to monitor data receipt from the limb.  If a timeout occurs then the parameter
        # is false until new data is received
        self.__active_connection = False

        # mpl_status updated by heartbeat messages
        self.__mpl_status_default = {
            'nfu_state': 'NULL',
            'lc_software_state': 'NULL',
            'lmc_software_state': [0,0,0,0,0,0,0],
            'bus_voltage': 0.0,
            'nfu_ms_per_CMDDOM': 0.0,
            'nfu_ms_per_ACTUATEMPL': 0.0,
        }
        self.mpl_status = self.__mpl_status_default

        # create a counter to delay how often CPU temperature is read and logged
        self.__lastTemp = 0.0
        self.__lastTempCounter = 0

    def is_alive(self):
        with self.__lock:
            val = self.__active_connection
        return val

    def get_voltage(self):
        # returns the battery voltage as a string based on the last status message
        return '{:6.2f}'.format(self.mpl_status['bus_voltage'])

    def get_temperature(self):
        # Get the processor temperature from the system
        # returns float
        # units is celsius
        #
        # Note: this function allows setting a reduced rate for how many calls are made to the system

        # Bail out if Windows
        if os.name is not 'posix':
            return 0.0

        # set a rate reduction factor to decrease calls to system process
        decimate_rate = 10

        if self.__lastTempCounter == 0:
            # Read the temperature
            try:
                with open('/sys/class/thermal/thermal_zone0/temp','r') as f:
                    contents = f.read()
                temp = float(contents) / 1000.0
                logging.info('CPU Temp: ' + str(temp))
            except FileNotFoundError:
                logging.warning('Failed to get system processor temperature')
                temp = 0.0
            self.__lastTemp = temp
        else:
            # Use the old temp
            temp = self.__lastTemp

        # increment and roll counter
        self.__lastTempCounter += 1

        if self.__lastTempCounter > decimate_rate:
            self.__lastTempCounter = 0

        return temp

    def get_status_msg(self):
        # returns a general purpose status message about the system state
        # e.g. ' 22.5V 72.6C'

        msg = u'{:4.1f}V '.format(self.mpl_status['bus_voltage'])
        msg += u'{:3.0f}\u00b0C '.format(self.get_temperature())
        msg += '<br>NFU:{} '.format(self.mpl_status['nfu_state'])
        msg += '<br>LC:{} '.format(self.mpl_status['lc_software_state'])
        msg += '<br>dt:{:.1f}ms '.format(self.mpl_status['nfu_ms_per_ACTUATEMPL'])

        return msg

    def connect(self):
        # open up the socket and bind to IP address

        # log socket creation
        logging.info('Setting up UDP comms on port {}. Default destination is {}:{}:'.format(
            self.udp['TelemPort'], self.udp['Hostname'], self.udp['CommandPort']))

        # create socket
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind to any IP address at the 'Telemetry' port (the port on which percepts are received)
        self.__sock.bind(('0.0.0.0', self.udp['TelemPort']))
        # set timeout in seconds
        self.__sock.settimeout(3.0)

        # Create a thread for processing new data
        if not self.__thread.isAlive():
            logging.warning('Starting NfuUdp rcv thread')
            self.__thread.start()

    def stop(self):
        # stop the receive thread
        self.__thread.join()

    def close(self):
        """ Cleanup socket """
        if self.__sock is not None:
            logging.info("Closing NfuUdp Socket IP={} Port={}".format(self.udp['Hostname'], self.udp['TelemPort']))
            self.__sock.close()
        self.stop()

    def message_handler(self):
        # Loop forever to receive data via UDP
        #
        # This is a thread to receive data as soon as it arrives.
        while True:
            # Blocking call until data received
            try:
                # receive call will error if socket closed externally (i.e. on exit)
                raw_chars, address = self.__sock.recvfrom(8192)  # blocks until timeout or socket closed
                data = bytearray(raw_chars)

                # if the above function returns (without error) it means we have a connection
                if not self.is_alive():
                    logging.info('MPL Connection is Active: Data received')
                    with self.__lock:
                        self.__active_connection = True

            except socket.timeout as e:
                # the data stream has stopped.  don't break the thread, just continue to wait
                msg = "NfuUdp timed out during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.udp['Hostname'], self.udp['TelemPort'], e)
                logging.warning(msg)
                with self.__lock:
                    logging.info('MPL Connection is Lost')
                    self.__active_connection = False
                    self.mpl_status = self.__mpl_status_default
                continue

            except socket.error as e:
                # The connection has been closed
                msg = "NfuUdp Socket Error during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.udp['Hostname'], self.udp['TelemPort'], e)
                logging.warning(msg)
                # break so that the thread can terminate
                break

            # Get the message ID
            if len(data) < 3:
                logging.warning('Message received was too small. Minimum message size is 3 bytes')
                continue
            else:
                msg_id = data[2]

            if msg_id == mpl.NfuUdpMsgId.UDPMSGID_HEARTBEATV2:

                # pass message bytes
                msg = decode_heartbeat_msg_v2(data[3:])
                with self.__lock:
                    self.mpl_status = msg

                logging.info(msg)

                if self.mpl_status['bus_voltage'] < SHUTDOWN_VOLTAGE:
                    # Execute limb Shutdown procedure
                    #
                    # Send a log message; set LC to soft reset; poweroff NFU
                    #
                    from utilities import shutdown

                    logging.critical('MPL bus voltage is below critical value.  Shutting down system!!!')
                    self.set_limb_soft_reset()
                    shutdown()

                if self.param['echoHeartbeat']:
                    print(msg)

            elif msg_id == mpl.NfuUdpMsgId.UDPMSGID_PERCEPTDATA:
                # Note, passing whole message to extraction function
                percepts = extract_percepts.extract(raw_chars)
                #values = np.array(percepts['jointPercepts']['torque'])
                #msg = np.array2string(values, precision=2, separator=',',max_line_width=200, prefix='Joint Percepts')
                #msg = 'Joint Percepts:' + np.array2string(values,
                #                                          formatter={'float_kind':lambda x: "%6.2f" % x},
                #                                          separator=',',
                #                                          max_line_width=200)
                #print(msg)
                #logging.debug(msg)
                pass

    def send_joint_angles(self, values):
        # Transmit joint angle command in radians
        #
        # Inputs:
        #
        # values -
        #    joint angles in radians of size 7 for arm joints
        #    joint angles in radians of size 27 for all arm joints

        if not self.is_alive():
            logging.warning('MPL Connection is closed; not sending joint angles.')
            return

        if len(values) == 7:
            # append hand angles
            # TODO: consider keeping hand in current position
            values = np.append(values, 20 * [0.0])

        # 3/24/2017 RSA: Updated angle formatting
        # 'Joint Angles: [0.00 1.20 3.14 ... ]'
        logging.info('Joint Angles: ' +
                     np.array2string(np.array(values),
                                     formatter={'float_kind': lambda x: "%.2f" % x}, max_line_width=250,
                                     suppress_small=True))

        # TEMP fix to lock middle finger and prevent drift
        # values[mpl.JointEnum.MIDDLE_MCP] = 0.35
        # values[mpl.JointEnum.MIDDLE_PIP] = 0.35
        # values[mpl.JointEnum.MIDDLE_DIP] = 0.35

        payload = np.append(values, 27 * [0.0])

        # Send data
        # size is 7 + 20 + 7 + 20
        # packing is one uint8 by 54 singles
        # total message is 221 bytes [uint16 MSD_ID_FIELD_BYTES]
        # uint16 MSG_LENGTH + uint8 MSG_TYPE + 1 msg_id + payload + checksum
        packer = struct.Struct('54f')
        msg = bytearray([219, 0, 5, 1])
        msg.extend(packer.pack(*payload))
        checksum = bytearray([sum(msg) % 256])

        # add on the checksum
        out = bytearray([])
        out.extend(msg)
        out.extend(checksum)

        self.send_udp_command(out)

    def set_limb_idle(self):
        # Send limb to idle; this is a lower power mode that still maintains position
        msg = bytearray([3, 0, 10, 10, 23])
        self.send_udp_command(msg)

    def set_limb_soft_reset(self):
        # Send limb to soft reset.  This will allow back driving joints. Active state resumes when next command received
        msg = bytearray([3, 0, 11, 11, 25])
        self.send_udp_command(msg)

    def send_udp_command(self, msg):
        # transmit packets (and optionally write to log for DEBUG)
        self.__sock.sendto(msg, (self.udp['Hostname'], self.udp['CommandPort']))

    def get_percepts(self):
        pass


def decode_heartbeat_msg_v2(msg_bytes):

    # Check if b is input as bytes, if so, convert to uint8
    if isinstance(msg_bytes, (bytes, bytearray)):
        msg_bytes = struct.unpack('B' * len(msg_bytes), msg_bytes)
        msg_bytes = np.array(msg_bytes, np.uint8)

    # REF: mpl.__init__.py for state enumerations
    # // published by openNFU (v2) at 1Hz
    # uint16_t length;                // the number of bytes excluding this field; 6 for an 8byte packet
    # uint8_t msgID;                  // should be UDPMSGID_PERCEPT_HEARTBEATV2
    #
    # uint8_t nfu_state;              // enum corresponding to BOOTSTATE of the NFU
    # uint8_t lc_software_state;      // enum corresponding to SWSTATE of the LC
    # uint8_t lmc_software_state[7];  // enum corresponding to SWSTATE of the LMCs
    # float32_t bus_voltage;          // units in Volts
    # float32_t nfu_ms_per_CMDDOM;    // average number of milliseconds between CMD_DOM issuances
    # float32_t nfu_ms_per_ACTUATEMPL;// average number of milliseconds between ACTUATE_MPL receipts
    #
    # // additional data possible
    # // messages per second
    # // flag - doubled messages per handle

    # Lookup NFU state id from the enumeration
    nfu_state_id = msg_bytes[0].view(np.uint8)
    try:
        nfu_state_str = str(mpl.BOOTSTATE(nfu_state_id)).split('.')[1]
    except ValueError:
        nfu_state_str = 'NFUSTATE_ENUM_ERROR={}'.format(nfu_state_id)

    # Lookup LC state id from the enumeration
    lc_state_id = msg_bytes[1].view(np.uint8)
    try:
        lc_state_str = str(mpl.LcSwState(lc_state_id)).split('.')[1]
    except ValueError:
        lc_state_str = 'LCSTATE_ENUM_ERROR={}'.format(nfu_state_id)

    msg = {
        'nfu_state': nfu_state_str,
        'lc_software_state': lc_state_str,
        'lmc_software_state': msg_bytes[2:9],
        'bus_voltage': msg_bytes[9:13].view(np.float32)[0],
        'nfu_ms_per_CMDDOM': msg_bytes[13:17].view(np.float32)[0],
        'nfu_ms_per_ACTUATEMPL': msg_bytes[17:21].view(np.float32)[0],
    }

    return msg
