# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:36:50 2016

@author: R. Armiger
"""
# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

import socket
import binascii
import struct
   
VERBOSE = 1;
   
class UnityUdp(object):
    def __init__(self, UDP_IP = "127.0.0.1", UDP_PORT = 25000):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        
        print("UnityUdp target IP:", self.UDP_IP)
        print("UnityUdp target port:", self.UDP_PORT)

        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
                             
    def sendJointAngles(self,values):
        
        # Send data
        packer = struct.Struct('27f')
        packed_data = packer.pack(*values)
        if VERBOSE > 1:
            print('Sending "%s"' % binascii.hexlify(packed_data), values)
        self.sock.sendto(packed_data, (self.UDP_IP, self.UDP_PORT))
    
    def close(self):
        self.sock.close()
        print("Closing Socket")
