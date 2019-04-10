"""
Handle UDP communications to Unity vMPL Environment

On construction, this class creates a communication port with the following
optional input arguments:

JHUAPL vMPL Unity Communications Info:
    Data should be sent in little endian format.

    Message               Transmission Type	Source	Target	Port
    Right vMPL Command            Broadcast	VULCANX	vMPLEnv	25000
    Right vMPL Percepts           Broadcast	vMPLEnv	VULCANX	25001
    Left vMPL Command             Broadcast	VULCANX	vMPLEnv	25100
    Left vMPL Percepts            Broadcast	vMPLEnv	VULCANX	25101
    Right Virtual Hand Command	  Broadcast	VULCANX	vMPLEnv	25200
    Right Virtual Hand Percepts	  Broadcast	vMPLEnv	VULCANX	25201
    Left Virtual Hand Command     Broadcast	VULCANX	vMPLEnv	25300
    Left Virtual Hand Percepts	  Broadcast	vMPLEnv	VULCANX	25301

    ** New as of 7/2019 **
    These command ports send data to control the position and color config of the transparent 'ghost' arms
    Right vMPL Ghost Command      Broadcast	VULCANX	vMPLEnv	25010
    Left vMPL Ghost Command       Broadcast	VULCANX	vMPLEnv	25110
    Right vMPL Ghost Control      Broadcast	VULCANX	vMPLEnv	27000
    Left vMPL Ghost Control       Broadcast	VULCANX	vMPLEnv	27100


Inputs: 
    remote_address - string of IP address and port of destination (running Unity) default = '//127.0.0.1:25000'
    local_address - string of IP address and port to receive percepts default = '//127.0.0.1:25001'

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

    >>> sink2 = UnityUdp(remote_address='//127.0.0.1:25100', local_address='//127.0.0.1:25101')
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

import struct
import logging
import numpy as np
from mpl import JointEnum as MplId
from mpl.data_sink import DataSink
from utilities import Udp
from utilities.user_config import get_user_config_var


def extract_percepts(data):
    """
    Get sensor data from vMPL (returns tuple)

    :return:

        percepts['jointPercepts']['position'] array [27] of joint position
        percepts['jointPercepts']['velocity'] array [27] of joint velocity
        percepts['jointPercepts']['torque'] array [27] of joint torque

        # ContactPerceptsType   74 (37 values (2 bytes each), so (2x37) enum for each of potential contact sensors)
        percepts['segmentPercepts']['contactPercepts'] - Contact pad data

        # FtsnForcePerceptsType 60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60))
        # FtsnAccelPerceptsType 60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60))
        # FtsnTempPerceptsType  20 (1 x 32-bit value (1 x 4 bytes) for each of 5 fingers, so (1x4x5 = 20))
        percepts['segmentPercepts']['ftsn'] - FTSN Data (old/new)

    """
    # this is the return value
    percepts = dict()

    # Convert raw bytes

    # Upper Arm Joints = 7 Joints * 3 values per joint * 4 bytes per value = 84 bytes)... bytes 0-84
    # Fingers and Thumb = 20 Joints * 3 values per joint * 4 bytes per value = 240 bytes)... bytes 85-324
    #
    # Float32Type angles;		// radians
    # Float32Type velocities;    // radians/second
    # Float32Type torques;       // Expect NaN from vMPLEnv.

    if len(data) >= 324:
        joint_data = struct.unpack('%df' % MplId.NUM_JOINTS * 3, data[0:324])
        percepts['jointPercepts'] = dict()
        percepts['jointPercepts']['position'] = joint_data[0::3]
        percepts['jointPercepts']['velocity'] = joint_data[1::3]
        percepts['jointPercepts']['torque'] = joint_data[2::3]
        percepts['jointPercepts']['temperature'] = [float('nan')] * 27

    # ContactPerceptsType   74 (37 values (2 bytes each), so (2x37) enum for each of potential contact sensors)
    # FtsnForcePerceptsType 60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60))
    # FtsnAccelPerceptsType 60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60))
    # FtsnTempPerceptsType  20 (1 x 32-bit value (1 x 4 bytes) for each of 5 fingers, so (1x4x5 = 20))
    if len(data) >= 398:
        percepts['segmentPercepts'] = dict()
        percepts['segmentPercepts']['contactPercepts'] = struct.unpack('%dH' % 37, data[324:398])

    # Segment forces (OLD) = 5 sensors * 3 axes/values per sensor * 4 bytes per value = 60 bytes)... bytes 399-458
    # Segment forces (NEW) = 5 sensors * 14 pads/values per sensor * 4 bytes per value = 280 bytes)... bytes 399-678
    if len(data) >= 678:
        percepts['segmentPercepts']['ftsn'] = struct.unpack('%df' % 70, data[398:678])
    elif len(data) >= 458:
        percepts['segmentPercepts']['ftsn'] = struct.unpack('%df' % 15, data[398:458])

    return percepts


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
    def __init__(self, local_address='//0.0.0.0:25001', remote_address='//127.0.0.1:25000'):
        DataSink.__init__(self)
        Udp.__init__(self, local_address=local_address, remote_address=remote_address)
        self.command_port = 25010  # integer port for ghost arm position commands
        self.config_port = 27000    # integer port for ghost arm display commands
        self.name = "UnityUdp"
        self.onmessage = self.message_handler
        self.percepts = None
        self.joint_offset = None
        self.load_config_parameters()

    def load_config_parameters(self):
        # Load parameters from xml config file

        self.joint_offset = [0.0] * MplId.NUM_JOINTS
        for i in range(MplId.NUM_JOINTS):
            self.joint_offset[i] = np.deg2rad(get_user_config_var(MplId(i).name + '_OFFSET', 0.0))

    def message_handler(self, data):

        self.percepts = extract_percepts(data)
        try:
            self.position['last_percept'] = self.percepts['jointPercepts']['position']
        except TypeError or KeyError:
            self.position['last_percept'] = None

    def get_status_msg(self):
        # returns a general purpose status message about the system state
        # e.g. ' 22.5V 72.6C'
        return 'vMPL'

    def send_joint_angles(self, values, velocity=[0.0] * MplId.NUM_JOINTS, send_to_ghost=False):
        """

        send_joint_angles

        encode and transmit MPL joint angles to unity using command port

        :param values:
         Array of joint angles in radians.  Ordering is specified in mpl.JointEnum
         values can either be the 7 arm values, or 27 arm and hand values

        :param velocity:
         Array of joint velocities.  Unused in unity

        :param send_to_ghost:
         Optional boolean operator to send data to alternate (ghost) arm as opposed to primary arm visualization

        :return:
         None

        """

        if not self.is_connected:
            logging.warning('Connection closed.  Call connect() first')
            return

        if len(values) == 7:
            # Only upper arm angles passed.  Use zeros for hand angles
            values = values + 20 * [0.0]
        elif len(values) != MplId.NUM_JOINTS:
            logging.info('Invalid command size for send_joint_angles(): len=' + str(len(values)))
            return

        # Apply joint offsets if needed
        values = np.array(values) + self.joint_offset

        # Send data
        msg = 'Joint Command: ' + ','.join(['%d' % elem for elem in values])
        logging.debug(msg)  # 60 us

        packer = struct.Struct('27f')
        packed_data = packer.pack(*values)
        if self.is_connected:
            if send_to_ghost:
                self.send(packed_data, (self.remote_hostname, self.command_port))
            else:
                self.send(packed_data)
        else:
            print('Socket disconnected')

    def send_config_command(self, enable=0.0, color=[0.3, 0.4, 0.5], alpha=0.8):
        """

        send_config_command

        encode and transmit MPL joint angles to unity.  The destination port for this function is stored in the
        self.config_port parameter

        :param enable:
         float indicating 1.0 show or 0.0 hide ghost limb

        :param color:
         float array (3 by 1) limb RGB color normalized 0.0-1.0

        :param alpha:
         float array limb transparency normalized 0.0-1.0

        :return:
         None

        """

        if not self.is_connected:
            logging.warning('Connection closed.  Call connect() first')
            return

        values = [enable] + color + [alpha]

        # Send data
        msg = 'vMPL Config Command: ' + ','.join(['%d' % elem for elem in values])
        logging.debug(msg)  # 60 us

        packer = struct.Struct('5f')
        packed_data = packer.pack(*values)
        if self.is_connected:
            self.send(packed_data, (self.udp['RemoteHostname'], self.config_port))
        else:
            print('Socket disconnected')

    def get_percepts(self):
        return self.percepts
