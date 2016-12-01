"""
Handle UDP communications to Unity vMPL Environment

On construction, this class creates a communication port with the following
optional input arguments:

JHUAPL vMPL Unity Communications Info:
    Data should be sent in little endian format.

    Message               Transmission Type	Source	Target	Port
    Left vMPL Command             Broadcast	VULCANX	vMPLEnv	25100
    Right vMPL Command            Broadcast	VULCANX	vMPLEnv	25000
    Left vMPL Percepts            Broadcast	vMPLEnv	VULCANX	25101
    Right vMPL Percepts           Broadcast	vMPLEnv	VULCANX	25001
    Left Virtual Hand Command     Broadcast	VULCANX	vMPLEnv	25300
    Right Virtual Hand Command	  Broadcast	VULCANX	vMPLEnv	25200
    Left Virtual Hand Percepts	  Broadcast	vMPLEnv	VULCANX	25301
    Right Virtual Hand Percepts	  Broadcast	vMPLEnv	VULCANX	25201

Inputs: 
    UDP_IP - string of IP address of destination (running Unity) default = "127.0.0.1"
    UDP_PORT - integer port number for unity communications default= 25000

Methods:
    sendJointAngles - accept a 7 element or 27 element array of joint angles in radians 
        and transmit to Unity environment
        
Example:
    (Requires a JHUAPL vMPL arm in Unity virtual environment)
    from the python console, in the git/minivie/python/minivie directory:

    >>> from mpl.unity import UnityUdp
    >>> sink = UnityUdp()
    >>> sink.send_joint_angles([0.2,0.2,0.2,0.2,0.2,0.2,0.2])

    Verify that the right virtual arm moves in Unity
    Next add a left arm controller:

    >>> sink2 = UnityUdp(port=25100)
    >>> sink2.send_joint_angles([0.2,0.2,0.2,0.9,0.2,0.2,0.2])

    Verify that the left virtual arm moves in Unity

TODO: Presently this is only one-way communication.  Receive sensor data


Created on Sat Jan 23 20:36:50 2016

@author: R. Armiger
"""
#TODO: Presently this is only one-way communication.  Receive sensor data

import socket
import binascii
import struct
import logging


class UnityUdp(object):
    def __init__(self, ip="127.0.0.1", port=25000):
        self.UDP_IP = ip
        self.UDP_PORT = port

        logging.info("UnityUdp target IP: {}".format(self.UDP_IP))
        logging.info("UnityUdp target port: {}".format(self.UDP_PORT))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    def connect(self):
        pass

    def get_voltage(self):
        return 'vMPL'        
        
    def send_joint_angles(self, values):

        if len(values) == 27:
            pass
        elif len(values) == 7:
            # Only upper arm angles passed.  Use zeros for hand angles
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
