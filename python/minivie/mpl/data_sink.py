#!/usr/bin/env python
"""
Created 7-21-2017

Abstract Base Class (abc) for all data sinks.
Will define minimum methods that must be overloaded
for each child to maintain proper functionality with
minivie.

@author: Connor Pyles
"""

from abc import ABCMeta, abstractmethod


class DataSink(object):
    __metaclass__ = ABCMeta

    def __init__(self):
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