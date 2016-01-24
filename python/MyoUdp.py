# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:39:30 2016

@author: armigrs1
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

import socket
import struct
import numpy
from transformations import euler_from_matrix
from transformations import quaternion_matrix
VERBOSE = 1;

class MyoUdp(object):
    def __init__(self, UDP_IP = "127.0.0.1", UDP_PORT = 10001):
        
        self.quat = (1.0, 0.0, 0.0, 0.0)
        self.accel = (0.0,0.0,0.0)
        self.gyro = (0.0,0.0,0.0)
        
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        
        print("MyoUdp target IP:", self.UDP_IP)
        print("MyoUdp target port:", self.UDP_PORT)
        
        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP

        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)

        self.emg_buffer = numpy.zeros((100,8))
    def getData(self):
        data =''
        address = ''
        try:
            data,address = self.sock.recvfrom(1024)
            output = struct.unpack("8b4f3f3f",data);
            self.emg_buffer[:1,:] = output[0:8]
            self.emg_buffer = numpy.roll(self.emg_buffer,1, axis=0)
            self.quat = output[8:12]
            print(self.getAngles)            
            
            
            self.accel = output[12:14]
            self.gyro = output[15:17]
        except socket.error:
            pass
        
    def getAngles(self):
        # convert the stored quaternions to angles
        return euler_from_matrix(quaternion_matrix(self.quat))

    def close(self):
        self.sock.close()
        print("Closing Socket")
