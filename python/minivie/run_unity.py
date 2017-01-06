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
from utilities import user_config
from scenarios import Scenario
from mpl.unity import UnityUdp
from inputs import myo
import pattern_rec as pr
from pattern_rec.training import TrainingManagerSpacebrew
from controls.plant import Plant
import assessment


print('starting script')

dt = 0.02


def main():

    # setup logging
    user_config.setup_file_logging(prefix='VMPL_')

    # Setup MPL scenario
    vie = Scenario()

    # setup web interface
    trainer = TrainingManagerSpacebrew()
    trainer.setup(description="JHU/APL Embedded Controller", server="127.0.0.1", port=9000)
    trainer.add_message_handler(vie.command_string)

    # Setup Assessment
    tac = assessment.TargetAchievementControl(vie, trainer)
    motion_test = assessment.MotionTester(vie, trainer)
    trainer.add_message_handler(motion_test.command_string)
    trainer.add_message_handler(tac.command_string)

    # attach inputs
    vie.attach_source([myo.MyoUdp(source='//127.0.0.1:15001'), myo.MyoUdp(source='//127.0.0.1:15002')])

    # Training Data holds data labels
    # training data manager
    vie.TrainingData = pr.TrainingData()
    vie.TrainingData.load()
    vie.TrainingData.num_channels = vie.num_channels
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

    vie.FeatureExtract = pr.FeatureExtract(zc_thresh=0.05, ssc_thresh=0.05, sample_rate=200)

    # Classifier parameters
    vie.SignalClassifier = pr.Classifier(vie.TrainingData)
    vie.SignalClassifier.fit()

    # Plant maintains current limb state (positions) during velocity control
    filename = "../../WrRocDefaults.xml"
    vie.Plant = Plant(dt, filename)

    # Sink is output to outside world (in this case to VIE)
    # For MPL, this might be: real MPL/NFU, Virtual Arm, etc.
    vmpl = UnityUdp(remote_host="127.0.0.1")  # ("192.168.1.24")
    vie.DataSink = vmpl

    # ##########################
    # Run the control loop
    # ##########################
    time_elapsed = 0.0
    while True:
        try:
            # Fixed rate loop.  get start time, run model, get end time; delay for duration
            time_begin = time.time()

            # Run the actual model
            output = vie.update()

            trainer.send_message("strStatus", 'V=' + vmpl.get_voltage() + ' ' + output['status'])
            trainer.send_message("strOutputMotion", output['decision'])

            msg = '{} [{:.0f}]'.format(vie.training_motion, round(vie.TrainingData.get_totals(vie.training_id), -1))
            trainer.send_message("strTrainingMotion", msg)

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
    vie.close()
    trainer.close()
    logging.info('Done')

if __name__ == '__main__':
    main()
