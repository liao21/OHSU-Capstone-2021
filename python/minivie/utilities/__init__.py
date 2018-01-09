import os
import six
import threading
import socket
import logging


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
                bytes, address = self.sock.recvfrom(self.read_buffer_size)

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
            self.onmessage(bytes)

    def send(self, msg_bytes):
        if self.is_connected:
            self.sock.sendto(msg_bytes, (self.udp['RemoteHostname'], self.udp['RemotePort']))
        else:
            logging.warning('Socket disconnected')

    def close(self):
        """ Cleanup socket """
        self.run_control = False
        if self.sock is not None:
            logging.info("{} Closing Socket IP={} Port={} to IP={} Port={}".format(
                self.name, self.udp['LocalHostname'], self.udp['LocalPort'],
                self.udp['RemoteHostname'], self.udp['RemotePort']))
            self.sock.close()
        self.join()


def ping(host):
    """
    Returns True if host responds to a ping request
    """
    import platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"

    # Ping
    return os.system("ping " + ping_str + " " + host) == 0


def get_address(url):
    # convert address url string to get hostname and port as tuple for socket interface
    # error checking is centralized here
    #
    # E.g. //127.0.0.1:1234 becomes:
    #   hostname = 127.0.0.1
    #   port = 1234
    a = six.moves.urllib.parse.urlparse(url)

    assert isinstance(a.hostname, six.string_types), "hostname is not a string: %r" % a.hostname
    assert isinstance(a.port, six.integer_types), "port is not an integer: %r" % a.port
    return a.hostname, a.port


def restart_myo(unused):
    # Use this function to issue a restart command on the myo services.
    # Note this gets trickier when primary/back myo bands are used.
    # first check if the service is active, only then issue restart
    os.system("sudo systemctl is-enabled mpl_myo1.service | grep 'enabled' > /dev/null && sudo systemctl stop mpl_myo1.service && sleep 3 && sudo systemctl start mpl_myo1.service")
    os.system("sudo systemctl is-enabled mpl_myo2.service | grep 'enabled' > /dev/null && sudo systemctl stop mpl_myo2.service && sleep 3 && sudo systemctl start mpl_myo2.service")


def change_myo(val):
    # Use this command to change the active pair of myos searched during startup
    # This is accomplished by stopping/disabling and enabling/starting the respective services
    # Set one is mpl_myo1
    # Set two is mpl_myo2

    if val == 1:
        os.system("sudo systemctl stop mpl_myo2.service")
        os.system("sudo systemctl disable mpl_myo2.service")
        os.system("sudo systemctl enable mpl_myo1.service")
        os.system("sudo systemctl start mpl_myo1.service")
    elif val == 2:
        os.system("sudo systemctl stop mpl_myo1.service")
        os.system("sudo systemctl disable mpl_myo1.service")
        os.system("sudo systemctl enable mpl_myo2.service")
        os.system("sudo systemctl start mpl_myo2.service")


def reboot():
    os.system("sudo shutdown -r now")


def shutdown():
    # os.system("sudo shutdown -h now")
    # TODO: This isn't a great strategy for issuing low battery warning, but it works
    import socket
    import time
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # Issue vibrate command for myo listenting on this port
        s.sendto(bytearray([1]), ('localhost', 16001))
        time.sleep(0.5)
        s.sendto(bytearray([1]), ('localhost', 16001))
        time.sleep(0.5)
        s.sendto(bytearray([1]), ('localhost', 16001))
        time.sleep(5)
