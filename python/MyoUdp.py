# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:39:30 2016
Read Myo Armband data from UDP

@author: armigrs1
"""
import socket
import struct
import numpy
import threading
from transformations import euler_from_matrix
from transformations import quaternion_matrix
VERBOSE = 0;

class MyoUdp(object):
    def __init__(self, UDP_IP = "127.0.0.1", UDP_PORT = 10001):
        
        # Default kinematic values
        self.quat = (0.0, 0.0, 0.0, 1.0)
        self.accel = (0.0,0.0,0.0)
        self.gyro = (0.0,0.0,0.0)

        # Default data buffer
        self.data = numpy.zeros((50,8))
        
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        
        print("MyoUdp target IP:", self.UDP_IP)
        print("MyoUdp target port:", self.UDP_PORT)
        
        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP

        self.sock.bind((UDP_IP, UDP_PORT))

        
        # Create a thread for processing new data
        # Create two threads as follows
        t = threading.Thread(target=self.parseData)
        t.start()        

    def parseData(self):
        
        # Loop forever to recv data
        while True:
            # Blocking call until data received
            data,address = self.sock.recvfrom(1024)
            if len(data) == 48:
                output = struct.unpack("8b4f3f3f",data);
                self.data[:1,:] = output[0:8]
                self.data = numpy.roll(self.data,1, axis=0)
                self.quat = output[8:12]
                self.accel = output[12:14]
                self.gyro = output[15:17]
    def getData(self):
        # access the data buffer
        return self.data
       
    def getAngles(self):
        # convert the stored quaternions to angles
        return euler_from_matrix(quaternion_matrix(self.quat))

    def close(self):
        self.sock.close()
        print("Closing Socket")
