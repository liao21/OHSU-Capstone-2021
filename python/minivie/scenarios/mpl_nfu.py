"""
Created on Tue Jan 23 10:17:58 2016

Initial pass at simulating MiniVIE processing using python so that this runs on an embedded device

@author: R. Armiger
"""

import sys
import logging
from utilities import user_config
import time
import numpy as np
from inputs import myo
import pattern_rec as pr
from mpl.nfu import NfuUdp as Sink
from controls.plant import Plant, class_map
from scenarios import Scenario

dt = 0.02  # seconds per loop.  50Hz update
zc_thresh = 0.0
ssc_thresh = 0.0
sample_rate = 200


def setup():
    """
    Create the building blocks of the MiniVIE

        SignalSource - source of EMG data
        SignalClassifier - algorithm to classify emg into 'intent'
        Plant - Perform forward integration and apply joint limits
        DataSink - output destination of command signals (e.g. real or virtual arm)
    """

    vie = Scenario()

    filename = "../../WrRocDefaults.xml"
    # Create data objects

    # Signal Source get external bio-signal data
    # For MPL, this might be CPC Headstage, External Signal Acquisition, MyoBand, etc.
    # input (emg) device
    # select either 1 or 2 myo bands
    vie.SignalSource = [myo.MyoUdp(source='//127.0.0.1:15001'), myo.MyoUdp(source='//127.0.0.1:15002')]
    # src = [myo.MyoUdp(source='//127.0.0.1:15001')]
    num_channels = 0
    for s in vie.SignalSource:
        s.connect()
        num_channels += 8

    # Training Data holds data labels
    # training data manager
    vie.TrainingData = pr.TrainingData()
    vie.TrainingData.load()
    vie.TrainingData.num_channels = num_channels

    # Classifier parameters
    vie.SignalClassifier = pr.Classifier(vie.TrainingData)
    vie.SignalClassifier.fit()

    # Plant maintains current limb state (positions) during velocity control
    vie.Plant = Plant(dt, filename)

    # Sink is output to outside world (in this case to VIE)
    # For MPL, this might be: real MPL/NFU, Virtual Arm, etc.
    # data_sink = UnityUdp()  # ("192.168.1.24")
    vie.DataSink = Sink()
    vie.DataSink.connect()

    return vie


def model(vie):
    # Get features from emg data
    f = np.array([])
    for s in vie.SignalSource:
        new_data = s.get_data() * 0.01
        features = pr.feature_extract(new_data, zc_thresh, ssc_thresh, sample_rate)
        f = np.append(f, features)
    f_out = f.tolist()

    # format the data in a way that sklearn wants it
    f = np.squeeze(f)
    f = f.reshape(1, -1)

    if vie.SignalClassifier.classifier is None:
        print('Untrained')
        return f_out

    try:
        out = int(vie.SignalClassifier.classifier.predict(f))
    except ValueError as e:
        logging.warning('Unable to classify. Error was: ' + str(e))
        return f_out

    class_decision = vie.TrainingData.motion_names[out]
    print(class_decision)

    class_info = class_map(class_decision)

    grasp_gain = 1.4
    joint_gain = 1.4

    # Set joint velocities
    vie.Plant.new_step()

    # set the mapped class
    if class_info['IsGrasp']:
        if class_info['GraspId'] is not None:
            vie.Plant.GraspId = class_info['GraspId']
        vie.Plant.set_grasp_velocity(class_info['Direction'] * grasp_gain)
    else:
        vie.Plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * joint_gain)

    vie.Plant.update()

    # transmit output
    vie.DataSink.send_joint_angles(vie.Plant.JointPosition)

    return f_out


def main():
    """ Main function that involves setting up devices,
        looping at a fixed time interval, and performing cleanup
    """

    vie = setup()

    # setup main loop control
    print("")
    print("Running...")
    print("")
    sys.stdout.flush()

    while True:  # main loop
        try:
            # Fixed rate loop.  get start time, run model, get end time; delay for duration
            time_begin = time.time()

            # Run the actual model
            model(vie)

            time_end = time.time()
            time_elapsed = time_end - time_begin
            if dt > time_elapsed:
                time.sleep(dt - time_elapsed)
            else:
                print("Timing Overload")
        except KeyboardInterrupt:
            print('Stopping')
            break

        finally:
            print("")
            # print("EMG Buffer:")
            # print(hMyo.getData())
            print("Last time_elapsed was: ", time_elapsed)
            print("")
            print("Cleaning up...")
            print("")

            for s in vie.SignalSource:
                s.close()
            vie.DataSink.close()

if __name__ == "__main__":
    user_config.setup_file_logging(prefix='MPL_')
    main()
