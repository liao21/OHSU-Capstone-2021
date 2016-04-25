# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:39:30 2016
Edited on Sun Apr 23 2016 - improved data byte processing, created __main__

Read Myo Armband data from UDP.  Buffer EMG Data and record the most recent IMU data.
If this module is executed as 'python MyoUdp.py', the output generated can
serve as a monitor of the EMG data streaming through UDP ports.

Note __variable signifies private variable  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NOT SURE WHAT THE IMPORTANCE OF HIDDEN VARIABLES IS??????

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
VERBOSE = 0

__version__ = "0.1"

class MyoUdp(object):
    """ Class for receiving Myo Armband data via UDP"""
    def __init__(self, UDP_PORT=10001, UDP_IP="127.0.0.1"):

        # Default kinematic values
        self.__quat = (1.0, 0.0, 0.0, 0.0)
        self.__accel = (0.0, 0.0, 0.0)
        self.__gyro = (0.0, 0.0, 0.0)

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use getData to access since it is thread-safe
        self.dataEMG = numpy.zeros((50, 8))

        # UDP Port setup
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        print("MyoUdp target IP:", self.UDP_IP)
        print("MyoUdp target port:", self.UDP_PORT)
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # Internet, UDP
        self.__sock.bind((UDP_IP, UDP_PORT))
        self.invalidDataValues = 0
        self.invalidDataLength = 0
        

    def parseData(self):
        """ Convert incoming bytes to emg, quaternion, accel, and ang rate """

        # Loop forever to recv data
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
##                print 'going for data'
                data, address = self.__sock.recvfrom(1024)
            except socket.error as e:
                print("Socket read error. Socket Closed?")
                print(e)
                return
                
##            if len(data) == 48: #NOTE: this is true if IMU data packs as a float point type
            if len(data) == 28: # NOTE: length==28 is true if IMU data packs as hex type
##                with self.__lock:
                with self.lock:
                    # unpack formatted data bytes
                    #  orientaiton:   int16 w, x, y, z
                    #  accelerometer: int16 +/-16 units of g
                    #  gyroscope:     int16 +/-2000 units of deg/s
                    output = struct.unpack("8b4h3h3h", data)

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
                        print 'NOTE: unlikely outcome: all EMG signals at max value and all IMU is zeros'
                        self.invalidDataValues += 1
            else:
                # incoming data is too short or too long
                self.invalidDataLength += 1



    def getData(self):
        """ Return data buffer [nSamples][nChannels] """
##        with self.__lock:
        with self.lock:
            return self.dataEMG
    def getAngles(self):
        """ Return Euler angles computed from Myo quaternion """
        # convert the stored quaternions to angles
##        with self.__lock:
        with self.lock:
            return euler_from_matrix(quaternion_matrix(self.__quat))
    def close(self):
        """ Cleanup socket """
        print("\n\nClosing MyoUdp Socket IP={} Port={}".format(self.UDP_IP,self.UDP_PORT) )
        self.__sock.close()
##        self.__thread.join()
        self.thread.join()
        print('Number of data value errors: %d' % self.invalidDataValues)
        print('Number of data length errors: %d' % self.invalidDataLength)


#%%
if __name__=='__main__':
    numMyo = int(input('How many Myo Armbands?'))
##    numMyo = 2
    myoReceiver1=MyoUdp(10001) # Establish myo1 UDP socket binding to port 10001
    if numMyo>1:
        myoReceiver2=MyoUdp(10002) # Establish myo2 UDP socket binding to port 10002
    
    # Create threadsafe lock
##    myoReceiver1.__lock = threading.Lock()
##    myoReceiver2.__lock = threading.Lock()
    myoReceiver1.lock = threading.Lock()
    if numMyo>1:
        myoReceiver2.lock = threading.Lock()
    
    # Create a thread for processing new data
##    myoReceiver1.__thread = threading.Thread(target=myoReceiver1.parseData)
##    myoReceiver2.__thread = threading.Thread(target=myoReceiver2.parseData)
##    myoReceiver1.__thread.start()
##    myoReceiver2.__thread.start()
    myoReceiver1.thread = threading.Thread(target=myoReceiver1.parseData)
    if numMyo>1:
        myoReceiver2.thread = threading.Thread(target=myoReceiver2.parseData)
    myoReceiver1.thread.start()
    if numMyo>1:
        myoReceiver2.thread.start()

    if numMyo>1:
        print '\n---- ---- ---- ---- ---- ---- ---- ---- | ---- ---- ---- ---- ---- ---- ---- ---- | ------ ------ --'
    else:
        print '\n---- ---- ---- ---- ---- ---- ---- ---- '
    try:
        bogusResponse = input('Make sure the above line fits the console window <Press Enter to continue...>')
    except SyntaxError:
        pass
    print '\n  Press <Ctrl-C> to terminate; <Ctrl-Z> to suspend (''fg'' to resume suspend)\n'

    try:
        while(True):
            time.sleep(1/300)
            a = myoReceiver1.dataEMG[:1,:]
            if numMyo>1:
                b = myoReceiver2.dataEMG[:1,:]
                sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %4d %4d %4d %4d %4d %4d %4d %4d ' %
                                 (a[0,0],a[0,1],a[0,2],a[0,3],a[0,4],a[0,5],a[0,6],a[0,7],
                                  b[0,0],b[0,1],b[0,2],b[0,3],b[0,4],b[0,5],b[0,6],b[0,7]))
                                  #b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7]))
        ##                          ,*myoReceiver1.dataEMG[:1,:], *myoReceiver2.dataEMG[:1,:]))
            else:
                sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d ' %
                                 (a[0,0],a[0,1],a[0,2],a[0,3],a[0,4],a[0,5],a[0,6],a[0,7]))
            sys.stdout.flush()

    except KeyboardInterrupt:
    ##    break
        pass
    myoReceiver1.close()
    if numMyo>1:
        myoReceiver2.close()

# TODO: Research/understand THREAD.JOIN() !!! ??????
##    myoReceiver1.__thread.join()
##    myoReceiver2.__thread.join()
