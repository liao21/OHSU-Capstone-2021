#!/usr/bin/python
"""
0.0 Created on Sat Jan 23 20:39:30 2016
0.1 Edited on Sun Apr 24 2016 - improved data byte processing, created __main__
0.1.a Edited on Sat APR 30 2016 - Python 3 ready, fixed compatibility to sample_main.py
0.1.b Edited on Sun May 01 2016 - numSamples input argument added
0.1.c Edited on Sun May 19 2016 - fixed stream receive for EMG Data Only: 16 bytes, not 8
0.1.c Edited on 7/20/2016 - RSA: fixed processing using MyoUdp.exe (Windows)
1.0.0 RSA: Added emulator, test code and verified function with linux and windows
2.0.0 RSA: Added myo transmission code to this as a single file

Read Myo Armband data.  Buffer EMG Data and record the most recent IMU data.
If this module is executed as ' $ python MyoUdp.py', the output generated can
serve as a monitor of the EMG data streaming through UDP ports.

Selecting 1 Myo will display streaming EMG and IMU data
Selecting 2 Myos will display streaming EMG1 and EMG2 data (no IMU data)

Note __variable signifies private variable which are acccessible to getData and getAngles.
A call to the class methods (getData, getAngles) allow external modules to read streaming data
that is buffered in the private variables.

@author: R. Armiger
contributor: W. Haris
"""

from __future__ import with_statement  # 2.5 only
import os
import threading
import socket
import struct
import numpy as np
import subprocess
import logging
import time

from transforms3d.euler import quat2euler

# The following is only supported under linux (transmit mode)
if os.name is 'posix':
    from bluepy.btle import DefaultDelegate as btleDefaultDelegate
    from bluepy.btle import BTLEException as btleBTLEException
    from bluepy.btle import Peripheral as btlePeripheral
    from bluepy.btle import ADDR_TYPE_PUBLIC as btleADDR_TYPE_PUBLIC
else:
    # override this bluepy object type (non-functionally) so that module can load on windows
    btleDefaultDelegate = object

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
if os.path.split(os.getcwd())[1] == 'inputs':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
import inputs
import utilities

__version__ = "2.0.0"

# Scaling constants for MYO IMU Data
MYOHW_ORIENTATION_SCALE = 16384.0
MYOHW_ACCELEROMETER_SCALE = 2048.0
MYOHW_GYROSCOPE_SCALE = 16.0


def emulate_myo_udp_exe(destination='//127.0.0.1:10001'):
    """
    Emulate MyoUdp.exe outputs for testing

    Example Usage within python:
        import os
        os.chdir(r"C:\git\minivie\python\minivie")
        import Inputs.MyoUdp
        Inputs.MyoUdp.EmulateMyoUdpExe() # CTRL+C to END

    Example Usage from command prompt:
        python Myo.py -SIMEXE

    MyoUdp.exe Data packet information:
    Data packet size is 48 bytes.
         uchar values encoding:
         Bytes 0-7: int8 [8] emgSamples
         Bytes 8-23: float [4]  quaternion (rotation)
         Bytes 24-35: float [3] accelerometer data, in units of g
         Bytes 36-47: float [3] gyroscope data, in units of deg / s

    Revisions:
        2016OCT23 Armiger: Created
        2016OCT24 Armiger: changed randint behavior for python 27 compatibility

    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    print('Running MyoUdp.exe Emulator to ' + destination)
    try:
        while True:
            # generate random bytes matching the size of MyoUdp.exe streaming
            # Future: generate orientation data in valid range

            # dtyp of randint is invalid in numpt 1.8, python 2.7:
            # data = np.random.randint(255, size=48, dtype='i1')
            # TypeError: randint() got an unexpected keyword argument 'dtype'

            data = np.random.randint(255, size=48).astype('int8')
            sock.sendto(data.tostring(), utilities.get_address(destination))
            time.sleep(0.005)  # 200Hz
    except KeyError:
        pass
    print('Closing MyoUdp.exe Emulator')
    sock.close()


def emulate_myo_unix(destination='//127.0.0.1:15001'):
    """
    Emulate Myo UNIX streaming outputs for testing

    Example Usage within python:
        import os
        os.chdir(r"C:\git\minivie\python\minivie")
        import Inputs.MyoUdp
        Inputs.MyoUdp.EmulateMyoUnix() # CTRL+C to END

    Example Usage from command prompt:
        python Myo.py -SIM_UNIX

    Revisions:
        2016OCT23 Armiger: Created
        2016OCT24 Armiger: changed randint behavior for python 27 compatibility

    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    print('Running MyoUdp.exe Emulator to ' + destination)
    try:
        while True:
            # generate random bytes matching the size of MyoUdp.exe streaming
            # Future: generate orientation data in valid range
            vals = np.random.randint(255, size=16).astype('uint8')
            sock.sendto(vals.tostring(), utilities.get_address(destination))
            time.sleep(0.005)  # 200Hz
            vals = np.random.randint(255, size=16).astype('uint8')
            sock.sendto(vals.tostring(), utilities.get_address(destination))

            # create synthetic orientation data
            # rpy = np.random.rand(90, size=3)
            # rpy = [30.0, 45.0, 15.0]
            # q = [1.0, 0.0, 0.0, 0.0] * MYOHW_ORIENTATION_SCALE

            # np.array(q, dtype=int16).tostring

            vals = np.random.randint(255, size=20).astype('uint8')
            sock.sendto(vals.tostring(), utilities.get_address(destination))
            time.sleep(0.005)  # 200Hz

    except KeyError:
        pass
    print('Closing Myo Emulator')
    sock.close()


class MyoUdp(object):
    """

        Class for receiving Myo Armband data via UDP

        Handles streaming data from MyoUdp.Exe OR streaming data from unix based streaming

        Note the use of __private variable and threading / locks to ensure data is read safely

    """

    def __init__(self, source='//127.0.0.1:10001', num_samples=50):

        # logging
        self.log_handlers = None

        # 8 channel max for myo armband
        self.__num_channels = 8

        # Default kinematic values
        self.__quat = (1.0, 0.0, 0.0, 0.0)
        self.__accel = (0.0, 0.0, 0.0)
        self.__gyro = (0.0, 0.0, 0.0)

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use getData to access since it is thread-safe
        self.__dataEMG = np.zeros((num_samples, 8))

        # UDP Port setup
        self.addr = utilities.get_address(source)

        # Initialize connection parameters
        self.__sock = None
        self.__lock = None
        self.__thread = None

    def connect(self):

        logging.info("Setting up MyoUdp socket {}".format(self.addr))
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP
        self.__sock.bind(self.addr)
        self.__sock.settimeout(3.0)

        # Create threadsafe lock so that user based reading of values and thread-based
        # writing of values do not conflict
        self.__lock = threading.Lock()

        # Create a thread for processing new incoming data
        self.__thread = threading.Thread(target=self.read_packet)
        self.__thread.name = 'MyoUdpRcv'
        self.__thread.start()

    def read_packet(self):
        """ Convert incoming bytes to emg, quaternion, accel, and ang rate """

        # Loop forever to receive data
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
                data, address = self.__sock.recvfrom(1024)
            except socket.error as e:
                msg = "MyoUdp Socket Error during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.addr[0], self.addr[1], e)
                logging.warning(msg)
                return

            if len(data) == 48:  # NOTE: This is the packet size for MyoUdp.exe
                # -------------------------------
                # Handles data from MyoUdp.exe
                # -------------------------------
                with self.__lock:
                    # unpack formatted data bytes
                    # Note: these have been scaled in MyoUdp from the raw hardware values
                    output = struct.unpack("8b4f3f3f", data)

                    if self.log_handlers is not None:
                        self.log_handlers(output[0:8])

                    # Populate EMG Data Buffer (newest on top)
                    self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                    self.__dataEMG[:1, :] = output[:8]  # insert in first buffer entry

                    # IMU Data Update
                    self.__quat = output[8:12]
                    self.__accel = output[12:15]
                    self.__gyro = output[15:18]

            elif len(data) == 16:  # EMG data only
                # -------------------------------------
                # Handles data from unix direct stream
                # -------------------------------------

                #    Myo UNIX  Data packet information:
                #    Data packet size either 16 or 20 bytes.
                #        <case> 16
                #            # EMG Samples (8 channels 2 samples per packet)
                #            d = double(typecast(bytes,'int8'))
                #            emgData = reshape(d,8,2)
                #        <case> 20
                #            # IMU sample
                #            MYOHW_ORIENTATION_SCALE = 16384.0
                #            MYOHW_ACCELEROMETER_SCALE = 2048.0
                #            MYOHW_GYROSCOPE_SCALE = 16.0
                #            dataInt16 = double(typecast(bytes,'int16'))
                #            orientation = dataInt16(1:4) ./ MYOHW_ORIENTATION_SCALE
                #            accelerometer = dataInt16(5:7) ./ MYOHW_ACCELEROMETER_SCALE
                #            gyroscope = dataInt16(8:10) ./ MYOHW_GYROSCOPE_SCALE
                with self.__lock:
                    # print(['{}'.format(i) for i in data])
                    output = struct.unpack('16b', data)
                    # Populate EMG Data Buffer (newest on top)
                    self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                    self.__dataEMG[:1, :] = output[0:8]  # insert in first buffer entry
                    self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                    self.__dataEMG[:1, :] = output[8:16]  # insert in first buffer entry

            elif len(data) == 20:  # IMU data only
                with self.__lock:
                    # create array of 10 int16
                    output = struct.unpack('10h', data)
                    unscaled = np.array(output, dtype=np.int16)

                    self.__quat = np.array(unscaled[0:4], np.float) / MYOHW_ORIENTATION_SCALE
                    self.__accel = np.array(unscaled[4:7], np.float) / MYOHW_ACCELEROMETER_SCALE
                    self.__gyro = np.array(unscaled[7:10], np.float) / MYOHW_GYROSCOPE_SCALE

                    # print(self.__quat)

            else:
                # incoming data is not of length = 8, 20, 40, or 48
                logging.warning('MyoUdp: Unexpected packet size. len=({})'.format(len(data)))

    def get_data(self):
        """ Return data buffer [nSamples][nChannels] """
        with self.__lock:
            return self.__dataEMG

    def get_angles(self):
        """ Return Euler angles computed from Myo quaternion """
        # convert the stored quaternions to angles
        with self.__lock:
            return quat2euler(self.__quat)

    def close(self):
        """ Cleanup socket """
        logging.info("\n\nClosing MyoUdp Socket @ {}".format(self.addr))
        if self.__sock is not None:
            self.__sock.close()
        if self.__thread is not None:
            self.__thread.join()


class MyoDelegate(btleDefaultDelegate):
    """
    Callback function for handling incoming data from bluetooth connection

    """
    # TODO: Currently this only supports udp streaming.  consider internal buffer for udp-free mode (local)

    def __init__(self, myo, sock, addr):
        self.myo = myo
        self.sock = sock
        self.addr = addr
        self.pCount = 0
        self.imuCount = 0
        self.battCount = 0

    def handleNotification(self, cHandle, data):
        if cHandle == 0x2b:  # EmgData0Characteristic
            self.sock.sendto(data, self.addr)
            # logging.info('EMG: ' + data)
            self.pCount += 2
        elif cHandle == 0x2e:  # EmgData1Characteristic
            self.sock.sendto(data, self.addr)
            self.pCount += 2
        elif cHandle == 0x31:  # EmgData2Characteristic
            self.sock.sendto(data, self.addr)
            self.pCount += 2
        elif cHandle == 0x34:  # EmgData3Characteristic
            self.sock.sendto(data, self.addr)
            self.pCount += 2
        elif cHandle == 0x1c:  # IMUCharacteristic
            self.sock.sendto(data, self.addr)
            # logging.info('IMU: ' + data)
            self.imuCount += 1
        elif cHandle == 0x11:  # BatteryCharacteristic
            self.sock.sendto(data, self.addr)
            logging.info('Battery Level: {}'.format(ord(data)))
            self.battCount += 1
        else:
            logging.info('Got Unknown Notification: %d' % cHandle)

        return


def set_parameters(p):
    """function parameters"""
    # Notifications are unacknowledged, while indications are acknowledged. Notifications are therefore faster,
    # but less reliable.
    # Indication = 0x02; Notification = 0x01

    # Setup main streaming:
    p.writeCharacteristic(0x12, struct.pack('<bb', 1, 0), 1)  # Un/subscribe from battery_level notifications
    p.writeCharacteristic(0x24, struct.pack('<bb', 0, 0), 1)  # Un/subscribe from classifier indications
    p.writeCharacteristic(0x1d, struct.pack('<bb', 1, 0), 1)  # Subscribe from imu notifications
    p.writeCharacteristic(0x2c, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data0 notifications
    p.writeCharacteristic(0x2f, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data1 notifications
    p.writeCharacteristic(0x32, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data2 notifications
    p.writeCharacteristic(0x35, struct.pack('<bb', 1, 0), 1)  # Subscribe to emg data3 notifications

    # note: Default values indicated by [] below:
    # [1]Should be for Classifier modes (00,01)
    # [1]Should be for IMU modes (00,01,02,03,04,05)
    # [1]Should be for EMG modes (00,02,03) **?can use value=1,4,5?
    # [2]Should be for payload size 03
    # [1]Should be for command 01
    # 200Hz (default) streaming
    p.writeCharacteristic(0x19, struct.pack('<bbbbb', 1, 3, 3, 1, 0), 1)  # Tell the myo we want EMG, IMU

    # Custom Streaming
    # Tell the myo we want EMG@300Hz, IMU@50Hz
    # p.writeCharacteristic(0x19, struct.pack('<bbbbbhbbhb',2,0xa,3,1,0,0x12c,0,0,0x32,0x62), 1)

    # turn off sleep
    p.writeCharacteristic(0x19, struct.pack('<bbb', 9, 1, 1), 1)

    return


def connect(mac_addr, stream_addr, hci_interface):
    logging.info("Connecting to: " + mac_addr)
    p = btlePeripheral(mac_addr, addrType=btleADDR_TYPE_PUBLIC, iface=hci_interface)
    logging.info("Done")

    logging.info("Setting Update Rate")
    cmd = "sudo hcitool -i hci%d cmd 0x08 0x0013 40 00 06 00 06 00 00 00 90 01 00 00 07 00" % hci_interface
    logging.info(cmd)
    subprocess.Popen(cmd, shell=True).wait()
    logging.info("Done")

    set_parameters(p)

    # Setup Socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Assign event handler
    h_delegate = MyoDelegate(p, s, stream_addr)
    p.withDelegate(h_delegate)

    t_start = time.time()

    while True:
        try:
            t_now = time.time()
            t_elapsed = t_now - t_start
            p.waitForNotifications(1.0)
            if t_elapsed > 2.0:
                rate1 = h_delegate.pCount / t_elapsed
                rate2 = h_delegate.imuCount / t_elapsed
                logging.info("Port: %d EMG: %4.1f Hz IMU: %4.1f Hz BattEvts: %d" % (
                    stream_addr[1], rate1, rate2, h_delegate.battCount))
                t_start = t_now
                h_delegate.pCount = 0
                h_delegate.imuCount = 0
        except:
            logging.info('Caught error. Closing UDP Connection')
            s.close()
            raise


def manage_connection(mac_addr='C3:0A:EA:14:14:D9', stream_addr=('127.0.0.1', 15001), hci_interface=0):

    while True:

        logging.debug('Running subprocess command: hcitool dev')
        hci = 'hci' + str(hci_interface)
        
        if hci in subprocess.check_output(["hcitool", "dev"]):
            logging.info('Found device: ' + hci)
            device_ok = True
        else:
            logging.info('Device not found: ' + hci)
            device_ok = False

        while device_ok:
            try:
                logging.info('Starting connection to ' + hci)
                connect(mac_addr, stream_addr, hci_interface)
            except KeyboardInterrupt:
                logging.info('Got Keyboard Interrupt')
                break
            except btleBTLEException:
                logging.info('Device Disconnected')
                break

        time.sleep(1.0)

    logging.info('Done')


def interactive_startup():
    num_myo = int(input('How many Myo Armbands?'))

    # Instantiate MyoUdp Class which will begin listening for streaming UDP data
    myo_receiver1 = MyoUdp('//127.0.0.1:15001')  # Establish myo1 UDP socket binding to port 10001
    if num_myo > 1:
        myo_receiver2 = MyoUdp('//127.0.0.1:15002')  # Establish myo2 UDP socket binding to port 10002

    if num_myo > 1:
        print(
            '\n' + '---- ' * 8 + '| ' + '---- ' * 8 + '| ' + '---- ' * 3 + '| ' + '---- ' * 3 + 'x')
    else:
        print('\n EMG: ---- ---- ---- ---- ---- ---- ---- ---- | EulerAngles: --.--- --.--- --.--- x')
    try:
        input('Make sure the above line fits the console window <Press Enter to continue...>')
    except SyntaxError:
        pass
    print('\n  Press <Ctrl-C> to terminate <Ctrl-Z> to suspend ' +
          '\n                             resume job in suspend: >fg ' +
          '\n                          terminate job in suspend: >kill $(jobs -p) sleep 3s kill -9 $(jobs -p)\n\n')

    # Forever loop to get streaming data
    try:
        while True:
            time.sleep(1 / 300)
            a = myo_receiver1.get_data()[:1, :]
            g1, g2, g3 = myo_receiver1.get_angles()
            if num_myo > 1:
                b = myo_receiver2.get_data()[:1, :]
                h1, h2, h3 = myo_receiver2.get_angles()
                # TODO: Interactive Myo Formatting needs updating
                # sys.stdout.write(
                #     '\r' + '%4d '*8 + '|' + '%4d '*8 + '| %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f' %
                #     (a[0, 0], a[0, 1], a[0, 2], a[0, 3], a[0, 4], a[0, 5], a[0, 6], a[0, 7],
                #      b[0, 0], b[0, 1], b[0, 2], b[0, 3], b[0, 4], b[0, 5], b[0, 6], b[0, 7],
                #      g1, g2, g3,
                #      h1, h2, h3))
            else:
                sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %5.2f %5.2f %5.2f' %
                                 (a[0, 0], a[0, 1], a[0, 2], a[0, 3], a[0, 4], a[0, 5], a[0, 6], a[0, 7],
                                  g1, g2, g3))
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    print('Myo1 DataBuffer:')
    print(myo_receiver1.get_data())
    if num_myo > 1:
        print('Myo2 DataBuffer:')
        print(myo_receiver2.get_data())
    myo_receiver1.close()
    if num_myo > 1:
        myo_receiver2.close()


def main():
    """Parse command line arguments into argparse model.
    
    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.
    
    """
    import sys
    import argparse

    # Parameters:
    parser = argparse.ArgumentParser(description='MyoUdp: Read from myo and stream UDP.')
    parser.add_argument('-e', '--SIM_EXE', help='Run MyoUdp.exe EMG Simulator', action='store_true')
    parser.add_argument('-u', '--SIM_UNIX', help='Run UNIX EMG Simulator', action='store_true')
    parser.add_argument('-rx', '--RX_MODE', help='set Myo to receive mode', action='store_true')
    parser.add_argument('-tx', '--TX_MODE', help='set Myo to transmit mode', action='store_true')
    parser.add_argument('-i', '--IFACE', help='hciX interface', default=0, type=int)
    parser.add_argument('-m', '--MAC', help='Myo MAC address', default='C3:0A:EA:14:14:D9', )
    parser.add_argument('-a', '--ADDRESS', help=r'Destination Address (e.g. //127.0.0.1:15001)',
                        default='//127.0.0.1:15001')
    args = parser.parse_args()

    if args.SIM_EXE:
        emulate_myo_udp_exe(args.ADDRESS)
    elif args.SIM_UNIX:
        emulate_myo_unix(args.ADDRESS)
    elif args.RX_MODE:
        h = MyoUdp(args.ADDRESS)
        l = inputs.DataLogger()
        h.log_handlers = l.add_sample
        h.connect()
    elif args.TX_MODE:
        f = 'hci' + str(args.IFACE) + '_myo.log'
        logging.basicConfig(filename=f, level=logging.DEBUG, format='%(asctime)s %(message)s')
        manage_connection(args.MAC, utilities.get_address(args.ADDRESS), args.IFACE)
    else:
        # No Action
        print(sys.argv[0] + " Version: " + __version__)

    logging.info(sys.argv[0] + " Version: " + __version__)

if __name__ == '__main__':
    main()