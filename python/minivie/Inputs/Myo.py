# -*- coding: utf-8 -*-
"""
0.0 Created on Sat Jan 23 20:39:30 2016
0.1 Edited on Sun Apr 24 2016 - improved data byte processing, created __main__
0.1.a Edited on Sat APR 30 2016 - Python 3 ready, fixed compatibility to sample_main.py
0.1.b Edited on Sun May 01 2016 - numSamples input argument added
0.1.c Edited on Sun May 19 2016 - fixed stream receive for EMG Data Only: 16 bytes, not 8
0.1.c Edited on 7/20/2016 - RSA: fixed processing using MyoUdp.exe (Windows)
1.0.0 RSA: Added emulator, test code and verified function with linux and windows

Read Myo Armband data.  Buffer EMG Data and record the most recent IMU data.
If this module is executed as ' $ python MyoUdp.py', the output generated can
serve as a monitor of the EMG data streaming through UDP ports.

Selecting 1 Myo will display streaming EMG and IMU data
Selecting 2 Myos will display streaming EMG1 and EMG2 data (no IMU data)

Note __variable signifies private variable; which are acccessible to getData and getAngles.
A call to the class methods (getData, getAngles) allow external modules to read streaming data
that is buffered in the private variables.

@author: R. Armiger
contributor: W. Haris
"""

from __future__ import with_statement # 2.5 only
import os
import argparse
import threading
import socket
import struct
import sys
import time
import logging
import binascii
import numpy as np
import six
from types import *
if os.path.split(os.getcwd())[1] == 'Inputs' :
    # Ensure base folder (python/minvie) is on path for imports
    sys.path.insert(0, os.path.abspath('..'))
import Utilities
from Utilities import transformations 

__version__ = "1.0.0"

# Scaling constants for MYO IMU Data
MYOHW_ORIENTATION_SCALE = 16384.0;
MYOHW_ACCELEROMETER_SCALE = 2048.0;
MYOHW_GYROSCOPE_SCALE = 16.0;

def EmulateMyoUdpExe(destination='//127.0.0.1:10001'):
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
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    
    print('Running MyoUdp.exe Emulator to ' + destination)
    try:
        while (1):
            # generate random bytes matching the size of MyoUdp.exe streaming
            # Future: generate orientation data in valid range
            vals = np.random.randint(255, size=48, dtype='uint8')
            #print(vals)
            sock.sendto(vals.tostring(), Utilities.getAddress(destination) )
            time.sleep(0.005) # 200Hz
    except:
        pass
    print('Closing MyoUdp.exe Emulator')
    sock.close()

def EmulateMyoUnix(destination='//127.0.0.1:15001'):
    """
    Emulate Myo UNIX streaming outputs for testing

    Example Usage within python:
        import os
        os.chdir(r"C:\git\minivie\python\minivie")
        import Inputs.MyoUdp
        Inputs.MyoUdp.EmulateMyoUnix() # CTRL+C to END

    Example Usage from command prompt:
        python Myo.py -SIMUNIX
        
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    
    print('Running MyoUdp.exe Emulator to ' + destination)
    try:
        while (1):
            # generate random bytes matching the size of MyoUdp.exe streaming
            # Future: generate orientation data in valid range
            vals = np.random.randint(255, size=16, dtype='uint8')
            sock.sendto(vals.tostring(), Utilities.getAddress(destination) )
            time.sleep(0.005) # 200Hz
            vals = np.random.randint(255, size=16, dtype='uint8')
            sock.sendto(vals.tostring(), Utilities.getAddress(destination) )
            
            # create synthetic orientation data
            #rpy = np.random.rand(90, size=3)
            #rpy = [30.0, 45.0, 15.0]
            #q = [1.0, 0.0, 0.0, 0.0] * MYOHW_ORIENTATION_SCALE
            
            #np.array(q, dtype=int16).tostring
            
            vals = np.random.randint(255, size=20, dtype='uint8')
            sock.sendto(vals.tostring(), Utilities.getAddress(destination) )
            time.sleep(0.005) # 200Hz
            
    except:
        pass
    print('Closing Myo Emulator')
    sock.close()
    
class MyoUdp(object):
    """ 
    
        Class for receiving Myo Armband data via UDP
        
        Handles streaming data from MyoUdp.Exe OR streaming data from unix based streaming
        
        Note the use of __private variable and threading / locks to ensure data is read safely
    
    """
    def __init__(self, source='//127.0.0.1:10001', numSamples=50):

        # Default kinematic values
        self.__quat = (1.0, 0.0, 0.0, 0.0)
        self.__accel = (0.0, 0.0, 0.0)
        self.__gyro = (0.0, 0.0, 0.0)

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use getData to access since it is thread-safe
        self.__dataEMG = np.zeros((numSamples, 8))

        # UDP Port setup
        self.addr = Utilities.getAddress(source);
        logging.info( "Setting up MyoUdp socket {}".format(self.addr) )
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # Internet, UDP
        self.__sock.bind(self.addr)
        
        # Create threadsafe lock so that user based reading of values and thread-based
        # writing of values don;t conflict
        self.__lock = threading.Lock()
    
        # Create a thread for processing new incoming data
        self.__thread = threading.Thread(target=self.readPacket)
        self.__thread.name = 'MyoUdpRcv'
        self.__thread.start()

    def readPacket(self):
        """ Convert incoming bytes to emg, quaternion, accel, and ang rate """

        # Loop forever to recv data
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
                data, address = self.__sock.recvfrom(1024)
            except socket.error as e:
                print("Socket read error. Socket Closed?")
                print(e)
                return
                
            if len(data) == 48: #NOTE: This is the packet size for MyoUdp.exe
            # -------------------------------
            # Handles data from MyoUdp.exe
            # -------------------------------
                with self.__lock:
                    # unpack formatted data bytes
                    # Note: these have been scaled in MyoUdp from the raw hardware values
                    output = struct.unpack("8b4f3f3f", data)

                    #Populate EMG Data Buffer (newest on top)
                    self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                    self.__dataEMG[:1, :] = output[:8] #insert in first buffer entry

                    #IMU Data Update
                    self.__quat = output[8:12]
                    self.__accel = output[12:15]
                    self.__gyro = output[15:18]  

            elif len(data) == 16: # EMG data only
            # -------------------------------------
            # Handles data from unix direct stream
            # -------------------------------------
            
            #    Myo UNIX  Data packet information:
            #    Data packet size either 16 or 20 bytes.
            #        <case> 16
            #            # EMG Samples (8 channels 2 samples per packet)
            #            d = double(typecast(bytes,'int8'));
            #            emgData = reshape(d,8,2);
            #        <case> 20
            #            # IMU sample
            #            MYOHW_ORIENTATION_SCALE = 16384.0;
            #            MYOHW_ACCELEROMETER_SCALE = 2048.0;
            #            MYOHW_GYROSCOPE_SCALE = 16.0;
            #            dataInt16 = double(typecast(bytes,'int16'));
            #            orientation = dataInt16(1:4) ./ MYOHW_ORIENTATION_SCALE;
            #            accelerometer = dataInt16(5:7) ./ MYOHW_ACCELEROMETER_SCALE;
            #            gyroscope = dataInt16(8:10) ./ MYOHW_GYROSCOPE_SCALE;
                with self.__lock:
                    #print(['{}'.format(i) for i in data])
                    output = struct.unpack('16b',data)
                    # Populate EMG Data Buffer (newest on top)
                    self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                    self.__dataEMG[:1, :] = output[0:8] #insert in first buffer entry
                    self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                    self.__dataEMG[:1, :] = output[8:16] #insert in first buffer entry

            elif len(data) == 20: #IMU data only
                with self.__lock:
                    # create array of 10 int16
                    output = struct.unpack('10h',data)
                    unscaled = np.array(output, dtype=np.int16)
                    
                    self.__quat = np.array(unscaled[0:4], np.float) / MYOHW_ORIENTATION_SCALE
                    self.__accel = np.array(unscaled[4:7], np.float) / MYOHW_ACCELEROMETER_SCALE
                    self.__gyro = np.array(unscaled[7:10], np.float) / MYOHW_GYROSCOPE_SCALE

                    print(self.__quat)
                    
            else:
                # incoming data is not of length = 8, 20, 40, or 48
                logging.warn('MyoUdp: Unexpected packet size. len=({})'.format(len(data)))

    def getData(self):
        """ Return data buffer [nSamples][nChannels] """
        with self.__lock:
            return self.__dataEMG
    def getAngles(self):
        """ Return Euler angles computed from Myo quaternion """
        # convert the stored quaternions to angles
        with self.__lock:
            return transformations.euler_from_matrix(transformations.quaternion_matrix(self.__quat))
    def close(self):
        """ Cleanup socket """
        logging.info("\n\nClosing MyoUdp Socket @ {}".format(self.addr) )
        self.__sock.close()
        self.__thread.join()

def interactiveStartup():

    numMyo = int(input('How many Myo Armbands?'))

    # Instantiate MyoUdp Class which will begin listening for streaming UDP data
    myoReceiver1=MyoUdp('//127.0.0.1:15001') # Establish myo1 UDP socket binding to port 10001
    if numMyo > 1:
        myoReceiver2=MyoUdp('//127.0.0.1:15002') # Establish myo2 UDP socket binding to port 10002
    

    if numMyo > 1:
        print('\n---- ---- ---- ---- ---- ---- ---- ---- | ---- ---- ---- ---- ---- ---- ---- ---- | ---- ---- ---- | ---- ---- ---- x')
    else:
        print('\n EMG: ---- ---- ---- ---- ---- ---- ---- ---- | EulerAngles: --.--- --.--- --.--- x')
    try:
        input('Make sure the above line fits the console window <Press Enter to continue...>')
    except SyntaxError:
        pass
    print('\n  Press <Ctrl-C> to terminate; <Ctrl-Z> to suspend ' +
          '\n                             resume job in suspend: >fg ' +
          '\n                          terminate job in suspend: >kill $(jobs -p); sleep 3s; kill -9 $(jobs -p)\n\n')

    # Forever loop to get streaming data
    try:
        while(True):
            time.sleep(1/300)
            a = myoReceiver1.getData()[:1,:]
            g1,g2,g3 = myoReceiver1.getAngles()
            if numMyo > 1:
                b = myoReceiver2.getData()[:1,:]
                h1,h2,h3 = myoReceiver2.getAngles()
                sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %4d %4d %4d %4d %4d %4d %4d %4d | %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f' %
                                 (a[0,0],a[0,1],a[0,2],a[0,3],a[0,4],a[0,5],a[0,6],a[0,7],
                                  b[0,0],b[0,1],b[0,2],b[0,3],b[0,4],b[0,5],b[0,6],b[0,7],
                                  g1,g2,g3,
                                  h1,h2,h3))
            else:
                sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %5.2f %5.2f %5.2f' %
                                 (a[0,0],a[0,1],a[0,2],a[0,3],a[0,4],a[0,5],a[0,6],a[0,7],
                                  g1,g2,g3))
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    print('Myo1 DataBuffer:')
    print(myoReceiver1.getData())
    if numMyo > 1:
        print('Myo2 DataBuffer:')
        print(myoReceiver2.getData())
    myoReceiver1.close()
    if numMyo>1:
        myoReceiver2.close()

def main() :
    """Parse command line arguments into argparse model.
    
    Command-line arguments:
    -h or --help -- ouput help text describing command-line arguments.
    
    """
    
    # Parameters:
    parser = argparse.ArgumentParser(description='MyoUdp: Read from myo and stream UDP.')
    parser.add_argument('-e', '--SIMEXE',   help='Run MyoUdp.exe EMG Simulator', action='store_true')
    parser.add_argument('-u', '--SIMUNIX',  help='Run UNIX EMG Simulator', action='store_true')
    parser.add_argument('-rx', '--RXMODE',  help='set Myo to receive mode',action='store_true')
    parser.add_argument('-tx', '--TXMODE',  help='set Myo to transmit mode',action='store_true')
    parser.add_argument('-m', '--MAC',      help='Myo MAC address', default='D4:5F:B3:52:6C:25',)
    parser.add_argument('-a', '--ADDR',     help=r'Destination Address (e.g. //127.0.0.1:15001)', default='//127.0.0.1:15001')
    parser.add_argument('-i', '--IFACE',    help='hciX interface',default=0, type=int)
    args = parser.parse_args()

    print (sys.argv[0]  + " Version: " + __version__)
    
    if args.SIMEXE :
        EmulateMyoUdpExe(args.ADDR)
    elif args.SIMUNIX :
        EmulateMyoUnix(args.ADDR)
    elif args.RXMODE :
        MyoUdp(args.ADDR)

if __name__=='__main__':
    main()

