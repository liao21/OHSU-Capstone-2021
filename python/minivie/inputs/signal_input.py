#!/usr/bin/env python
"""
Created 4-20-2017

Abstract Base Class (abc) for all signal inputs.
Will define minimum methods that must be overloaded
for each child to maintain proper functionality with
minivie.

@author: Connor Pyles
"""

from abc import ABCMeta, abstractmethod


class SignalInput(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    # All methods with this decorator must be overloaded
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def close(self):
        pass
