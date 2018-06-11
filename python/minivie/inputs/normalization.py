import logging
import threading
import numpy as np
import time
from abc import ABCMeta, abstractmethod
import operator
import os
import os.path
import h5py

class NormalizationInterface(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    # All methods with this decorator must be overloaded
    @abstractmethod
    def start_normalization(self):
        pass

    @abstractmethod
    def save_results(self):
        pass



class MyoNormalization(NormalizationInterface):
# Method to perform myo normalization

    def __init__(self, vie, trainer):

        # Initialize superclass
        super(NormalizationInterface, self).__init__()

        self.vie = vie
        self.trainer = trainer
        self.thread = None
        self.reset()

        self.timeout = 5.0  # Time before normalization times out

        self.shoulder = True
        self.elbow = True

        # Initialize data storage lists
        self.target_class = []
        self.class_decision = []
        self.correct_decision = []
        self.time_stamp = []
        self.class_id_to_test = []
        self.data = []  # List of dicts
        self.normalized_motion = None
        self.normalized_orientation = []

    def reset(self):
        # Method to reset all stored data

        self.target_class = []
        self.class_decision = []
        self.correct_decision = []
        self.time_stamp = []
        self.class_id_to_test = []
        self.data = []  # List of dicts
        self.NextMotionButtonPushed = False

    def command_string(self, value):
        """
        Commands are strings with the following format:

        [CMD_TYPE]:[CMD_VALUE]

        [CMD_TYPE] options are:
            Cmd - Indicates the cmd_value is a command word. Options are:
                StartAssessment
        """

        parsed = value.split(':')
        if not len(parsed) == 2:
            return
        else:
            cmd_type = parsed[0]
            cmd_data = parsed[1]

        if cmd_type == 'Cmd':
            if 'StartNormalizeMyo' in cmd_data:
                self.normalized_motion = cmd_data.split('-')[1]
                self.thread = threading.Thread(target=self.start_normalization())
                self.thread.name = 'NormalizeMyoPosition'
                self.thread.start()

            elif 'ResetOrientation' in cmd_data:
                self.reset_orientation()

    def start_normalization(self):
        # Method to assess all trained classes

        # Clear assessment data from previous assessments
        self.reset()

        # Determine which classes should be normalized
        all_class_names = self.vie.TrainingData.motion_names
        totals = self.vie.TrainingData.get_totals()
        trained_classes = [all_class_names[i] for i, e in enumerate(totals) if e != 0]
        # Remove no movement class
        if 'No Movement' in trained_classes: trained_classes.remove('No Movement')

        class_to_normalize = None

        if self.normalized_motion == 'Wrist Extend Out' :
            if 'Wrist Extend Out' in trained_classes:
                class_to_normalize = 'Wrist Extend Out'
            else:
                self.send_status('Wrist Extend Out Not Trained ... Exiting Myo Normalization')
                return
        elif self.normalized_motion == 'Elbow Flexion':
            if 'Elbow Flexion' in trained_classes:
                class_to_normalize = 'Elbow Flexion'
            else:
                self.send_status('Elbow Flextion Not Trained ... Exiting Myo Normalization')
                return
        else:
            self.send_status('No Normalization Class Selected... Exiting Myo Normalization')
            return

        # pause limb during normalization
        self.vie.pause('All', True)
        self.send_status('Holdout')


        self.send_status('Starting Normalization')
        self.data.append({'targetClass': [], 'featureData': []})

        # Assess class
        is_complete = self.assess_class(class_to_normalize)
        if is_complete:
            self.send_status('Normalization Completed!')
        else:
            self.send_status('Normalization Incomplete')

        # Compute Normalization
        self.compute_normalization()
        # Send status
        self.send_status('Myo Normalization Completed.')
        #set orientation
        self.save_normalization()
        # Unlock limb
        self.vie.pause('All', False)


    def assess_class(self, class_name):
        # Method to assess a single class, display/save results for viewing

        # Update GUI image
        image_name = self.vie.TrainingData.get_motion_image(class_name)
        if image_name:
            self.trainer.send_message("strNormalizeMyoPositionImage", image_name)

        ## Give countdown
        countdown_time = 3
        dt = 1
        tvec = np.linspace(countdown_time,0,int(round(countdown_time/dt)+1))
        for t in tvec:
            self.send_status('Normalizing Class - ' + class_name + ' - In ' + str(t) + ' Seconds')
            time.sleep(dt)

        dt = 0.1  # 100ms RIC JAMA
        timeout = self.timeout
        time_begin = time.time()
        time_elapsed = 0.0

        while (time_elapsed < timeout):

            features = []
            # get the features
            features_data = self.vie.output['features']

            if features_data is not None:
                num_features = (len(features_data) / self.vie.TrainingData.num_channels)

                for i, signal in enumerate(self.vie.SignalSource):
                    front_index = int(i * (8 * num_features))
                    back_index = int((i * (8 * num_features)) + (8 * num_features))
                    features.append(features_data[front_index:back_index])

                    # update data for output
                    self.add_data(class_name, features)

            # print status
            self.send_status('Normalizing Class: ' + class_name + ' - ' + ' Time Left: ' + str(int(timeout - time_elapsed)) + '.0 seconds')



            # Sleep before next assessed classification
            time.sleep(dt)
            time_elapsed = time.time() - time_begin

        # Motion completed, update status
        self.send_status('Class Myo Normalization - ' + class_name + ' - Complete')

        return True

    def send_status(self, status):
        # Method to send more verbose status updates for command line users and logging purposes
        print(status)
        logging.info(status)
        self.trainer.send_message("strNormalizeMyoPosition", status)

    def add_data(self, class_name, features):
        # Method to add data following each assessment

        # Append to data dicts
        self.data[-1]['targetClass'].append(class_name)
        self.data[-1]['featureData'].append(features)

    def compute_normalization(self):
        # Method to compute normalization from collected features
        self.send_status('Computing Myo Position Normalization')

        #load training data
        training_data = self.vie.TrainingData.data
        training_motion = self.vie.TrainingData.name

        num_features = 0

        training_features = []
        # create array of training data for each myo
        for myo, signal in enumerate(self.vie.SignalSource):
            myo_features = []
            for i, data in enumerate(training_data):
                if (training_motion[i] == self.normalized_motion):
                    # get the features data from training data
                    num_features = (len(data) / self.vie.TrainingData.num_channels)
                    front_index = int(myo * (8 * num_features))
                    back_index = int((myo * (8 * num_features)) + (8 * num_features))
                    myo_features.append(data[front_index:back_index])
            training_features.append(myo_features)

        # average training data
        averaged_training_features = []
        for myo, data in enumerate(training_features):
            averaged_training_features_one_myo = []
            for i, sample in enumerate(data):
                if len(averaged_training_features_one_myo) < 1:
                    averaged_training_features_one_myo = sample
                else:
                    averaged_training_features_one_myo = (
                    (np.array(averaged_training_features_one_myo) + np.array(sample)) / (i + 1)).tolist()
            averaged_training_features.append(averaged_training_features_one_myo)


        #average normalization feature data
        averaged_normalization_features = []
        for i, data in enumerate(self.data[-1]['featureData']):
            for myo, sample in enumerate(data):
                if len(averaged_normalization_features) < (myo + 1):
                    averaged_normalization_features.append(sample)
                else:
                    averaged_normalization_features[myo] = (
                    (np.array(averaged_normalization_features[myo]) + np.array(sample)) / (i + 1)).tolist()

        self.normalized_orientation = []
        for myo, normalization_data in enumerate(averaged_normalization_features):
            best_diff = None
            best_orientation = 0
            for orientation in range(8):
                #change orientation
                rolled_normalization_data = np.roll(normalization_data, int(orientation*num_features))
                myo_taining_features = averaged_training_features[myo]
                #find differences between rolled average and training average of first feature
                difference = sum(abs((np.array(myo_taining_features[:8]) - np.array(rolled_normalization_data[:8]))))
                if best_diff is None:
                    best_diff = difference
                    best_orientation = orientation
                elif difference < best_diff:
                    best_diff = difference
                    best_orientation = orientation
            self.normalized_orientation.append(best_orientation)

        self.send_status('Myo Position Normalization Computed: ' + str(self.normalized_orientation))

        # Clear data for next assessment
        self.reset()

    #adjust future data for orientation
    def save_normalization(self):
        self.vie.FeatureExtract.normalize_orientation(self.normalized_orientation)

    #rest orientation and adjust future data
    def reset_orientation(self):
        self.send_status('Myo Orientation Reset')
        self.normalized_orientation = None
        self.save_normalization()
