from abc import ABCMeta, abstractmethod, abstractproperty


class EMGFeatures(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractproperty
    def name(self):
        pass

    # All methods with this decorator must be overloaded
    @abstractmethod
    def extract_features(self):
        pass



