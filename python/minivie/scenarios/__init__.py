class Scenario(object):
    """
    Define the building blocks of the MiniVIE

        SignalSource - source of EMG data
        SignalClassifier - algorithm to classify emg into 'intent'
        Plant - Perform forward integration and apply joint limits
        DataSink - output destination of command signals (e.g. real or virtual arm)
    """
    def __init__(self):
        self.SignalSource = None
        self.SignalClassifier = None
        self.TrainingData = None
        self.Plant = None
        self.DataSink = None

        self.__pause = False
        self.__gain_value = 1.0
        self.__hand_gain_value = 1.0


    def is_paused(self):
        return self.__pause

    def get_gain_value(self):
        return self.__gain_value

    def get_hand_gain_value(self):
        return self.__hand_gain_value

    def pause(self):
        if self.__pause:
            self.__pause = False
        else:
            self.__pause = True

    def gain(self,factor):        
        self.__gain_value *= factor
        if self.__gain_value < 0.1:
            self.__gain_value = 0.1

    def hand_gain(self,factor):        
        self.__hand_gain_value *= factor
        if self.__hand_gain_value < 0.1:
            self.__hand_gain_value = 0.1
        
