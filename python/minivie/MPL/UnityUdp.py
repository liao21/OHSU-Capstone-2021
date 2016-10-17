# -*- coding: utf-8 -*-
"""
Handle UDP communucations to Unity vMPL Environment

On construction, this class creates a communication port with the following
optional input arguments:

Inputs: 
    UDP_IP - string of IP address of destination (running Unity) default = "127.0.0.1"
    UDP_PORT - integer port number for unity communications; default= 25000

Methods:
    sendJointAngles - accept a 7 element or 27 element array of joint angles in radians 
        and transmit to Unity environment
        
TODO: Presently this is only one-way communication.  Receive sensor data


Created on Sat Jan 23 20:36:50 2016

@author: R. Armiger
"""
# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

import socket
import binascii
import struct
import logging
   
VERBOSE = 1;
   
class UnityUdp(object):
    def __init__(self, UDP_IP = "127.0.0.1", UDP_PORT = 25000):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        
        logging.info("UnityUdp target IP:", self.UDP_IP)
        logging.info("UnityUdp target port:", self.UDP_PORT)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        
    def connect(self):
        pass
        
    def sendJointAngles(self,values):
        
        if len(values) == 27:
            pass
        elif len(values) == 7:
            values = values + 20 * [0.0]
        else:
            return
            
        # Send data
        packer = struct.Struct('27f')
        packed_data = packer.pack(*values)
        logging.debug('Sending "%s"' % binascii.hexlify(packed_data), values)
        self.sock.sendto(packed_data, (self.UDP_IP, self.UDP_PORT))
    
    def close(self):
        self.sock.close()
        logging.info("Closing UnityUdp Socket IP={} Port={}".format(self.UDP_IP,self.UDP_PORT) )
