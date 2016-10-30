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
from pySpacebrew.spacebrew import Spacebrew

brew = Spacebrew("MPL Trainer", description="MPL Training Interface", server="sandbox.spacebrew.cc", port=9000)

user_config.setup_file_logging(prefix='MPL_')

brew.addSubscriber("Preview", "boolean")
brew.addSubscriber("webCommand", "boolean")

# Setup devices and modules
vie = mpl_nfu.setup()

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

dt = 0.02
zc_thresh = 0.0
ssc_thresh = 0.0
sample_rate = 200

add_data = True
current_motion = 'No Movement'


def handlePreviewBoolean(value):
    if value == 'true':
        print('Start')
    else:
        print('Stop')


def handle_string(value):
    global current_motion, add_data
    print(value)
    if value == 'A1':
        current_motion = 'Elbow Flexion'
    elif value == 'A2':
        current_motion = 'Elbow Extension'
    elif value == 'A9':
        current_motion = 'No Movement'
    elif value == 'F1':
        add_data = True
    elif value == 'F2':
        add_data = False
    elif value == 'F3':
        # clear
        vie.TrainingData.reset()
        vie.SignalClassifier.fit()
    elif value == 'F4':
        vie.SignalClassifier.fit()


def main_loop():
    global add_data, current_motion

    # ##########################
    # Run the control loop
    # ##########################
    while True:
        try:
            # Fixed rate loop.  get start time, run model, get end time; delay for duration
            time_begin = time.time()

            # Run the actual model
            f = mpl_nfu.model(vie)
            #
            if add_data:
                vie.TrainingData.add_data(f, 0, current_motion)
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


brew.subscribe("Preview", handlePreviewBoolean)
brew.subscribe("webCommand", handle_string)

brew.start()

# blocks until interrupt
main_loop()

# cleanup
for s in vie.SignalSource:
    s.close()
vie.DataSink.close()

brew.stop()

print("Done")
