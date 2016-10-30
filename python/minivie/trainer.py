#!/usr/bin/python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
from scenarios import mpl_nfu
from utilities import user_config
import time
from six.moves import input
import numpy as np
import pattern_rec as pr
from pySpacebrew.spacebrew import Spacebrew

brew = Spacebrew("MPL Trainer", description="MPL Training Interface", server="192.168.1.1", port=9000)

user_config.setup_file_logging(prefix='MPL_')

brew.addSubscriber("Preview", "boolean")


# Setup devices and modules
vie = mpl_nfu.setup()

dt = 0.02
zc_thresh = 0.0
ssc_thresh = 0.0
sample_rate = 200


def handlePreviewBoolean(value):
    
    if value == 'true':
        print('Start')
    else:
        print('Stop')

brew.subscribe("Preview", handlePreviewBoolean)

brew.start()

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
    for idx, val in enumerate(vie.TrainingData.motion_names):
        print("{:2d}. {} [{}]".format(idx+1, val, vie.TrainingData.get_totals(idx)))
    print(30 * '-')
    print(" 0. Exit")
    print(30 * '-')

    # Get input
    choice = input('Enter selection : ')
    assert isinstance(choice, str)  # native str on Py2 and Py3

    # Take action as per selected menu-option #
    if choice == '0':
        # exit case
        print("Exiting...")
        break
    if choice.upper() == 'P':
        # Preview data stream
        while True:
            try:
                time.sleep(0.02)  # 50Hz
                f = np.array([])
                for s in vie.SignalSource:
                    new_data = s.get_data()*0.01
                    features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
                    f = np.append(f, features)
                f = f.tolist()
                print(''.join(format(x, "6.2f") for x in f[0::4]))

            except KeyboardInterrupt:
                print('Stopping')
                break

    elif choice.upper() == 'S':
        # save
        vie.TrainingData.save()
        vie.SignalClassifier.fit()

    elif choice.upper() == 'B':
        # backup
        vie.TrainingData.copy()

    elif choice.upper() == 'X':
        # clear
        vie.TrainingData.reset()
        vie.SignalClassifier.fit()

    elif choice.upper() == 'R':
        # run classifier:

        if vie.SignalClassifier.classifier is None:
            continue

        # ##########################
        # Run the control loop
        # ##########################
        while True:
            try:
                # Fixed rate loop.  get start time, run model, get end time; delay for duration
                time_begin = time.time()

                # Run the actual model
                mpl_nfu.model(vie)

                time_end = time.time()
                time_elapsed = time_end - time_begin
                if dt > time_elapsed:
                    time.sleep(dt - time_elapsed)
                else:
                    #print("Timing Overload: {}".format(time_elapsed))
                    pass

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

        if choice < 1 or choice > len(vie.TrainingData.motion_names):
            print('Selection Out of Range')
            continue

        for i in range(100):
            time.sleep(0.02)
            f = np.array([])
            for s in vie.SignalSource:
                new_data = s.get_data()*0.01
                features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
                f = np.append(f, features)
            f = f.tolist()
            vie.TrainingData.add_data(f, choice - 1, vie.TrainingData.motion_names[choice - 1])

            print(vie.TrainingData.motion_names[choice - 1] + ''.join(format(x, "6.2f") for x in f[0::4]))

        vie.SignalClassifier.fit()
        pass

# cleanup
for s in vie.SignalSource:
    s.close()
vie.DataSink.close()

brew.stop()

print("Done")

