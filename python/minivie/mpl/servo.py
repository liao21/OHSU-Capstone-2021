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


Created on 4/29/2019

@author: R. Armiger
"""

import asyncio
import time
import struct
import logging
import numpy as np
import pigpio
import random
from mpl import JointEnum as MplId
from mpl.data_sink import DataSink
from utilities.user_config import get_user_config_var
from utilities import get_address
from mpl.unity import extract_percepts
from controls import timestep


class UdpProtocol(asyncio.DatagramProtocol):
    """ Extend the UDP Protocol for unity data communication

    """
    def __init__(self, parent):
        self.parent = parent
        # Mark the time when object created. Note this will get overwritten once data received
        self.parent.time_emg = time.time()

    def datagram_received(self, data, addr):

        self.parent.percepts = extract_percepts(data)
        try:
            self.parent.position['last_percept'] = self.parent.percepts['jointPercepts']['position']
            self.parent.packet_count += 1
        except TypeError or KeyError:
            self.parent.position['last_percept'] = None


class Servo(DataSink):
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
    # def __init__(self):
        DataSink.__init__(self)
        self.command_port = 25010  # integer port for ghost arm position commands
        self.config_port = 27000    # integer port for ghost arm display commands
        self.name = "Servo"
        self.joint_offset = None
        self.load_config_parameters()
        self.loop = None
        self.transport = None
        self.protocol = None
        #self.local_address = local_address
        #self.remote_address = remote_address
        self.is_connected = True
        self.percepts = None
        self.position = {'last_percept': None}

        # store some rate counting parameters
        self.packet_count = 0
        self.packet_time = 0.0
        self.packet_rate = 0.0
        self.packet_update_time = 1.0  # seconds

        # servo stuff
        self.pi = pigpio.pi()

        self.servo_num = get_user_config_var('Servo.joint_num', 2)
        self.servo_joints = []
        self.servo_velocities = []
        self.servo_motor_limits = []
        self.servo_joint_limits = []
        for i in range(0, self.servo_num):
            joint = get_user_config_var('Servo.joint_id'+str(i), 4)
            self.servo_joints.append(joint)
            self.servo_velocities.append(get_user_config_var('Servo.joint_velocity'+str(i), 5.0))
            self.servo_motor_limits.append(get_user_config_var('Servo.motor_limits'+str(i), (500, 2500)))
            self.servo_joint_limits.append(get_user_config_var(MplId(joint).name+'_LIMITS', (0.0, 100.0)))

    def load_config_parameters(self):
        # Load parameters from xml config file

        self.joint_offset = [0.0] * MplId.NUM_JOINTS
        for i in range(MplId.NUM_JOINTS):
            self.joint_offset[i] = np.deg2rad(get_user_config_var(MplId(i).name + '_OFFSET', 0.0))

    def connect(self):
        """ Connect UDP socket and register callback for data received """
        #self.loop = asyncio.get_event_loop()
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        # From python 3.7 docs (https://docs.python.org/3.7/library/asyncio-protocol.html#)
        #listen = self.loop.create_datagram_endpoint(
        #    lambda: UdpProtocol(parent=self), local_addr=get_address(self.local_address))
        #self.transport, self.protocol = self.loop.run_until_complete(listen)
        pass

    async def wait_for_connection(self):
        # After connecting, this function can be used as a blocking call to ensure the desired percepts are received
        # before continuing program execution.  E.g. ensure valid joint percepts are received to ensure smooth start

        print('Checking for valid percepts...')

#        while self.position['last_percept'] is None or self.get_packet_data_rate() is 0:
#            await asyncio.sleep(timestep)
#            print('Waiting 20 ms for valid percepts...')
#            self.get_packet_data_rate()
#            logging.info('Waiting 20 ms for valid percepts...')

    def get_status_msg(self):
        """
        Create a short status message, typically shown on user interface

        :return: a general purpose status message about the system state
            e.g. ' 22.5V 72.6C' or vMPL: 50Hz
        """
        return 'vMPL: {:.0f}Hz%'.format(self.get_packet_data_rate())

    def send_joint_angles(self, values, velocity=None, send_to_ghost=False):
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
        
        rad_to_deg = 57.2957795  # 180/pi
        deg_values = [int(values[joint]*rad_to_deg) for joint in self.servo_joints]

        # Send data
        msg = ','.join(deg_values)
        logging.debug('JointCmd: ' + msg)  # 60 us
        self.pi.serial_write(self.serial, "<%s>\n" % msg)


    def send_config_command(self, enable=0.0, color=(0.3, 0.4, 0.5), alpha=0.8):
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

        values = [enable] + list(color) + [alpha]

        # Send data
        msg = 'vMPL Config Command: ' + ','.join(['%.1f' % elem for elem in values])
        logging.debug(msg)  # 60 us

        packer = struct.Struct('5f')
        packed_data = packer.pack(*values)

        (addr, port) = get_address(self.remote_address)

        if self.is_connected:
            self.transport.sendto(packed_data, (addr, self.config_port))
        else:
            print('Socket disconnected')

    def get_percepts(self):
        return self.percepts

    def get_packet_data_rate(self):
        # Return the packet data rate

        # get the number of new samples over the last n seconds

        # compute data rate
        t_now = time.time()
        t_elapsed = t_now - self.packet_time

        if t_elapsed > self.packet_update_time:
            # compute rate (every few seconds second)
            self.packet_rate = self.packet_count / t_elapsed
            self.packet_count = 0  # reset counter
            self.packet_time = t_now

        return self.packet_rate

    def close(self):
        logging.info("Closing Unity Socket @ {}".format(self.remote_address))
        self.pi.serial_close(self.serial)
        self.transport.close()

async def run_loop(sender):
    # test asyncio loop commands
    # create a positive / negative ramp to command the arm

    counter = 0
    direction = +1
    # setup main loop control
    print("")
    print("Running...")
    print("")

    dt = 0.02
    print(dt)
    angles = [0.0] * 27
    while True:
        counter += direction
        if counter > 135:
            direction = -direction
        if counter < 1:
            direction = -direction
        # print(counter)

        angles[3] = counter * 3.14159/180.0
        sender.send_joint_angles(angles)

        await asyncio.sleep(dt)


def main():

    # create socket
    vie = UnityUdp(local_address='//0.0.0.0:25001', remote_address='//127.0.0.1:25000')

    loop = asyncio.get_event_loop()
    loop.create_task(run_loop(vie))
    loop.run_forever()

    pass


if __name__ == '__main__':
    main()
