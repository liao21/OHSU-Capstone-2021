#!/usr/bin/python

from __future__ import with_statement  # 2.5 only
import logging
import time
import utilities
from scenarios import mpl_nfu

__version__ = "1.0.0"


def run():
    # Setup devices and modules
    vie = mpl_nfu.setup()

    dt = 0.02

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
                print("Timing Overload: {}".format(time_elapsed))

        except BaseException as e:
            logging.warning('Stopping mpl execution with error: ' + str(e))
            # cleanup
            for s in vie.SignalSource:
                s.close()
            vie.DataSink.close()
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
