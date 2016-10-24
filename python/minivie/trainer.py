#!/usr/bin/python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
from shutil import copyfile
import h5py
import datetime as dt
import time
from six.moves import input
import numpy as np
from inputs import myo
from pattern_rec.feature_extract import feature_extract
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from controls.plant import Plant
from mpl.nfu import NfuUdp
from mpl.unity import UnityUdp

class Classifier:
    def __init__(self, training_data=None):
        self.TrainingData = training_data
        self.classifier = None
        pass

    def fit(self):
        """
        Fit data currently stored in self.TrainingData and self.TrainingClass to LDA or QDA model

        """

        if self.TrainingData.num_samples == 0:
            print('No Data')
            self.classifier = None
            return
            # raise ValueError('Training Data or Class array(s) is empty. Did you forget to save training data?')

        f_ = np.array(self.TrainingData.data)
        print(f_)
        y = np.array(self.TrainingData.id)
        print('Training data Numpy arrays')
        print('shape of X: ' + str(f_.shape))
        print('shape of y: ' + str(y.shape))

        # self.clf = QuadraticDiscriminantAnalysis()
        self.classifier = LinearDiscriminantAnalysis()
        self.classifier.fit(f_, y)


class TrainingData:
    """Python Class for managing machine learning and Myo training operations."""
    def __init__(self):
        self.filename = 'TRAINING_DATA'
        self.file_ext = '.hdf5'
        self.reset()
        self.motion_names = (
            'Elbow Flexion', 'Elbow Extension',
            'Wrist Rotate In', 'Wrist Rotate Out',
            'Wrist Flex In', 'Wrist Extend Out',
            'Hand Open',
            'Spherical Grasp',
            'Tip Grasp',
            'Point Grasp',
            'No Movement',
        )
        self.data = []  # List of all feature extracted samples
        self.id = []  # List of class indices that each sample belongs to
        self.name = []  # Name of each class
        self.time_stamp = []
        self.num_channels = 0
        self.num_samples = 0

    def reset(self):
        self.data = []  # List of all feature extracted samples
        self.id = []  # List of class indices that each sample belongs to
        self.name = []  # Name of each class
        self.time_stamp = []
        self.num_samples = 0

    def add_data(self, data_, id_, name_):
        self.time_stamp.append(time.time())
        self.name.append(name_)
        self.id.append(id_)
        self.data.append(data_)
        self.num_samples += 1

    def get_totals(self, motion_id=None):

        num_motions = len(self.motion_names)

        if motion_id is None:
            total = [0] * num_motions
            for c_ in range(num_motions):
                total[c_] = self.id.count(c)
        else:
            total = self.id.count(motion_id)

        return total

    def load(self):

        h5 = h5py.File(self.filename + self.file_ext, 'r')
        self.id = h5['/data/id'][:].tolist()
        motion_name = h5['/data/name'][:].tolist()
        for idx_, val_ in enumerate(motion_name):
            motion_name[idx_] = val_.decode('utf-8')
        self.name = motion_name
        self.data = h5['/data/data'][:].tolist()
        h5.close()

        self.num_samples = len(self.id)

    def save(self):
        t = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        h5 = h5py.File(self.filename + self.file_ext, 'w')
        group = h5.create_group('data')
        group.attrs['description'] = t + 'Myo Armband Raw EMG Data'
        group.attrs['num_channels'] = self.num_channels
        group.create_dataset('time_stamp', data=self.time_stamp)
        group.create_dataset('id', data=self.id)
        encoded = [a.encode('utf8') for a in self.name]
        group.create_dataset('name', data=encoded)
        group.create_dataset('data', data=self.data)
        h5.close()
        print('Saved ' + self.filename)

    def copy(self):
        # if a training file exists, copy it to a datestamped name
        t = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        src_ = self.filename + self.file_ext
        dst_ = self.filename + '_' + t + self.file_ext
        try:
            copyfile(src_, dst_)
        except FileNotFoundError:
            print('No file exists to backup')

# Setup devices and modules

# plant aka state machine
filename = "../../WrRocDefaults.xml"
plant = Plant(0.05, filename)

# input (emg) device
src = (myo.MyoUdp(source='//127.0.0.1:15001'), myo.MyoUdp(source='//127.0.0.1:15002'))
for s in src:
    s.connect()
data = TrainingData()
try:
    data.load()
except OSError:
    print('File Not Found')
    pass
except IOError:
    print('File Not Found')
    pass

data.num_channels = 16

c = Classifier(data)
c.fit()

# output destination
data_sink = NfuUdp()
# data_sink = UnityUdp() # (ip="192.168.137.1")
data_sink.connect()

while True:

    # Show menu
    print(30 * '\n')
    print(30 * '-')
    print("   T R A I N E R  ")
    print(30 * '-')
    print(" R. Run decode")
    print(" B. Backup training data")
    print(" S. Save File")
    print(" X. Reset File")
    print(30 * '-')
    for idx, val in enumerate(data.motion_names):
        print("{:2d}. {} [{}]".format(idx+1, val, data.get_totals(idx)))
    print(30 * '-')
    print(" 0. Exit")
    print(30 * '-')

    # Get input
    choice = input('Enter selection : ')
    assert isinstance(choice, str)  # native str on Py2 and Py3

    # Take action as per selected menu-option #
    if choice == '0':
        print("Exiting...")
        break
    if choice == 'P':
        for idx, s in enumerate(src):
            print('Source ' + str(idx))
            print(s.get_data())
            print('\n')

    elif choice == 'S':
        data.save()
        c.fit()

    elif choice == 'B':
        data.copy()

    elif choice == 'X':
        data.reset()
        c.fit()

    elif choice.upper() == 'R':
        # run classifier:

        if c.classifier is None:
            continue

        for i in range(100):
            time.sleep(0.02)  # 50Hz

            # Get features from emg data
            f = np.array([])
            for s in src:
                f = np.append(f, feature_extract(s.get_data() * 0.01))
            # format the data in a way that sklearn wants it
            f = np.squeeze(f)
            f = f.reshape(1, -1)
            out = c.classifier.predict(f)
            # print(out)
            class_decision = data.motion_names[out]
            print(class_decision)

            class_info = plant.class_map(class_decision)

            gain = 0.2

            # Set joint velocities
            plant.new_step()
            # set the mapped class
            if class_info['IsGrasp']:
                if class_info['GraspId'] is not None:
                    plant.GraspId = class_info['GraspId']
                plant.set_grasp_velocity(class_info['Direction'] * gain)
            else:
                plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * gain)

            plant.update()

            # transmit output
            data_sink.send_joint_angles(plant.JointPosition)

    else:
        # print('Invalid Selection')
        # Train the selected class

        try:
            choice = int(choice)

        except ValueError:
            print('Invalid Selection')
            continue

        if choice < 1 or choice > len(data.motion_names):
            print('Out of Range')
            continue

        for i in range(100):
            time.sleep(0.02)
            f = np.array([])
            for s in src:
                f = np.append(f, feature_extract(s.get_data()*0.01))
            f = f.tolist()
            data.add_data(f, choice - 1, data.motion_names[choice - 1])

            print(data.motion_names[choice - 1] + ''.join(format(x, "10.3f") for x in f[0::4]))
            # print(data.motion_names[choice - 1])

        c.fit()
        pass

for s in src:
    s.close()

print("Done")
