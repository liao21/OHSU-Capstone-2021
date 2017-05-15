# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

The Plant object should hold the state information for the limb system.  This
Allows generating velocity commands that are locally integrated to update position
as a function of time.  The update() method should be called repeatedly at fixed intervals
to advance the kinematic state

Usage:

from the python\minivie folder:

from Controls import Plant

Plant.main()

Revisions:
2016JUL26: Reverted changes back to the simple Joint dictionary since ROC table not working
2016OCT07: Added joint limit from xml file

@author: R. Armiger
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger
import os
import math
import time
import logging
import numpy as np

import mpl.roc as roc
from mpl import JointEnum as MplId
from utilities import user_config


def class_map(class_name):
    """ Map a pattern recognition class name to a joint command

     The objective of this function is to decide how to interpret a class decision
     as a movement action.

     return JointId, Direction, IsGrasp, Grasp

       'No Movement' is not necessary in dict_Joint with '.get default return
     JointId, Direction = self.Joint.get(class_name,[ [], 0 ])
    """
    class_info = {'IsGrasp': 0, 'JointId': None, 'Direction': 0, 'GraspId': None}

    # Map classes to joint id and direction of motion
    # Class Name: IsGrasp, JointId, Direction, GraspId
    class_lookup = {
        'No Movement': [False, None, 0, None],
        'Shoulder Flexion': [False, MplId.SHOULDER_FE, +1, None],
        'Shoulder Extension': [False, MplId.SHOULDER_FE, -1, None],
        'Shoulder Adduction': [False, MplId.SHOULDER_AB_AD, +1, None],
        'Shoulder Abduction': [False, MplId.SHOULDER_AB_AD, -1, None],
        'Humeral Internal Rotation': [False, MplId.HUMERAL_ROT, +1, None],
        'Humeral External Rotation': [False, MplId.HUMERAL_ROT, -1, None],
        'Elbow Flexion': [False, MplId.ELBOW, +1, None],
        'Elbow Extension': [False, MplId.ELBOW, -1, None],
        'Wrist Rotate In': [False, MplId.WRIST_ROT, +1, None],
        'Wrist Rotate Out': [False, MplId.WRIST_ROT, -1, None],
        'Wrist Adduction': [False, MplId.WRIST_AB_AD, +1, None],
        'Wrist Abduction': [False, MplId.WRIST_AB_AD, -1, None],
        'Wrist Flex In': [False, MplId.WRIST_FE, +1, None],
        'Wrist Extend Out': [False, MplId.WRIST_FE, -1, None],
        'Hand Open': [True, None, -1, None],
        'Spherical Grasp': [True, None, +1, 'Spherical'],
        'Tip Grasp': [True, None, +1, 'FinePinch(American)'],
        'Three Finger Pinch Grasp': [True, None, +1, 'ThreeFingerPinch'],
        'Lateral Grasp': [True, None, +1, 'Lateral'],
        'Cylindrical Grasp': [True, None, +1, 'Cylindrical'],
        'Power Grasp': [True, None, +1, 'Cylindrical'],
        'Point Grasp': [True, None, +1, 'Trigger(Drill)'],
        'Index Grasp': [True, None, +1, 'Index Only'],
        'Middle Grasp': [True, None, +1, 'Middle Only'],
        'Ring Grasp': [True, None, +1, 'Ring Only'],
        'Little Grasp': [True, None, +1, 'Little Only'],
        'Thumb Grasp': [True, None, +1, 'Thumb Only'],
    }

    if class_name in class_lookup:
        class_info['IsGrasp'], class_info['JointId'], class_info['Direction'], class_info['GraspId'] = class_lookup[
            class_name]
    else:
        logging.warning('Unmatched class name {}'.format(class_name))

    return class_info


class Plant(object):
    """
        The main state-space integrator for the system.
        Allows setting velocity commands and then as long as they execute
        the arm will move in that direction.  position parameters will be updated
        automatically so that position commands can be send to output devices
        Additionally limits are handled here as well as roc table lookup
    """

    def __init__(self, dt, roc_filename):

        self.JointPosition = np.zeros(MplId.NUM_JOINTS)
        self.JointVelocity = np.zeros(MplId.NUM_JOINTS)

        # Load limits from xml config file
        self.lowerLimit = [0.0] * MplId.NUM_JOINTS
        self.upperLimit = [30.0] * MplId.NUM_JOINTS

        for i in range(MplId.NUM_JOINTS):
            limit = user_config.get_user_config_var(MplId(i).name + '_LIMITS', (0.0, 30.0))
            self.lowerLimit[i] = limit[0] * math.pi / 180
            self.upperLimit[i] = limit[1] * math.pi / 180

        self.dt = dt

        self.rocTable = roc.read_roc_table(roc_filename)

        # currently selected ROC for arm motion
        self.RocId = ''
        self.RocPosition = 0.0
        self.RocVelocity = 0.0

        # currently selected ROC for hand motion
        self.GraspId = ''
        self.GraspPosition = 0.0
        self.GraspVelocity = 0.0

    def new_step(self):
        # set all velocities to 0 to prepare for a new timestep 
        # Typically followed by a call to setVelocity

        # reset velocity
        self.JointVelocity[:] = 0.0
        self.RocVelocity = 0.0
        self.GraspVelocity = 0.0

    def set_roc_velocity(self, roc_velocity):
        # set the velocities of the roc
        self.RocVelocity = roc_velocity

    def set_grasp_velocity(self, grasp_velocity):
        # set the velocities of the grasp roc
        self.GraspVelocity = grasp_velocity

    def set_joint_velocity(self, joint_id, joint_velocity):
        # set the velocities of the list of joint ids
        if joint_id is not None:
            self.JointVelocity[joint_id] = joint_velocity

    def update(self):
        # perform time integration based on elapsed time, dt

        # integrate roc values
        self.RocPosition += self.RocVelocity * self.dt
        self.GraspPosition += self.GraspVelocity * self.dt
        # Apply limits
        self.RocPosition = np.clip(self.RocPosition, 0, 1)
        self.GraspPosition = np.clip(self.GraspPosition, 0, 1)

        # integrate joint positions from velocity commands
        self.JointPosition += self.JointVelocity * self.dt

        # set positions based on roc commands
        # hand positions will always be roc
        if self.RocId in self.rocTable:
            new_vals = roc.get_roc_values(self.rocTable[self.RocId], self.RocPosition)
            self.JointPosition[self.rocTable[self.RocId].joints] = new_vals
        if self.GraspId in self.rocTable:
            new_vals = roc.get_roc_values(self.rocTable[self.GraspId], self.GraspPosition)
            self.JointPosition[self.rocTable[self.GraspId].joints] = new_vals

        # Apply limits
        self.JointPosition = np.clip(self.JointPosition, self.lowerLimit, self.upperLimit)


def main():
    # for demo
    from mpl.unity import UnityUdp as hSink

    # get default roc file.  This should be run from python\minivie as home, but 
    # also support calling from module directory (Utilities)
    roc_filename = "../../WrRocDefaults.xml"
    if os.path.split(os.getcwd())[1] == 'Controls':
        roc_filename = '../' + roc_filename

    dt = 0.02
    p = Plant(dt, roc_filename)

    sink = hSink()
    sink.connect()

    print('LOWER LIMITS:')
    print(p.lowerLimit)
    print('UPPER LIMITS:')
    print(p.upperLimit)

    time_begin = time.time()
    while time.time() < (time_begin + 1.5):  # main loop
        time.sleep(dt)
        class_name = 'Shoulder Flexion'
        class_info = class_map(class_name)

        # Set joint velocities
        p.new_step()
        # set the mapped class
        p.set_joint_velocity(class_info['JointId'], class_info['Direction'])
        # set a few other joints with a new velocity
        p.set_joint_velocity([MplId.ELBOW, MplId.WRIST_AB_AD], 2.5)

        # set a grasp state        
        # p.GraspId = 'rest'
        p.GraspId = 'Spherical'
        p.set_grasp_velocity(0.5)

        p.update()

        sink.send_joint_angles(p.JointPosition)

        # Print first 7 joints
        ang = ''.join('{:6.1f}'.format(k * 180 / math.pi) for k in p.JointPosition[:7])
        print('Angles (deg):' + ang + ' | Grasp Value: {:6.3f}'.format(p.GraspPosition))

    class_map('Unmatched')

    sink.close()


# Main Function (for demo)
if __name__ == "__main__":
    main()
