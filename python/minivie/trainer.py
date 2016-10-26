#!/usr/bin/python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
import logging
from utilities import user_config
user_config.setup_file_logging(prefix='MPL_')
import time
from six.moves import input
import numpy as np

from inputs import myo
import pattern_rec as pr
from controls.plant import Plant, class_map
from mpl.nfu import NfuUdp as Sink
# from mpl.unity import UnityUdp as Sink

# Setup devices and modules

# plant aka state machine
filename = "../../WrRocDefaults.xml"
plant = Plant(0.02, filename)

# input (emg) device
# select either 1 or 2 myo bands
src = (myo.MyoUdp(source='//127.0.0.1:15001'), myo.MyoUdp(source='//127.0.0.1:15002'))
# src = [myo.MyoUdp(source='//127.0.0.1:15001')]
num_channels = 0
for s in src:
    s.connect()
    num_channels += 8

# training data manager
data = pr.TrainingData()
data.load()

data.num_channels = num_channels

c = pr.Classifier(data)
c.fit()

zc_thresh = 0.0
ssc_thresh = 0.0
sample_rate = 200

# output destination
data_sink = Sink()
data_sink.connect()

while True:

    # Show menu
    print(30 * '\n')
    print(30 * '-')
    print("   T R A I N E R  ")
    print(30 * '-')
    print(" P. Preview Data Sources")
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
    if choice.upper() == 'P':
        while True:
            try:
                time.sleep(0.02)  # 50Hz
                f = np.array([])
                for s in src:
                    new_data = s.get_data()*0.01
                    features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
                    f = np.append(f, features)
                f = f.tolist()
                print(''.join(format(x, "6.2f") for x in f[0::4]))

            except KeyboardInterrupt:
                print('Stopping')
                break

    elif choice.upper() == 'S':
        data.save()
        c.fit()

    elif choice.upper() == 'B':
        data.copy()

    elif choice.upper() == 'X':
        data.reset()
        c.fit()

    elif choice.upper() == 'R':
        # run classifier:

        if c.classifier is None:
            continue

        # ##########################
        # Run the control loop
        # ##########################
        while True:
            try:
                time.sleep(0.02)  # 50Hz

                # Get features from emg data
                f = np.array([])
                for s in src:
                    new_data = s.get_data() * 0.01
                    features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
                    f = np.append(f, features)
                # format the data in a way that sklearn wants it
                f = np.squeeze(f)
                f = f.reshape(1, -1)
                try:
                    out = int(c.classifier.predict(f))
                except ValueError as e:
                    logging.warning('Unable to classify. Error was: ' + e)
                    break

                class_decision = data.motion_names[out]
                print(class_decision)

                class_info = class_map(class_decision)

                graspGain = 0.5
                jointGain = 1.2

                # Set joint velocities
                plant.new_step()
                # set the mapped class
                if class_info['IsGrasp']:
                    if class_info['GraspId'] is not None:
                        plant.GraspId = class_info['GraspId']
                    plant.set_grasp_velocity(class_info['Direction'] * graspGain)
                else:
                    plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * jointGain)

                plant.update()

                # transmit output
                data_sink.send_joint_angles(plant.JointPosition)

            except KeyboardInterrupt:
                print('Stopping')
                break

    else:
        # Train the selected class
        try:
            choice = int(choice)
        except ValueError:
            print('Invalid Selection')
            continue

        if choice < 1 or choice > len(data.motion_names):
            print('Selection Out of Range')
            continue

        for i in range(100):
            time.sleep(0.02)
            f = np.array([])
            for s in src:
                new_data = s.get_data()*0.01
                features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
                f = np.append(f, features)
            f = f.tolist()
            data.add_data(f, choice - 1, data.motion_names[choice - 1])

            print(data.motion_names[choice - 1] + ''.join(format(x, "6.2f") for x in f[0::4]))

        c.fit()
        pass

for s in src:
    s.close()

print("Done")
