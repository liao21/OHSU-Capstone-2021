# -*- coding: utf-8 -*-
"""EMG Device websocket client

This module acts as a client / receiver of streaming EMG Device data via websocket.

The main class is EmgSocket, which inherits from SignalInput

Typical usage would be as follows:

    from inputs import emg_device_client
    src = emg_device_client.EmgSocket(source=ws_address, num_samples=buffer_len)
    self.SignalSource = [src]
    self.num_channels += src.num_channels
    self.futures = src.connect


    f = np.array([])
    for s in data_input:
        f = np.append(f, self.feature_extract(s.get_data()*0.01))






Packet Format
-------
The data packets follow a JSON format per the outline below:

    num_channels = 16
    num_samples = 16
    data = {
        "api_version": "X.X.X",
        "stream_batch": {
            "raw_emg": {
                "samples": [{
                    "data": np.zeros(num_channels, dtype=np.int16),
                    "timestamp_s": 0.0
                }] * num_samples,
                "batch_num": 0
            }
        }
    }

Revisions
-------
2019JAN31 Armiger: Created

"""


import asyncio
import websockets
import time
import numpy as np
import logging
from collections import deque
import json

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'inputs':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs.signal_input import SignalInput


logger = logging.getLogger(__name__)

__version__ = "1.0.0"


class EmgSocket(SignalInput):
    """Main class for creating a EMG Device Data Source Object.

        This class sets up a websocket connection after calling connect() and asynchronously
        receives new packets storing them in an internal rolling data buffer.
        When data is requested the get_data() method is called, returning the samples as a numpy style matrix

        """

    def __init__(self, source='ws://localhost:5678', num_samples=200):

        # Initialize superclass
        super(EmgSocket, self).__init__()

        # websocket address
        self.source = source

        # specify channel and sample count
        self.num_channels = 16
        self.num_samples_per_packet = 16
        self.num_samples = num_samples

        # Default data packet buffer
        self.data_buffer = deque([], maxlen=self.num_samples)

        # packet size is 16 channels by 16 samples per packet.  fill buffer with zeros
        empty_packet = self.num_channels * [0]
        for x in range(0, self.num_samples):
            self.data_buffer.append(empty_packet)

        # Internal values
        self.num_packets = 0
        self.rate = 0.0
        self.rate_counter = 0
        self.rate_last_time = time.time()

        self.status_msg = 'EMG: INITIALIZED'

    async def connect(self, port='ws://localhost:5678'):
        """
            Connect to the websocket server and begin to receive packets in background

        """

        logger.info("Setting up socket {}".format(self.source))
        while True:  # this outer loop will perpetually try to find connection
            try:
                async with websockets.connect(port) as websocket:
                    while True:  # this inner loop will perpetually check for packets
                        try:
                            msg = await websocket.recv()  # get websocket bytes
                        except websockets.exceptions.ConnectionClosed:
                            break

                        data = json.loads(msg)
                        for sample in data['stream_batch']['raw_emg']['samples']:
                            self.data_buffer.append(sample['data'])  # add data to internal buffer

                        self.num_packets += 1  # count packets received

                        # compute data rate
                        if self.rate_counter == 0:
                            # mark time
                            self.rate_last_time = time.time()
                        self.rate_counter += 1  # 2 data points per packet

                        t_now = time.time()
                        t_elapsed = t_now - self.rate_last_time
                        if t_elapsed > 3.0:
                            # compute rate (every few seconds)
                            self.rate = self.rate_counter / t_elapsed
                            self.rate_counter = 0  # reset counter

                        self.status_msg = f'EMG: {self.rate:.1f} Hz Packets: {self.num_packets}'

            except OSError:
                # OSError: Multiple exceptions: [Errno 10061] Connect call failed ('127.0.0.1', 5678),
                #                               [Errno 10061] Connect call failed ('::1', 5678, 0, 0)
                self.status_msg = f'EMG: Server not found on port {port}'
                logging.warning('No Data for EMG Device')
                await asyncio.sleep(3.0)  # wait to reconnect after a few seconds

    def get_data(self):
        """ Return data buffer of stored data [nSamples][nChannels] """
        # num_samples_per_packet = 16
        # data = np.reshape(self.data_buffer, [num_samples_per_packet*self.num_samples, self.num_channels])
        data = np.reshape(self.data_buffer, [self.num_samples, self.num_channels])
        return data

    def get_status_msg(self):
        """ Return a string status message of data source state """
        return self.status_msg

    def close(self):
        """ Cleanup socket """


def main():

    import asyncio

    print('Running')
    src = EmgSocket(source='ws://localhost:5678', num_samples=1)

    # try https://bastibe.de/2013-05-30-speeding-up-matplotlib.html
    async def display():
        while True:
            samples = (src.get_data()[0]-2047) * 0.01
            msg = 'EMG: ' + ','.join(['%4.1f' % elem for elem in samples])
            print(msg)
            await asyncio.sleep(0.01)

    loop = asyncio.get_event_loop()
    loop.create_task(display())
    loop.run_until_complete(src.connect())


if __name__ == '__main__':
    main()
