import keyboard
import socket
import threading
import time
import struct


class MplUdpToKeyboard(threading.Thread):

    def __init__(self, hostname="127.0.0.1", udp_telem_port=9027, udp_command_port=9028):
        threading.Thread.__init__(self)
        self.name = 'MplUdpKeyboard'

        self.udp = {'Hostname': hostname, 'TelemPort': udp_telem_port, 'CommandPort': udp_command_port}

        # create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind to any IP address at the 'Telemetry' port (the port on which percepts are received)
        self.sock.bind(('0.0.0.0', self.udp['TelemPort']))
        # set timeout in seconds
        self.sock.settimeout(0.5)
        self.run_control = True

        # Add a bail out key to terminate emulation
        keyboard.add_hotkey('esc', lambda: self.terminate())

    def terminate(self):
        print('Terminating Key Mapper')
        self.run_control = False

    def run(self):
        print('Waiting for UDP connection')
        # Loop forever to receive data via UDP
        #
        # This is a thread to receive data as soon as it arrives.
        skip_count = 0

        while self.run_control:
            # Blocking call until data received
            try:
                # receive call will error if socket closed externally (i.e. on exit)
                bytes, address = self.sock.recvfrom(1024)  # blocks until timeout or socket closed

            except socket.timeout as e:
                # the data stream has stopped.  don't break the thread, just continue to wait
                msg = "MplUdpKeyboard timed out during recvfrom() on IP={} Port={}. Error: {}".format(
                    self.udp['Hostname'], self.udp['TelemPort'], e)
                print(msg)
                continue

            except socket.error:
                # The connection has been closed
                msg = "MplUdpKeyboard Socket Closed on IP={} Port={}.".format(
                    self.udp['Hostname'], self.udp['TelemPort'])
                print(msg)
                # break so that the thread can terminate
                break

            if skip_count < 0:
                skip_count += 1
            else:
                skip_count = 0

                velocity = [0.0] * 27
                length = len(bytes)
                # print(length)
                if length == 108:
                    # Unity position command
                    # print(len(raw_chars))
                    angles = struct.unpack("27f", bytes)

                if length == 329:
                    # Vulcan X PVI command
                    values = struct.unpack("HBB81fB", bytes)
                    angles = values[3:30]
                    velocity = values[30:57]
                    impedance = values[57:84]

                if length == 221:
                    # Vulcan X PV command
                    values = struct.unpack("HBB54fB", bytes)
                    angles = values[3:30]
                    velocity = values[30:57]

                if velocity[6] > 0:
                    print('Wrist Flex')
                    keyboard.press('right')
                elif velocity[6] < 0:
                    print('Wrist Extend')
                    keyboard.press('left')
                else:
                    print('RELEASED')
                    keyboard.release('left')
                    keyboard.release('right')


def main():
    # create object and start
    # This creates the thread objects, but they don't do anything yet
    m = MplUdpToKeyboard()

    for i in reversed(range(3)):
        print('Starting in {} seconds'.format(i+1))
        time.sleep(1.0)

    # This causes each thread to do its work
    m.start()

if __name__ == "__main__":
    main()


