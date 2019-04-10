import threading
import socket
import logging
import time
from urllib.parse import urlparse


class Udp(threading.Thread):
    # Basic Template for thread based udp communications
    #
    # key function is the onmessage attribute that is called on data receive

    def __init__(self, local_address='//0.0.0.0:9027', remote_address='//127.0.0.1:9028'):

        threading.Thread.__init__(self)
        self.run_control = False  # Used by the start and terminate to control thread
        self.read_buffer_size = 1024
        self.sock = None

        remote_hostname, remote_port = get_address(remote_address)
        local_hostname, local_port = get_address(local_address)
        self.udp = {'RemoteHostname': remote_hostname, 'RemotePort': remote_port,
                    'LocalHostname': local_hostname, 'LocalPort': local_port}

        self.is_data_received = False
        self.is_connected = False
        self.timeout = 3.0

        # default callback is just the print function.  this can be overwritten. also for i in callbacks??
        self.onmessage = lambda s: 1 + 1
        # self.onmessage = print
        pass

    def connect(self):
        logging.info("{} local port: {}:{}".format(self.name, self.udp['LocalHostname'], self.udp['LocalPort']))
        logging.info("{} remote port: {}:{}".format(self.name, self.udp['RemoteHostname'], self.udp['RemotePort']))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Enable broadcasting
        self.sock.bind((self.udp['LocalHostname'], self.udp['LocalPort']))
        self.sock.settimeout(self.timeout)
        self.is_connected = True

        # Create a thread for processing new data
        if not self.isAlive():
            logging.info('Starting thread: {}'.format(self.name))
            self.start()

    def terminate(self):
        logging.info('Terminating receive thread: {}'.format(self.name))
        self.run_control = False

    def on_connection_lost(self):
        msg = "{} timed out during recvfrom() on IP={} Port={}".format(
            self.name, self.udp['LocalHostname'], self.udp['LocalPort'])
        logging.warning(msg)
        logging.info('{} Connection is Lost'.format(self.name))

    def run(self):
        # Loop forever to receive data via UDP
        #
        # This is a thread to receive data as soon as it arrives.

        if not self.is_connected:
            logging.error("Socket is not connected")
            return

        self.run_control = True

        while self.run_control:
            # Blocking call until data received
            try:
                # receive call will error if socket closed externally (i.e. on exit)
                # blocks until timeout or socket closed
                data_bytes, address = self.sock.recvfrom(self.read_buffer_size)

                # if the above function returns (without error) it means we have a connection
                if not self.is_data_received:
                    logging.info('{} Connection is Active: Data received'.format(self.name))
                    self.is_data_received = True

            except socket.timeout:
                # the data stream has stopped.  don't break the thread, just continue to wait
                self.is_data_received = False
                self.on_connection_lost()
                continue

            except socket.error:
                # The connection has been closed
                msg = "{} Socket Closed on IP={} Port={}.".format(
                    self.name, self.udp['LocalHostname'], self.udp['LocalPort'])
                logging.info(msg)
                # break so that the thread can terminate
                self.run_control = False
                break

            # Execute the callback function assigned to self.onmessage
            self.onmessage(data_bytes)

    def send(self, msg_bytes, address=None):
        """
        Send msg_bytes to remote host using either the established parameters stored as properties, or those
        parameters provided to the function call
        :param msg_bytes:
            encoded message bytes to be sent via socket
        :param address:
            address is a tuple (host, port)
        :return:
            None
        """

        address = address if address is not None else (self.udp['RemoteHostname'], self.udp['RemotePort'])

        if self.is_connected:
            self.sock.sendto(msg_bytes, address)
        else:
            logging.warning('Socket disconnected')

    def close(self):
        """
            Cleanup socket
            close the socket
            disable the run control loop and join receive thread to main

        :return:
            None
        """
        self.run_control = False
        if self.sock is not None:
            logging.info("{} Closing Socket IP={} Port={} to IP={} Port={}".format(
                self.name, self.udp['LocalHostname'], self.udp['LocalPort'],
                self.udp['RemoteHostname'], self.udp['RemotePort']))
            self.sock.close()
        self.join()


class FixedRateLoop(object):
    """
    A class for creating a fixed rate loop that compensates for function execution time.

    Revisions:
        2018FEB16 Armiger: Created
    """

    def __init__(self, dt):
        self.dt = dt
        self.enabled = True

    def loop(self, loop_function):
        """Runs the function provided at fixed rate. This is a blocking call"""

        time_elapsed = 0.0
        while self.enabled:
            try:
                # Fixed rate loop.  get start time, run model, get end time; delay for duration
                time_begin = time.time()

                # run the fixed rate function
                loop_function()

                time_end = time.time()
                time_elapsed = time_end - time_begin
                if self.dt > time_elapsed:
                    time.sleep(self.dt - time_elapsed)

                # print('{0} dt={1:6.3f}'.format(output['decision'], time_elapsed))

            except KeyboardInterrupt:
                break

        print("")
        print("Last time_elapsed was: ", time_elapsed)
        print("")
        print("Terminating loop...")
        print("")


def get_address(url):
    """
    convert address url string to get hostname and port as tuple for socket interface
    error checking port is native to urlparse

       # E.g. //127.0.0.1:1234 becomes:
       hostname = 127.0.0.1
       port = 1234

    :param url:
        url string in format '//0.0.0.0:80'
    :return:
        tuple of (hostname, port)
    """
    a = urlparse(url)

    return a.hostname, a.port
