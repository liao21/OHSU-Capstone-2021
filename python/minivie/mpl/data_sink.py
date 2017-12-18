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

from abc import ABCMeta, abstractmethod


class DataSink(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        # This private variable is used to monitor data receipt from the limb.  If a timeout occurs then the parameter
        # is false until new data is received
        self.active_connection = False

        # store the last known limb position
        self.last_percept_position = None

    def wait_for_connection(self):
        # After connecting, this function can be used as a blocking call to ensure the desired percepts are received
        # before continuing program execution.  E.g. ensure valid joint percepts are received to ensure smooth start

        print('Checking for valid percepts...')

        while (not self.active_connection) and (self.last_percept_position is None):
            time.sleep(0.02)
            print('Waiting 20 ms for valid percepts...')
            logging.info('Waiting 20 ms for valid percepts...')

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
