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
import time
import threading
from scenarios import mpl_nfu
from utilities import user_config, ping
from scenarios import Scenario
from pySpacebrew.spacebrew import Spacebrew
from mpl.nfu import NfuUdp, connection_manager
from inputs import myo
import pattern_rec as pr
from controls.plant import Plant, class_map

print('starting script')

dt = 0.02
zc_thresh = 0.0
ssc_thresh = 0.0
sample_rate = 200

add_data = False
current_motion = 'Elbow Flexion'  # Should match the startup page of the www trainer
motion_id = 0

vie = {}


def handle_string(value):
    global current_motion, add_data, motion_id
    logging.info(value)
    if value == 'A1':
        current_motion = 'Elbow Flexion'
        motion_id = 0
        add_data = False
    elif value == 'A2':
        current_motion = 'Elbow Extension'
        motion_id = 1
        add_data = False
    elif value == 'A3':
        current_motion = 'Wrist Rotate In'
        motion_id = 2
        add_data = False
    elif value == 'A4':
        current_motion = 'Wrist Rotate Out'
        motion_id = 3
        add_data = False
    elif value == 'A5':
        current_motion = 'Wrist Flex In'
        motion_id = 4
        add_data = False
    elif value == 'A6':
        current_motion = 'Wrist Extend Out'
        motion_id = 5
        add_data = False
    elif value == 'A7':
        current_motion = 'Hand Open'
        motion_id = 6
        add_data = False
    elif value == 'A8':
        current_motion = 'Spherical Grasp'
        motion_id = 7
        add_data = False
    elif value == 'A9':
        current_motion = 'No Movement'
        motion_id = 10
        add_data = False

    elif value == 'F1':
        add_data = True
    elif value == 'F2':
        add_data = False
        vie.SignalClassifier.fit()
    elif value == 'F3':
        # clear
        vie.TrainingData.reset()
        vie.SignalClassifier.fit()
    elif value == 'F4':
        vie.SignalClassifier.fit()
    elif value == 'F5':
        vie.TrainingData.copy()
        vie.TrainingData.save()
    elif value == 'F6':
        vie.TrainingData.copy()


def main():
    global vie, add_data, current_motion, motion_id

    # setup logging
    user_config.setup_file_logging(prefix='MPL_')

    # setup web interface
    brew = Spacebrew("MPL Trainer", description="MPL Training Interface", server="192.168.1.1", port=9000)
    brew.addSubscriber("webCommand", "string")
    brew.subscribe("webCommand", handle_string)
    brew.start()

    # Setup MPL scenario
    vie = Scenario()
    vie.SignalSource = [myo.MyoUdp(source='//127.0.0.1:15001'), myo.MyoUdp(source='//127.0.0.1:15002')]
    num_channels = 0
    for s in vie.SignalSource:
        s.connect()
        num_channels += 8

    # Training Data holds data labels
    # training data manager
    vie.TrainingData = pr.TrainingData()
    vie.TrainingData.load()
    vie.TrainingData.num_channels = num_channels
    vie.TrainingData.motion_names = (
        'Elbow Flexion', 'Elbow Extension',
        'Wrist Rotate In', 'Wrist Rotate Out',
        'Wrist Flex In', 'Wrist Extend Out',
        'Hand Open',
        'Spherical Grasp',
        'Tip Grasp',
        'Point Grasp',
        'No Movement',
    )

    # Classifier parameters
    vie.SignalClassifier = pr.Classifier(vie.TrainingData)
    vie.SignalClassifier.fit()

    # Plant maintains current limb state (positions) during velocity control
    filename = "../../WrRocDefaults.xml"
    vie.Plant = Plant(dt, filename)

    # Sink is output to outside world (in this case to VIE)
    # For MPL, this might be: real MPL/NFU, Virtual Arm, etc.
    # data_sink = UnityUdp()  # ("192.168.1.24")
    hostname = user_config.get_user_config_var('mplNfuIp', '192.168.1.111')
    udp_telem_port = user_config.get_user_config_var('mplNfuUdpStreamPort', 6300)
    udp_command_port = user_config.get_user_config_var('mplNfuUdpCommandPort', 6201)
    nfu = NfuUdp(hostname, udp_telem_port, udp_command_port)
    # start mpl manager as thread
    threading.Thread(target=connection_manager(nfu))
    vie.DataSink = nfu

    # ##########################
    # Run the control loop
    # ##########################
    while True:
        try:
            # Fixed rate loop.  get start time, run model, get end time; delay for duration
            time_begin = time.time()

            # Run the actual model
            f = mpl_nfu.model(vie)

            if add_data:
                vie.TrainingData.add_data(f, motion_id, current_motion)
                print(current_motion)
                # print(current_motion + )

            time_end = time.time()
            time_elapsed = time_end - time_begin
            if dt > time_elapsed:
                time.sleep(dt - time_elapsed)
            else:
                # print("Timing Overload: {}".format(time_elapsed))
                pass

        except KeyboardInterrupt:
            print('Stopping')
            break

    # cleanup
    for s in vie.SignalSource:
        s.close()
    vie.DataSink.close()

    brew.stop()

    logging.info('Done')
    print("Done")

if __name__ == '__main__':
    print('starting script')
    file = 'mpl_www_auto_run.log'
    logging.basicConfig(filename=file, level=logging.INFO, format='%(asctime)s %(message)s')
    main()
