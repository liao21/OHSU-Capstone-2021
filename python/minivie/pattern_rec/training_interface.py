#!/usr/bin/env python
"""
Created 7-21-2017

Abstract Base Class (abc) for all training managers.
Will define minimum methods that must be overloaded
for each child to maintain proper functionality with
minivie.

@author: Connor Pyles
"""

from abc import ABCMeta, abstractmethod


class TrainingInterface(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    # All methods with this decorator must be overloaded
    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def add_message_handler(self, func):
        pass

    @abstractmethod
    def send_message(self, msg_id, msg):
        pass

    @abstractmethod
    def close(self):
        pass