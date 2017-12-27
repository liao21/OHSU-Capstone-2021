#!/usr/bin/env python3
#
# This function is a linux based module for establishing myo armband streaming as a server via UDP
# This relies on the bluepy module for linux
#
#
import os
import logging
import time
import socket
import struct
import binascii
from bluepy import btle

# Ensure that the project modules can be found on path allowing execution from the 'inputs' folder
if os.path.split(os.getcwd())[1] == 'inputs':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from utilities import user_config as uc
from utilities import get_address

logger = logging.getLogger(__name__)

__version__ = "1.0.0"


class MyoUdpServer(object):

    def __init__(self, iface=0, mac_address='xx:xx:xx:xx:xx:xx',
                 local_port=('localhost', 16001),
                 remote_port=('localhost', 15001),
                 data_logger=logger,
                 name='Myo'):
        import threading
        import subprocess

        # Process input arguments
        self.iface = iface
        self.mac_address = mac_address.upper()  # note this needs to be upper when finding handle to peripheral
        self.local_port = local_port
        self.remote_port = remote_port

        # Create data object handles
        self.peripheral = None
        self.sock = None
        send_udp = lambda data: self.sock.sendto(data, self.remote_port)
        self.delegate = MyoDelegate(send_udp, data_logger)
        self.thread = threading.Thread(target=self.run)
        self.thread.name = name

        self.logger = data_logger
        self.logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(
            'EMG_MAC_{}_PORT_{}.log'.format(self.mac_address.replace(':', ''), self.remote_port[1]))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(created)f %(message)s'))
        self.logger.addHandler(file_handler)

        self.logger.debug('Running subprocess command: hcitool dev')
        hci = 'hci' + str(iface)

        output = subprocess.check_output(["hcitool", "dev"])
        if hci in output.decode('utf-8'):
            self.logger.info('Found device: ' + hci)
        else:
            self.logger.info('Device not found: ' + hci)

    def set_device_parameters(self):
        """function parameters"""
        # Notifications are unacknowledged, while indications are acknowledged. Notifications are therefore faster,
        # but less reliable.
        # Indication = 0x02; Notification = 0x01
        import struct

        write = self.peripheral.writeCharacteristic

        # Setup main streaming:
        write(0x12, struct.pack('<bb', 1, 0), 1)  # Un/subscribe from battery_level notifications
        write(0x24, struct.pack('<bb', 0, 0), 1)  # Un/subscribe from classifier indications
        write(0x1d, struct.pack('<bb', 1, 0), 1)  # Subscribe from imu notifications
        write(0x2c, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data0 notifications
        write(0x2f, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data1 notifications
        write(0x32, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data2 notifications
        write(0x35, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data3 notifications

        # note: Default values indicated by [] below:
        # [1]Should be for Classifier modes (00,01)
        # [1]Should be for IMU modes (00,01,02,03,04,05)
        # [1]Should be for EMG modes (00,02,03) **?can use value=1,4,5?
        # [2]Should be for payload size 03
        # [1]Should be for command 01
        # 200Hz (default) streaming
        write(0x19, struct.pack('<bbbbb', 1, 3, 3, 1, 0), 1)  # Tell the myo we want EMG, IMU

        # Custom Streaming
        # Tell the myo we want EMG@300Hz, IMU@50Hz
        # write(0x19, struct.pack('<bbbbbhbbhb',2,0xa,3,1,0,0x12c,0,0,0x32,0x62), 1)

        # turn off sleep
        write(0x19, struct.pack('<bbb', 9, 1, 1), 1)

    def set_host_parameters(self):
        """
            Set parameters on the host adapter to allow low-latency streaming

            The command sets the Preferred Peripheral Connection Parameters (PPCP).  You can find summary Bluetooth
            information here: https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.
                characteristic.gap.peripheral_preferred_connection_parameters.xml

            Breaking down the command "sudo hcitool cmd 0x08 0x0013 40 00 06 00 06 00 00 00 90 01 00 00 07 00"

            the syntax for the 'cmd' option in 'hcitool' is:
                hcitool cmd <ogf> <ocf> [parameters]

                OGF: 0x08 "7.8 LE Controller Commands"

                OCF: 0x0013 "7.8.18 LE Connection Update Command"

            The significant command parameter bytes are "06 00 06 00 00 00 90 01" (0x0006, 0x0006, 0x0000, 0x0190)

            These translate to setting the min, and max Connection Interval to 0x0006=6;6*1.25ms=7.5ms, with no slave
                latency, and a 0x0190=400; 400*10ms=4s timeout.
            UPDATE: Added non-zero slave latency for robustness on DART board

            For more info, you can search for the OGF, OCF sections listed above in the Bluetooth Core 4.2 spec

        """
        import subprocess

        # get the connection information
        conn_raw = subprocess.check_output(['hcitool', 'con'])

        # parse to get our connection handle
        conn_lines = conn_raw.decode('utf-8').split('\n')

        handle_hex = None
        for conn in conn_lines:
            if conn.find(self.mac_address) > 0:
                start = 'handle'
                end = 'state'
                handle = int(conn.split(start)[1].split(end)[0])
                handle_hex = '{:04x}'.format(handle)
                self.logger.info('MAC: {} is handle {}'.format(self.mac_address, handle))

        if handle_hex is None:
            logging.error('Connection not found while setting adapter rate')

        cmd_str = "hcitool -i hci{} cmd 0x08 0x0013 {} {} 06 00 06 00 00 00 90 01 01 00 07 00".format(
            self.iface, handle_hex[2:], handle_hex[:2])
        self.logger.info("Setting host adapter update rate: " + cmd_str)
        subprocess.Popen(cmd_str, shell=True)

    def set_udp_parameters(self, source_address, destination_address):

        pass

    def run(self):

        # connect bluetooth
        self.logger.info("Connecting to: " + self.mac_address)

        # This blocks until device is awake and connection established
        self.peripheral = btle.Peripheral(None, addrType=btle.ADDR_TYPE_PUBLIC, iface=self.iface)
        self.peripheral.connect(self.mac_address)

        self.set_host_parameters()
        self.set_device_parameters()

        # connect udp
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.sock.bind(self.local_port)

        # Assign event handler
        self.peripheral.withDelegate(self.delegate)

        # start run loop
        status_msg_rate = 2.0  # seconds
        t_start = time.time()

        while True:
            t_now = time.time()
            t_elapsed = t_now - t_start

            #  waitForNotifications(timeout) Blocks until a notification is received from the peripheral
            # or until the given timeout (in seconds) has elapsed
            if not self.peripheral.waitForNotifications(1.0):
                self.logger.warning('Missed Myo notification.')

            if t_elapsed > status_msg_rate:
                rate1 = self.delegate.counter['emg'] / t_elapsed
                rate2 = self.delegate.counter['imu'] / t_elapsed
                status = "MAC: %s Port: %d EMG: %4.1f Hz IMU: %4.1f Hz BattEvts: %d" % (
                    self.mac_address, self.remote_port[1], rate1, rate2, self.delegate.counter['battery'])
                self.logger.info(status)

                # reset timer and rate counters
                t_start = t_now
                self.delegate.counter['emg'] = 0
                self.delegate.counter['imu'] = 0

            # Check for receive messages
            # Send a single byte for vibration command with duration of 0-3 seconds
            # s.sendto(bytearray([2]),('localhost',16001))
            try:
                data, address = self.sock.recvfrom(1024)
                print(data)
                length = ord(data)
                if 0 <= length <= 3:
                    self.peripheral.writeCharacteristic(0x19, struct.pack('<bbb', 0x03, 0x01, length), True)
            except BlockingIOError:
                pass

    def close(self):
        self.sock.close()


class MyoDelegate(btle.DefaultDelegate):
    """
    Callback function for handling incoming data from bluetooth connection

    """
    # TODO: Currently this only supports udp streaming.  consider internal buffer for udp-free mode (local)

    def __init__(self, send_udp, raw_logger=logger):
        self.send_udp = send_udp
        self.counter = {'emg': 0, 'imu': 0, 'battery': 0}
        self.logger = raw_logger
        super(MyoDelegate, self).__init__()

    def handleNotification(self, cHandle, data):
        if cHandle == 0x2b:  # EmgData0Characteristic
            self.send_udp(data)
            self.logger.debug('E0: ' + binascii.hexlify(data).decode('utf-8'))
            self.counter['emg'] += 2
        elif cHandle == 0x2e:  # EmgData1Characteristic
            self.send_udp(data)
            self.logger.debug('E1: ' + binascii.hexlify(data).decode('utf-8'))
            self.counter['emg'] += 2
        elif cHandle == 0x31:  # EmgData2Characteristic
            self.send_udp(data)
            self.logger.debug('E2: ' + binascii.hexlify(data).decode('utf-8'))
            self.counter['emg'] += 2
        elif cHandle == 0x34:  # EmgData3Characteristic
            self.send_udp(data)
            self.logger.debug('E3: ' + binascii.hexlify(data).decode('utf-8'))
            self.counter['emg'] += 2
        elif cHandle == 0x1c:  # IMUCharacteristic
            self.send_udp(data)
            self.logger.debug('IMU: ' + binascii.hexlify(data).decode('utf-8'))
            self.counter['imu'] += 1
        elif cHandle == 0x11:  # BatteryCharacteristic
            self.send_udp(data)
            self.logger.info('Battery Level: {}'.format(ord(data)))
            self.counter['battery'] += 1
        else:
            self.logger.warning('Got Unknown Notification: %d' % cHandle)

        return


def run_threads():

    # get parameters from xml files and create Servers
    s1 = MyoUdpServer(iface=0,
                      mac_address=uc.get_user_config_var('myo_mac_address_1', 'xx:xx:xx:xx:xx'),
                      local_port=get_address(uc.get_user_config_var('myo_local_port_1', '//127.0.0.1:16001')),
                      remote_port=get_address(uc.get_user_config_var('myo_remote_port_1', '//127.0.0.1:15001')),
                      data_logger=logging.getLogger('Myo1'),
                      name='Myo1')

    s2 = MyoUdpServer(iface=0,
                      mac_address=uc.get_user_config_var('myo_mac_address_2', 'xx:xx:xx:xx:xx'),
                      local_port=get_address(uc.get_user_config_var('myo_local_port_2', '//127.0.0.1:16002')),
                      remote_port=get_address(uc.get_user_config_var('myo_remote_port_2', '//127.0.0.1:15002')),
                      data_logger=logging.getLogger('Myo2'),
                      name='Myo2')

    # go live with connections
    s1.thread.start()
    time.sleep(0.1)
    s2.thread.start()


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import sys
    import argparse

    # Parameters:
    parser = argparse.ArgumentParser(description='myo_server: read bluetooth packets from myo and stream to UDP.')
    parser.add_argument('-x', '--XML', help=r'XML Parameter File (e.g. user_config.xml)',
                        default=None)
    args = parser.parse_args()

    if args.XML is not None:
        uc.read_user_config(file=args.XML)
        run_threads()
    else:
        # No Action
        print(sys.argv[0] + " Version: " + __version__)

    logger.info(sys.argv[0] + " Version: " + __version__)


if __name__ == '__main__':
    main()
