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
    global vie, current_motion, add_data, motion_id

    # Commands should come in with colon operator
    # e.g. Cmd:Add or Cls:Elbow Flexion
    logging.info('Received New Spacebrew command:' + value)

    parsed = value.split(':')
    if not len(parsed) == 2:
        logging.warning('Invalid Command: ' + value)
        return
    else:
        cmd_type = parsed[0]
        cmd_data = parsed[1]

    if cmd_type == 'Cls':
        # Parse a Class Message
        current_motion = cmd_data
        motion_id = vie.TrainingData.motion_names.index(cmd_data)
        add_data = False

    elif cmd_type == 'Cmd':
        if cmd_data == 'Add':
            add_data = True
        elif cmd_data == 'Stop':
            add_data = False
            vie.SignalClassifier.fit()
        elif cmd_data == 'ClearClass':
            vie.TrainingData.clear(motion_id)
            vie.SignalClassifier.fit()
        elif cmd_data == 'ClearAll':
            vie.TrainingData.reset()
            vie.SignalClassifier.fit()
        elif cmd_data == 'Train':
            vie.SignalClassifier.fit()
        elif cmd_data == 'Save':
            vie.TrainingData.copy()
            vie.TrainingData.save()
        elif cmd_data == 'Backup':
            vie.TrainingData.copy()
        elif cmd_data == 'Pause':
            vie.pause()
        elif cmd_data == 'SpeedUp':
            vie.gain(1.2)
        elif cmd_data == 'SpeedDown':
            vie.gain(0.8)
        else:
            logging.warning('Unknown Command: ' + cmd_type)


def main():
    global vie, add_data, current_motion, motion_id

    # setup logging
    user_config.setup_file_logging(prefix='MPL_')

    # setup web interface
    brew = Spacebrew("MPL Trainer", description="MPL Training Interface", server="192.168.1.1", port=9000)
    brew.addSubscriber("strCommand", "string")
    brew.addPublisher("strStatus", "string")
    brew.addPublisher("strTrainingMotion", "string")
    brew.addPublisher("strOutputMotion", "string")
    brew.subscribe("strCommand", handle_string)
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
    # print('***starting MPL connection Thread')
    t = threading.Thread(name='MPLNFU',target=connection_manager, args=(nfu,))
    # print('***finished starting MPL connection Thread')
    t.setDaemon(True)
    t.start()
    vie.DataSink = nfu

    # ##########################
    # Run the control loop
    # ##########################
    str_status = ''
    str_training_motion = ''
    str_output_motion = ''

    while True:
        try:
            # Fixed rate loop.  get start time, run model, get end time; delay for duration
            time_begin = time.time()

            # Run the actual model
            output = mpl_nfu.model(vie)

            if add_data:
                vie.TrainingData.add_data(output['features'], motion_id, current_motion)

            msg = 'V=' + nfu.get_voltage() + ' ' + output['status']
            if not str_status == msg:
                brew.publish("strStatus", msg)
                str_status = msg
            msg = '{} [{:.0f}]'.format(current_motion, round(vie.TrainingData.get_totals(motion_id),-1))
            if not str_training_motion == msg:
                brew.publish("strTrainingMotion", msg)
                str_training_motion = msg
            if not str_output_motion == output['decision']:
                brew.publish("strOutputMotion", output['decision'])
                str_output_motion = output['decision']

            time_end = time.time()
            time_elapsed = time_end - time_begin
            if dt > time_elapsed:
                time.sleep(dt - time_elapsed)
            else:
                # print("Timing Overload: {}".format(time_elapsed))
                pass

        except KeyboardInterrupt:
            break

    # cleanup
    for s in vie.SignalSource:
        s.close()
    vie.DataSink.close()

    brew.stop()

    logging.info('Done')

if __name__ == '__main__':
    file = 'mpl_www_auto_run.log'
    logging.basicConfig(filename=file, level=logging.INFO, format='%(asctime)s %(message)s')
    main()
