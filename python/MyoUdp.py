# -*- coding: utf-8 -*-
"""
0.0 Created on Sat Jan 23 20:39:30 2016
0.1 Edited on Sun Apr 24 2016 - improved data byte processing, created __main__
0.1.a Edited on Sat APR 30 2016 - Python 3 ready, fixed compatibility to sample_main.py
0.1.b Edited on Sun May 01 2016 - numSamples input argument added

Read Myo Armband data from UDP.  Buffer EMG Data and record the most recent IMU data.
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
import threading
import socket
import struct
import numpy
from transformations import euler_from_matrix
from transformations import quaternion_matrix
import sys
import time
import binascii

__version__ = "0.1.b"
print (sys.argv[0]  + " Version: " + __version__)

class MyoUdp(object):
    """ Class for receiving Myo Armband data via UDP"""
    def __init__(self, UDP_PORT=10001, UDP_IP="127.0.0.1", numSamples=50):

        # Default kinematic values
        self.__quat = (1.0, 0.0, 0.0, 0.0)
        self.__accel = (0.0, 0.0, 0.0)
        self.__gyro = (0.0, 0.0, 0.0)

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use getData to access since it is thread-safe
        self.dataEMG = numpy.zeros((numSamples, 8))

        # UDP Port setup
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        print("MyoUdp target IP:", self.UDP_IP)
        print("MyoUdp target port:", self.UDP_PORT)
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # Internet, UDP
        self.__sock.bind((UDP_IP, UDP_PORT))
        self.invalidDataValues = 0
        self.invalidDataLength = 0
        
        # Create threadsafe lock
        self.__lock = threading.Lock()
    
        # Create a thread for processing new data
        self.__thread = threading.Thread(target=self.parseData)
        self.__thread.start()

    def parseData(self):
        """ Convert incoming bytes to emg, quaternion, accel, and ang rate """

        # Loop forever to recv data
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
##                print('going for data')
                data, address = self.__sock.recvfrom(1024)
            except socket.error as e:
                print("Socket read error. Socket Closed?")
                print(e)
                return
                
            if len(data) == 48: #NOTE: this is true if IMU data packs as a float point type
##            if len(data) == 28: # NOTE: length==28 is true if IMU data packs as hex type
                with self.__lock:
##                with self.lock:
                    # unpack formatted data bytes
                    #  orientaiton:   int16 w, x, y, z
                    #  accelerometer: int16 +/-16 units of g
                    #  gyroscope:     int16 +/-2000 units of deg/s
##                    output = struct.unpack("8b4h3h3h", data)
                    output = struct.unpack("8b4f3f3f", data)
                    
                    # update internal variables and buffers
                    if sum(output[0:8]) == 1016:
                        #IMU Data Update
                        vectAccel=output[12:15]
                        vectGyro=output[15:18]
                        if ((abs(a)<=16 for a in vectAccel) or
                            (abs(g)<=2000 for g in vectGyro)):
                            self.__quat = output[8:12]   #[ q * 16384.0 for q in output[8:12]]
                            self.__accel = vectAccel #[ a * 2048.0 for a in vectAccel]
                            self.__gyro = vectGyro  #[ g * 16.0 for g in vectGyro]
                        else:
                            self.invalidDataValues += 1
                    elif sum(output[8:]) == 1:
                        #Populate EMG Data Buffer (newest on top)
                        self.dataEMG = numpy.roll(self.dataEMG, 1, axis=0)
                        self.dataEMG[:1, :] = output[:8] #insert in first buffer entry
                    else:
                        print('NOTE: unlikely outcome: all EMG signals at max value and all IMU is zeros')
                        self.invalidDataValues += 1
            elif len(data) == 40 or len(data) == 20: #IMU data only
                if len(data) == 40:
                    output = struct.unpack("4f3f3f", data)
                else:
                    output = struct.unpack("4h3h3h", data)
                #IMU Data Update
                vectAccel=output[4:7]
                vectGyro=output[7:12]
                if ((abs(a)<=16 for a in vectAccel) or
                    (abs(g)<=2000 for g in vectGyro)):
                    self.__quat = output[0:4]   #[ q * 16384.0 for q in output[8:12]]
                    self.__accel = vectAccel #[ a * 2048.0 for a in vectAccel]
                    self.__gyro = vectGyro  #[ g * 16.0 for g in vectGyro]
                else:
                    self.invalidDataValues += 1
            elif len(data) == 8: # EMG data only
                output = struct.unpack("8b", data)
                #Populate EMG Data Buffer (newest on top)
                self.dataEMG = numpy.roll(self.dataEMG, 1, axis=0)
                self.dataEMG[:1, :] = output[:8] #insert in first buffer entry
            else:
                # incoming data is not of length = 8, 20, 40, or 48
                self.invalidDataLength += 1



    def getData(self):
        """ Return data buffer [nSamples][nChannels] """
        with self.__lock:
            return self.dataEMG
    def getAngles(self):
        """ Return Euler angles computed from Myo quaternion """
        # convert the stored quaternions to angles
        with self.__lock:
            return euler_from_matrix(quaternion_matrix(self.__quat))
    def close(self):
        """ Cleanup socket """
        print("\n\nClosing MyoUdp Socket IP={} Port={}".format(self.UDP_IP,self.UDP_PORT) )
        self.__sock.close()
        self.__thread.join()
        print('Number of data value errors: %d' % self.invalidDataValues)
        print('Number of data length errors: %d' % self.invalidDataLength)


#%%
if __name__=='__main__':
    print (sys.argv[0]  + " Version: " + __version__)
    numMyo = int(input('How many Myo Armbands?'))
##    numMyo = 2

    # Instanciate MyoUdp Class which will begin listening for streaming UDP data
    myoReceiver1=MyoUdp(10001) # Establish myo1 UDP socket binding to port 10001
    if numMyo>1:
        myoReceiver2=MyoUdp(10002) # Establish myo2 UDP socket binding to port 10002
    

    if numMyo>1:
        print('\n---- ---- ---- ---- ---- ---- ---- ---- | ---- ---- ---- ---- ---- ---- ---- ---- | ---- ---- ---- | ---- ---- ---- x')
    else:
##        print('\n---- ---- ---- ---- ---- ---- ---- ---- |q------ ------ ------ ------ |a------ ------ ------ |g------ ------ ------ x')
        print('\n EMG: ---- ---- ---- ---- ---- ---- ---- ---- | EulerAngles: --.--- --.--- --.--- x')
    try:
        bogusResponse = input('Make sure the above line fits the console window <Press Enter to continue...>')
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
            if numMyo>1:
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
    ##    break
        pass
    print('Myo1 DataBuffer:')
    print(myoReceiver1.getData())
    if numMyo>1:
        print('Myo2 DataBuffer:')
        print(myoReceiver2.getData())
    myoReceiver1.close()
    if numMyo>1:
        myoReceiver2.close()

# TODO: Research/understand THREAD.JOIN() !!! ??????
