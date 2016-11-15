"""
Handle UDP communications to Unity vMPL Environment

On construction, this class creates a communication port with the following
optional input arguments:

Inputs: 
    UDP_IP - string of IP address of destination (running Unity) default = "127.0.0.1"
    UDP_PORT - integer port number for unity communications default= 25000

Methods:
    sendJointAngles - accept a 7 element or 27 element array of joint angles in radians 
        and transmit to Unity environment
        
TODO: Presently this is only one-way communication.  Receive sensor data


Created on Sat Jan 23 20:36:50 2016

@author: R. Armiger
"""
#TODO: Presently this is only one-way communication.  Receive sensor data

import socket
import binascii
import struct
import logging

VERBOSE = 1


class UnityUdp(object):
    def __init__(self, ip="127.0.0.1", port=25000):
        self.UDP_IP = ip
        self.UDP_PORT = port

        logging.info("UnityUdp target IP: {}".format(self.UDP_IP))
        logging.info("UnityUdp target port: {}".format(self.UDP_PORT))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    def connect(self):
        pass

    def send_joint_angles(self, values):

        if len(values) == 27:
            pass
        elif len(values) == 7:
            values = values + 20 * [0.0]
        else:
            logging.info('Invalid command size for send_joint_angles(): len=' + str(len(values)))
            return

        # Send data
        logging.debug('Joint Command:')
        logging.debug(["{0:0.2f}".format(i) for i in values[0:27]])
        packer = struct.Struct('27f')
        packed_data = packer.pack(*values)
        self.sock.sendto(packed_data, (self.UDP_IP, self.UDP_PORT))

    def close(self):
        self.sock.close()
        logging.info("Closing UnityUdp Socket IP={} Port={}".format(self.UDP_IP, self.UDP_PORT))