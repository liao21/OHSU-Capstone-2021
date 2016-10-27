#!/usr/bin/python

from __future__ import with_statement  # 2.5 only
import logging
import time
import numpy as np
import utilities

__version__ = "1.0.0"


def run():

    from inputs import myo
    import pattern_rec as pr
    from controls.plant import Plant, class_map
    from mpl.nfu import NfuUdp as Sink

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
                logging.warning('Unable to classify. Error was: ' + str(e))
                break

            class_decision = data.motion_names[out]
            logging.info(class_decision)

            class_info = class_map(class_decision)

            grasp_gain = 1.2
            joint_gain = 2.2

            # Set joint velocities
            plant.new_step()
            # set the mapped class
            if class_info['IsGrasp']:
                if class_info['GraspId'] is not None:
                    plant.GraspId = class_info['GraspId']
                plant.set_grasp_velocity(class_info['Direction'] * grasp_gain)
            else:
                plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * joint_gain)

            plant.update()

            # transmit output
            data_sink.send_joint_angles(plant.JointPosition)

        except BaseException as e:
            logging.warning('Stopping mpl execution with error: ' + str(e))
            # cleanup
            for s in src:
                s.close()
            data_sink.close()
            logging.warning("Finished exception cleanup")

            raise


def main():
    while True:

        ip = '192.168.1.111'
        # ip = '127.0.0.1'

        logging.info('Pinging MPL at: ' + ip)
        device_ok = utilities.ping(ip)

        if device_ok:
            logging.info('Ping Success')
        else:
            logging.info('Ping Failed')

        while device_ok:
            try:
                logging.info('Starting connection to mpl:' + ip)
                run()
            except KeyboardInterrupt:
                logging.info('Got Keyboard Interrupt')
                break
            except:
                logging.info('Device Disconnected')
                break

        time.sleep(1.0)

    logging.info('Done')

if __name__ == '__main__':
    file = 'mpl_auto_run.log'
    logging.basicConfig(filename=file, level=logging.INFO, format='%(asctime)s %(message)s')
    main()
