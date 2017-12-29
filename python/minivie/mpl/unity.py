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
    >>> sink.connect()
    >>> sink.send_joint_angles([0.2,0.2,0.2,0.2,0.2,0.2,0.2])

    Verify that the right virtual arm moves in Unity
    Next add a left arm controller:

    >>> sink2 = UnityUdp(port=25100)
    >>> sink2.connect()
    >>> sink2.send_joint_angles([0.2,0.2,0.2,0.9,0.2,0.2,0.2])

    Verify that the left virtual arm moves in Unity

Notes:
    for debug use:
    import logging
    logging.basicConfig(level=logging.DEBUG)

Created on Sat Jan 23 20:36:50 2016

@author: R. Armiger
"""

import socket
import struct
import logging
import numpy as np
import threading
import mpl
from mpl.data_sink import DataSink
from utilities import Udp


def get_percepts(data):
    """
    Get sensor data from vMPL (returns tuple)

    :return:

        joint_data - [27x3] matrix of position velocity and torque for each joint
        contact_data - Contact pad data
        segment_data - FTSN Data (old/new)

    """
    joint_data = None
    contact_data = None
    segment_data = None

    # Convert raw bytes

    # Upper Arm Joints = 7 Joints * 3 values per joint * 4 bytes per value = 84 bytes)... bytes 0-84
    # Fingers and Thumb = 20 Joints * 3 values per joint * 4 bytes per value = 240 bytes)... bytes 85-324
    if len(data) >= 324:
        joint_data = np.frombuffer(data[0:324], np.float32, mpl.JointEnum.NUM_JOINTS * 3)

    # ContactPerceptsType   74 (37 values (2 bytes each), so (2x37) enum for each of potential contact sensors)
    # FtsnForcePerceptsType 60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60))
    # FtsnAccelPerceptsType 60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60))
    # FtsnTempPerceptsType  20 (1 x 32-bit value (1 x 4 bytes) for each of 5 fingers, so (1x4x5 = 20))
    if len(data) >= 398:
        contact_data = np.frombuffer(data[324:398], np.short, 37)

    # Segment forces (OLD) = 5 sensors * 3 axes/values per sensor * 4 bytes per value = 60 bytes)... bytes 399-458
    # Segment forces (NEW) = 5 sensors * 14 pads/values per sensor * 4 bytes per value = 280 bytes)... bytes 399-678
    if len(data) >= 678:
        segment_data = np.frombuffer(data[398:678], np.float32, 70)
    elif len(data) >= 458:
        segment_data = np.frombuffer(data[398:458], np.float32, 15)

    return joint_data, contact_data, segment_data


class UnityUdp(Udp, DataSink):
    """
        % Left
        obj.MplCmdPort = 25100;
        obj.MplLocalPort = 25101;
        obj.MplAddress = '127.0.0.1';
        % Right
        obj.MplCmdPort = 25000;
        obj.MplLocalPort = 25001;
        obj.MplAddress = '127.0.0.1';

    """
    def __init__(self):
        DataSink.__init__(self)
        Udp.__init__(self)
        self.name = "UnityUdp"
        self.onmessage = self.message_handler
        pass

    def message_handler(self, data):

        joint_data, contact_data, segment_data = get_percepts(data)
        try:
            self.position['last_percept'] = np.array(joint_data[0::3])
        except TypeError:
            self.position['last_percept'] = None

    def get_status_msg(self):
        # returns a general purpose status message about the system state
        # e.g. ' 22.5V 72.6C'
        return 'vMPL'

    def send_joint_angles(self, values, velocity=[0.0]*mpl.JointEnum.NUM_JOINTS):
        """

        send_joint_angles

        encode and transmit MPL joint angles to unity.

        :param values:
         Array of joint angles in radians.  Ordering is specified in mpl.JointEnum
         values can either be the 7 arm values, or 27 arm and hand values

        :param velocity:
         Array of joint velocities.  Unused in unity

        :return:
         None

        """

        if not self.is_connected:
            logging.warning('Connection closed.  Call connect() first')
            return

        if len(values) == mpl.JointEnum.NUM_JOINTS:
            pass
        elif len(values) == 7:
            # Only upper arm angles passed.  Use zeros for hand angles
            values = values + 20 * [0.0]
        else:
            logging.info('Invalid command size for send_joint_angles(): len=' + str(len(values)))
            return

        # Send data
        logging.debug('Joint Command:' + np.array2string(np.array(values), precision=2, separator=','))
        packer = struct.Struct('27f')
        packed_data = packer.pack(*values)
        if self.is_connected:
            self.send(packed_data)
        else:
            print('Socket disconnected')
