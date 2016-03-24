# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:39:30 2016
Read Myo Armband data from UDP

Note __variable signifies private variable

@author: R. Armiger
"""
from __future__ import with_statement # 2.5 only
import threading
import socket
import struct
import numpy
from transformations import euler_from_matrix
from transformations import quaternion_matrix
VERBOSE = 0

class MyoUdp(object):
    """ Class for receiving Myo Armband data via UDP"""
    def __init__(self, UDP_IP="127.0.0.1", UDP_PORT=10001):

        # Default kinematic values
        self.__quat = (1.0, 0.0, 0.0, 0.0)
        self.__accel = (0.0, 0.0, 0.0)
        self.__gyro = (0.0, 0.0, 0.0)

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use getData to access since it is thread-safe
        self.__data = numpy.zeros((50, 8))

        # UDP Port setup
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        print("MyoUdp target IP:", self.UDP_IP)
        print("MyoUdp target port:", self.UDP_PORT)
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # Internet, UDP
        self.__sock.bind((UDP_IP, UDP_PORT))
        
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
                data, address = self.__sock.recvfrom(1024)
            except socket.error as e:
                print("Socket read error. Socket Closed?")
                print(e)
                return
                
            if len(data) == 48:
                with self.__lock:
                    # unpack formatted data bytes
                    output = struct.unpack("8b4f3f3f", data)
                    # update internal variables and buffers
                    self.__data = numpy.roll(self.__data, 1, axis=0)
                    self.__data[:1, :] = output[0:8]
                    self.__quat = output[8:12]
                    self.__accel = output[12:14]
                    self.__gyro = output[15:17]
    def getData(self):
        """ Return data buffer [nSamples][nChannels] """
        with self.__lock:
            return self.__data
    def getAngles(self):
        """ Return Euler angles computed from Myo quaternion """
        # convert the stored quaternions to angles
        with self.__lock:
            return euler_from_matrix(quaternion_matrix(self.__quat))
    def close(self):
        """ Cleanup socket """
        print("Closing MyoUdp Socket IP={} Port={}".format(self.UDP_IP,self.UDP_PORT) )
        self.__sock.close()
        self.__thread.join()
