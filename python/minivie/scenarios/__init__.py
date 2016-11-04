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
