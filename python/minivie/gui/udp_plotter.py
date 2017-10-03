#
# INCOMPLETE TEST FUNCTION
#
#
# Simple plot function for showing the UDP data stream
# Requires matplotlib
#
# To run from command line:
#
# Test function can also be 'double-clicked' to start

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np
import logging
import socket
import threading
import struct
import time

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
import utilities


logger = logging.getLogger(__name__)


class UdpReceiver():
    """
        Class for receiving UDP floats

        Note the use of __private variable and threading / locks to ensure data is read safely

    """

    def __init__(self, source='//127.0.0.1:15001', num_samples=50):

        # 8 channel max for myo armband
        self.num_channels = 8
        self.num_samples = num_samples

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use get_data to access since it is thread-safe
        self.__data = np.zeros((num_samples, 8))

        # UDP Port setup
        self.addr = utilities.get_address(source)

        # Internal values
        self.__packet_count = 0
        self.__packet_time = 0.0
        self.__packet_rate = 0.0

        # Initialize connection parameters
        self.__sock = None
        self.__lock = None
        self.__thread = None

    def connect(self):
        """
            Connect to the udp server and receive UDP Packets
        """
        logger.info("Setting up Udp socket {}".format(self.addr))
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP
        self.__sock.bind(self.addr)
        self.__sock.settimeout(3.0)

        # Create thread-safe lock so that user based reading of values and thread-based
        # writing of values do not conflict
        self.__lock = threading.Lock()

        # Create a thread for processing new incoming data
        self.__thread = threading.Thread(target=self.read_packet)
        self.__thread.name = 'UdpRcv'
        self.__thread.start()

    def read_packet(self):
        """ Convert incoming bytes to emg, quaternion, accel, and ang rate """

        # Loop forever to receive data
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
                data, address = self.__sock.recvfrom(1024)
                # print('Got Packet')
            except socket.timeout:
                # the data stream has stopped.  don't break the thread, just continue to wait
                msg = "MyoUdp timed out during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.addr[0], self.addr[1], socket.timeout)
                logger.warning(msg)
                # data rate goes to zero
                self.__packet_count = 0
                self.__packet_rate = 0.0
                continue
            except socket.error:
                msg = "MyoUdp Socket Error during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.addr[0], self.addr[1], socket.error)
                logger.warning(msg)
                return

            if len(data) == 32:
                # -------------------------------------
                # Handles data from unix direct stream
                # -------------------------------------

                with self.__lock:
                    output = struct.unpack('8f', data)
                    # Populate EMG Data Buffer (newest on top)
                    self.__data = np.roll(self.__data, 1, axis=0)
                    self.__data[:1, :] = output[0:8]  # insert in first buffer entry

                    # compute data rate
                    if self.__packet_count == 0:
                        # mark time
                        self.__packet_time = time.time()
                    self.__packet_count += 1  # 2 data points per packet

                    t_now = time.time()
                    t_elapsed = t_now - self.__packet_time

                    if t_elapsed > 3.0:
                        # compute rate (every few seconds)
                        self.__packet_rate = self.__packet_count / t_elapsed
                        self.__packet_count = 0  #reset counter
            else:
                # incoming data is not of expected length
                logger.warning('Udp: Unexpected packet size. len=({})'.format(len(data)))

    def get_data(self):
        """ Return data buffer [nSamples][nChannels] """
        with self.__lock:
            return self.__data

    def get_data_rate_emg(self):
        # Return the emg data rate
        with self.__lock:
            return self.__packet_rate

    def get_status_msg(self):
        # return string formatted status message
        # with data rate and battery percentage
        # E.g. 200Hz 99%
        battery = '--'
        return '{:.0f}Hz {}%'.format(self.get_data_rate_emg(),battery)

    def close(self):
        """ Cleanup socket """
        logger.info("\n\nClosing Udp Socket @ {}".format(self.addr))
        if self.__sock is not None:
            self.__sock.close()
        if self.__thread is not None:
            self.__thread.join()


# Setup Data Source
m = UdpReceiver()
m.connect()

style.use('dark_background')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
fig.canvas.set_window_title('EMG Preview')


def animate(i):
    d = m.get_data() * 1 - 1.2

    for iChannel in range(0, 8):
        d[:, iChannel] = d[::-1, iChannel] + (1 * (iChannel + 1) )

    ax1.clear()
    ax1.plot(d)
    plt.ylim((0, 9))
    plt.xlabel('Samples')
    plt.ylabel('Channel')
    plt.title('EMG Stream')
    print('{:0.2f}'.format(m.get_data_rate_emg()))


ani = animation.FuncAnimation(fig, animate, interval=50)
plt.show()
