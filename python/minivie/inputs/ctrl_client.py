import asyncio
import websockets
import time
import numpy as np
import logging
from collections import deque

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'inputs':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs.signal_input import SignalInput


logger = logging.getLogger(__name__)

__version__ = "1.0.0"


class CtrlSocket(SignalInput):

    # buffer 1 sec of data (@2000Hz)
    def __init__(self, source='ws://localhost:5678', num_samples=125):

        # Initialize superclass
        super(CtrlSocket, self).__init__()

        # logger
        self.log_handlers = None

        self.source = source

        # 16 channel max for myo armband
        self.num_channels = 16
        self.num_samples_per_packet = 16
        self.num_samples = num_samples

        # Default data packet buffer
        self.data_buffer = deque([], maxlen=self.num_samples)

        # packet size is 16 channels by 16 samples per packet.  fill buffer with zeros
        empty_packet = np.zeros(self.num_samples_per_packet*self.num_channels, dtype=np.int16)
        for x in range(0, self.num_samples):
            self.data_buffer.append(empty_packet)

        # Internal values
        self.num_packets = 0
        self.rate = 0.0
        self.rate_counter = 0
        self.rate_last_time = time.time()

        self.status_msg = 'CTRL: INITIALIZED'

    async def connect(self, port='ws://localhost:5678'):
        """
            Connect to the websocket server and receive packets

        """

        logger.info("Setting up Ctrl socket {}".format(self.source))
        while True:  # this outer loop will perpetually try to find connection
            try:
                async with websockets.connect(port) as websocket:
                    while True:  # this inner loop will perpetually check for packets
                        try:
                            msg = await websocket.recv()  # get websocket bytes
                        except websockets.exceptions.ConnectionClosed:
                            break
                        data = np.fromstring(msg, dtype=np.int16)  # convert data types
                        self.num_packets += 1  # count packets received
                        self.data_buffer.append(data)  # add data to internal buffer

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

                        self.status_msg = f'CTRL: {self.rate:.1f} Hz Packets: {self.num_packets}'

            except OSError:
                # OSError: Multiple exceptions: [Errno 10061] Connect call failed ('127.0.0.1', 5678),
                #                               [Errno 10061] Connect call failed ('::1', 5678, 0, 0)
                self.status_msg = f'CTRL: Server not found on port {port}'
                logging.warning('No Data for CTRL Device')
                await asyncio.sleep(3.0)  # wait to reconnect after a few seconds

    def get_data(self):
        """ Return data buffer [nSamples][nChannels] """
        num_samples_per_packet = 16
        data = np.reshape(self.data_buffer, [num_samples_per_packet*self.num_samples, self.num_channels])
        return data

    def get_status_msg(self):
        return self.status_msg

    def close(self):
        """ Cleanup socket """


def main():

    import asyncio

    print('Running')
    a = CtrlSocket()

    asyncio.get_event_loop().run_until_complete(a.connect())


if __name__ == '__main__':
    main()
