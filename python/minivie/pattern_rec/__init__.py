# -*- coding: utf-8 -*-
import os
from shutil import copyfile
import h5py
import datetime as dt
import time
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis


import numpy as np


def feature_extract(y, zc_thresh=0.15, ssc_thresh=0.15, sample_rate=200):
    """
    Created on Mon Jan 25 16:25:14 2016

    Perform feature extraction, veoctorized

    @author: R. Armiger
    # compute features
    #
    # Input:
    # data buffer to compute features
    # y = numpy.zeros((numSamples, numChannels))
    # E.g. numpy.zeros((50, 8))
    #
    # Optional:
    # Thresholds for computing zero crossing and slope sign change features
    #
    # Output: feature vector should be [1,nChan*nFeat]
    # data ordering is as follows
    # [ch1f1, ch1f2, ch1f3, ch1f4, ch2f1, ch2f2, ch2f3, ch2f4, ... chNf4]
    """

    # Number of Samples
    n = y.shape[0]

    # Normalize features so they are independent of the window size
    fs = sample_rate

    # Value to compute 'zero-crossing' around
    t = 0.0

    # Compute mav across all samples (axis=0)
    mav = np.mean(abs(y), 0)  # mav shouldn't be normalized

    # Curve length is the sum of the absolute value of the derivative of the
    # signal, normalized by the sample rate
    curve_len = np.sum(abs(np.diff(y, axis=0)), axis=0) * fs / n

    # Criteria for crossing zero
    # zeroCross=(y[iSample] - t > 0 and y[iSample + 1] - t < 0) or (y[iSample] - t < 0 and y[iSample + 1] - t > 0)
    # overThreshold=abs(y[iSample] - t - y[iSample + 1] - t) > zc_thresh
    # if zeroCross and overThreshold:
    #     # Count a zero cross
    #     zc[iChannel]=zc[iChannel] + 1
    zc = np.sum(
        ((y[0:n - 1, :] - t > 0) & (y[1:n, :] - t < 0) |
         (y[0:n - 1, :] - t < 0) & (y[1:n, :] - t > 0)) &
        (abs(y[0:n - 1, :] - t - y[1:n, :] - t) > zc_thresh),
        axis=0) * fs / n

    # Criteria for counting slope sign changes
    # signChange = (y[iSample] > y[iSample - 1]) and (y[iSample] > y[iSample + 1]) or (y[iSample] < y[iSample - 1]) and
    #       (y[iSample] < y[iSample + 1])
    # overThreshold=abs(y[iSample] - y[iSample + 1]) > ssc_thresh or abs(y[iSample] - y[iSample - 1]) > ssc_thresh
    # if signChange and overThreshold:
    #     # Count a slope change
    #     ssc[iChannel]=ssc[iChannel] + 1
    ssc = np.sum(
        ((y[1:n - 1, :] > y[0:n - 2, :]) & (y[1:n - 1, :] > y[2:n, :]) |
         (y[1:n - 1, :] < y[0:n - 2, :]) & (y[1:n - 1, :] < y[2:n, :])) &
        ((abs(y[1:n - 1, :] - y[2:n, :]) > ssc_thresh) | (abs(y[1:n - 1, :] - y[0:n - 2, :]) > ssc_thresh)),
        axis=0) * fs / n

    # VAR = np.var(y,axis=0) * fs / n

    features = np.vstack((mav, curve_len, zc, ssc))

    return features.T.reshape(1, 32)


def test_feature_extract():
    # Offline test code
    import matplotlib.pyplot as plt
    import math
    import timeit

    NUM = 2000
    emg_buffer = np.zeros((NUM, 8))
    sinArray = np.sin(2 * math.pi * 10 * np.linspace(0, 1, num=NUM))

    emg_buffer[:, :1] = np.reshape(sinArray, (NUM, 1))
    emg_buffer[:, :7] = np.reshape(sinArray, (NUM, 1))
    plt.plot(sinArray)

    start_time = timeit.default_timer()
    # code you want to evaluate
    f = feature_extract(emg_buffer)
    # code you want to evaluate
    elapsed = timeit.default_timer() - start_time
    print(elapsed)

    print(f)


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
                total[c_] = self.id.count(c_)
        else:
            total = self.id.count(motion_id)

        return total

    def load(self):

        if not os.path.isfile(self.filename + self.file_ext):
            print('File Not Found: ' + self.filename + self.file_ext)
            return

        if not os.access(self.filename + self.file_ext, os.R_OK):
            print('File Not Readable: ' + self.filename + self.file_ext)
            return

        try:
            h5 = h5py.File(self.filename + self.file_ext, 'r')
        except IOError:
            print('Error Loading file: ' + self.filename + self.file_ext)
            return

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

        if not os.path.isfile(self.filename + self.file_ext):
            print('File Not Found: ' + self.filename + self.file_ext)
            return

        if not os.access(self.filename + self.file_ext, os.R_OK):
            print('File Not Readable: ' + self.filename + self.file_ext)
            return

        t = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        src_ = self.filename + self.file_ext
        dst_ = self.filename + '_' + t + self.file_ext
        try:
            copyfile(src_, dst_)
        except IOError:
            print('Failed to create file backup')
