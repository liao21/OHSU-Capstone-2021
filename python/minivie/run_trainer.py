#!/usr/bin/env python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
import scenarios
from utilities import user_config
import time
import numpy as np
import pattern_rec as pr
from mpl.open_nfu import NfuUdp

user_config.setup_file_logging(prefix='MPL_')

# Setup devices and modules
vie = mpl_nfu.setup()
vie.DataSink.close()
# Replace sink with actual arm
hSink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
#t = threading.Thread(name='MPLNFU', target=connection_manager, args=(hSink,))
#t.setDaemon(True)
#t.start()
hSink.connect()
vie.DataSink = hSink


dt = 0.02
zc_thresh = 0.05
ssc_thresh = 0.05
sample_rate = 200

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
                time.sleep(dt)  # 50Hz
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

        mpl_nfu.run(vie)

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
            time.sleep(dt)

            # Get features from emg data
            f = np.array([])
            imu = np.array([])
            for s in vie.SignalSource:
                new_data = s.get_data()*0.01
                features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
                f = np.append(f, features)
            for s in vie.SignalSource:
                result = s.get_imu()
                imu = np.append(imu, result['quat'])
                imu = np.append(imu, result['accel'])
                imu = np.append(imu, result['gyro'])
                # add imu to features
                #f = np.append(f, imu)
            f = f.tolist()
            vie.TrainingData.add_data(f, choice - 1, vie.TrainingData.motion_names[choice - 1],imu)

            print(vie.TrainingData.motion_names[choice - 1] + ''.join(format(x, "6.2f") for x in f[0::4]))

        vie.SignalClassifier.fit()
        pass

# cleanup
vie.close()

print("Done")
