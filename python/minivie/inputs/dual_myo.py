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

from bluepy.btle import DefaultDelegate as btleDefaultDelegate
from bluepy.btle import BTLEException as btleBTLEException
from bluepy.btle import Peripheral as btlePeripheral
from bluepy.btle import ADDR_TYPE_PUBLIC as btleADDR_TYPE_PUBLIC

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
if os.path.split(os.getcwd())[1] == 'inputs':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
import inputs
import utilities

__version__ = "2.0.0"

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
    #p.writeCharacteristic(0x19, struct.pack('<bbbbb', 1, 3, 3, 1, 0), 1)  # Tell the myo we want EMG, IMU

    # Custom Streaming
    # Tell the myo we want EMG@300Hz, IMU@50Hz
    p.writeCharacteristic(0x19, struct.pack('<bbbbbhbbhb',2,0xa,3,1,0,0x12c,0,0,0x32,0x62), 1)

    # turn off sleep
    p.writeCharacteristic(0x19, struct.pack('<bbb', 9, 1, 1), 1)

    return


def main():

    mac1 = 'D8:53:80:BA:2E:BE'
    mac2 = 'E8:A2:46:0B:2C:49'

    print("Connecting to: " + mac1)
    p1 = btlePeripheral(mac1, addrType=btleADDR_TYPE_PUBLIC, iface=0)
    print("Done")

    print("Setting Update Rate")
    cmd = "sudo hcitool -i hci%d cmd 0x08 0x0013 40 00 06 00 06 00 00 00 90 01 00 00 07 00" % 0
    print(cmd)
    subprocess.Popen(cmd, shell=True).wait()
    print("Done")

    set_parameters(p1)

    print("Connecting to: " + mac2)
    p2 = btlePeripheral(mac2, addrType=btleADDR_TYPE_PUBLIC, iface=0)
    print("Done")

    print("Setting Update Rate")
    cmd = "sudo hcitool -i hci%d cmd 0x08 0x0013 41 00 06 00 06 00 00 00 90 01 00 00 07 00" % 0
    print(cmd)
    subprocess.Popen(cmd, shell=True).wait()
    print("Done")

    set_parameters(p2)
    print("Done with parmeters")

    # Setup Socket
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    stream_addr1 = ('127.0.0.1', 15001)
    stream_addr2 = ('127.0.0.1', 15002)

    # Assign event handler
    h_delegate1 = MyoDelegate(p1, s1, stream_addr1)
    p1.withDelegate(h_delegate1)

    h_delegate2 = MyoDelegate(p2, s2, stream_addr2)
    p2.withDelegate(h_delegate2)

    t_start = time.time()

    while True:
        try:
            t_now = time.time()
            t_elapsed = t_now - t_start
            p1.waitForNotifications(1.0)
            p2.waitForNotifications(1.0)
            if t_elapsed > 2.0:
                emgRate1 = h_delegate1.pCount / t_elapsed
                imuRate1 = h_delegate1.imuCount / t_elapsed
                emgRate2 = h_delegate2.pCount / t_elapsed
                imuRate2 = h_delegate2.imuCount / t_elapsed
                print("Port: %d EMG: %4.1f Hz IMU: %4.1f Hz BattEvts: %d Port: %d EMG: %4.1f Hz IMU: %4.1f Hz BattEvts: %d" % (
                    stream_addr1[1], emgRate1, imuRate1, h_delegate1.battCount, stream_addr2[1], emgRate2, imuRate2, h_delegate2.battCount))
                t_start = t_now
                h_delegate1.pCount = 0
                h_delegate1.imuCount = 0
                h_delegate2.pCount = 0
                h_delegate2.imuCount = 0
        except:
            print('Caught error. Closing UDP Connection')
            s1.close()
            s2.close()
            raise



if __name__ == '__main__':
    main()
