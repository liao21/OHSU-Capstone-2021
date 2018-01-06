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
from mpl import JointEnum as Mpl
import controls
import utilities.user_config as uc
import numpy as np

from abc import ABCMeta, abstractmethod


class DataSink(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.active_connection = False # marked for removal.  only used by NfuUdp

        # store the last known limb position; None indicates no valid percepts received
        self.position = {'last_percept': None, 'home': [0.0] * Mpl.NUM_JOINTS, 'park': [0.0] * Mpl.NUM_JOINTS}

        for i in range(Mpl.NUM_JOINTS):
            self.position['park'][i] = np.deg2rad(uc.get_user_config_var(Mpl(i).name + '_POS_PARK', 0.0))

        for i in range(Mpl.NUM_JOINTS):
            self.position['home'][i] = np.deg2rad(uc.get_user_config_var(Mpl(i).name + '_POS_HOME', 0.0))

    def wait_for_connection(self):
        # After connecting, this function can be used as a blocking call to ensure the desired percepts are received
        # before continuing program execution.  E.g. ensure valid joint percepts are received to ensure smooth start

        print('Checking for valid percepts...')

        while self.position['last_percept'] is None:
            time.sleep(controls.timestep)
            print('Waiting 20 ms for valid percepts...')
            logging.info('Waiting 20 ms for valid percepts...')

    def goto_smooth(self, new_position):
        # Smoothly move to a new position

        # first get current position
        if self.position['last_percept'] is None:
            logging.warning('Limb Position is unknown. Go-to command disabled')
            return

        # create map between current position and target position
        start_angles = self.position['last_percept']
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
            time.sleep(controls.timestep)
        logging.info('Limb Go-to Complete')

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
