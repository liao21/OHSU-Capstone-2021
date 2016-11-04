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
from scenarios import mpl_nfu
from utilities import user_config, ping
from pySpacebrew.spacebrew import Spacebrew

print('starting script')

dt = 0.02
zc_thresh = 0.0
ssc_thresh = 0.0
sample_rate = 200

add_data = False
current_motion = 'Elbow Flexion' # Should match the startup page of the www trainer
motion_id = 0

vie = {}


def setup():
    global vie
    vie = mpl_nfu.setup()

    brew = Spacebrew("MPL Trainer", description="MPL Training Interface", server="192.168.1.1", port=9000)

    user_config.setup_file_logging(prefix='MPL_')

    brew.addSubscriber("Preview", "boolean")
    brew.addSubscriber("webCommand", "string")

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

    # brew.subscribe("Preview", handle_preview_boolean)
    brew.subscribe("webCommand", handle_string)

    brew.start()

    return brew


def handle_preview_boolean(value):
    if value == 'true':
        print('Start')
    else:
        print('Stop')


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


def main_loop():
    global vie, add_data, current_motion, motion_id

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


def main():
    brew = setup()

    while True:

        ip = '192.168.1.111'
        # ip = '127.0.0.1'

        logging.info('Pinging MPL at: ' + ip)
        device_ok = ping(ip)

        if device_ok:
            logging.info('Ping Success')
        else:
            logging.info('Ping Failed')

        while device_ok:
            try:
                logging.info('Starting connection to mpl:' + ip)
                main_loop()
            except KeyboardInterrupt:
                logging.info('Got Keyboard Interrupt')
                break
            except:
                logging.info('Device Disconnected')
                raise

        time.sleep(1.0)

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
