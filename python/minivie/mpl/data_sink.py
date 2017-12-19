#!/usr/bin/env python
"""
Created 7-21-2017

Abstract Base Class (abc) for all data sinks.
Will define minimum methods that must be overloaded
for each child to maintain proper functionality with
minivie.

@author: Connor Pyles
"""

import time
import logging
import math
import mpl
import utilities.user_config
import numpy as np

from abc import ABCMeta, abstractmethod


class DataSink(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        # This private variable is used to monitor data receipt from the limb.  If a timeout occurs then the parameter
        # is false until new data is received
        self.active_connection = False

        # store the last known limb position
        self.last_percept_position = None

        self.position_park = [0.0] * mpl.JointEnum.NUM_JOINTS
        for i in range(mpl.JointEnum.NUM_JOINTS):
            pos = utilities.user_config.get_user_config_var(mpl.JointEnum(i).name + '_POS_PARK', 0.0)
            self.position_park[i] = pos * math.pi / 180

    def wait_for_connection(self):
        # After connecting, this function can be used as a blocking call to ensure the desired percepts are received
        # before continuing program execution.  E.g. ensure valid joint percepts are received to ensure smooth start

        print('Checking for valid percepts...')

        while (not self.active_connection) and (self.last_percept_position is None):
            time.sleep(0.02)
            print('Waiting 20 ms for valid percepts...')
            logging.info('Waiting 20 ms for valid percepts...')

    def goto_smooth(self, new_position):
        # Smoothly move to a new position

        # first get current position
        if (not self.active_connection) or (self.last_percept_position is None):
            logging.warning('Limb Position is unknown. Go-to command disabled')
            return

        # create map between current position and target position
        start_angles = self.last_percept_position
        end_angles = new_position

        for percent in np.linspace(0, 100, 200):

            intermediate_command = [0.0] * len(start_angles)
            for idx, start_angle in enumerate(start_angles):
                # linear interpolate
                end_angle = end_angles[idx]
                x0 = 0
                y0 = start_angle
                x1 = 100
                y1 = end_angle
                x = percent
                y = (y0 * (x1 - x) + y1 * (x - x0)) / (x1 - x0)
                intermediate_command[idx] = y
            self.send_joint_angles(intermediate_command)
            time.sleep(0.02)
            logging.warning('Limb Go-to...')
        logging.warning('Limb Go-to Complete')

        pass

    # All methods with this decorator must be overloaded
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def get_status_msg(self):
        pass

    @abstractmethod
    def send_joint_angles(self, values):
        pass

    @abstractmethod
    def get_percepts(self):
        pass

    @abstractmethod
    def close(self):
        pass
