#!/usr/bin/env python
"""
This module will establish RS485 serial communications with the DCell strain gauge digitizer.
The digitizer follows an ASCII Protocol: ex) !001:SGAI=123.456<CR>
    !        Framing character
    001      Station address
    :        Separator
    SGAI     Command identifier
    =        Access code
    123.456  Data
    <CR>     End of frame

Created by COP on 07FEB2017

We used USB-RS485-WE-1800-TB converter for initial testing. Make sure correct drivers are installed from:
http://www.ftdichip.com/Drivers/VCP.htm
This will install a Virtual Com Port (VBP), which you can check under device manager in Windows.

Mantracourt's "Instrument Explorer" software can be useful for debug purposes:
http://www.mantracourt.com/software/panel-mount-instrumentation/test-and-configuration-utility

Documentation for DCell including communications protocols and available commands can be found here:
http://www.mantracourt.com/products/signal-converters/digital-load-cell-converter#downloads

Example usage from python script

import dcell
import time

# Initialize object
dcell = dcell.DCellSerial(port='COM4')
# Connect and start streaming
dcell.connect()

# Query strain data every second
while True:
    strain_data = dcell.get_data()
    print('Measured Strain: ' + str(strain_data[0]) + '\n')
    time.sleep(1)


Example usage from shell

#!/bin/bash
cd /home/pi/git/minivie/python/minivie/inputs/
sudo ./dcell.py --PORT COM4 &
"""
import time
import serial
import serial.rs485
import threading
import logging
import numpy as np
from datetime import datetime

class DCellSerial(object):
    """

        Class for receiving DCell strain data via RS485 serial connection


    """
    def __init__(self, port='/dev/ttyUSB0', num_samples=50):
        # Initialize object properties, does not actually connect to port
        self.port = port  # port name ex: 'COM4' for windows
        self.ser = None  # placeholder for pySerial object
        self.__lock = None  # thread lock
        self.__thread = None  # thread
        self.__dataStrain = np.zeros((num_samples, 1))  # strain data buffer

    def connect(self, start_streaming=True):
        # Method to connect to serial port and optionally start streaming

        logging.info("Setting up DCell serial comms {}".format(self.port))

        # configure the serial connections for RS485 protocol
        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            xonxoff=False,
            rtscts=False,
            timeout=1
        )
        #self.ser.rs485_mode = serial.rs485.RS485Settings()

        # Check that port opened
        if self.ser.isOpen():  # Check if open
            print('DCell serial port opened: ' + self.ser.name + '\n')  # Check which port was really opened
        else:
            print('DCell serial port was not opened \n')

        # Set DCell default parameters
        self._set_defaults()

        # Stream unless start_streaming set to false
        # Might do this if we want to run diagnostics without bogging down communications
        if start_streaming:

            # Create threadsafe lock so that user based reading of values and thread-based
            # writing of values do not conflict
            self.__lock = threading.Lock()

            # Create a thread for processing new incoming data
            self.__thread = threading.Thread(target=self._stream_data)
            self.__thread.name = 'DCellSerRcv'
            self.__thread.start()

    def send_command(self, command_string):
        # Method to send command according to DCell ASCII protocol
        self.ser.write('!001:' + command_string + '\r')
        # Every command has an output
        out = self._readline()
        return out

    def _readline(self):
        # Method to read incoming serial data, expects each output to end with EOL carriage return
        eol = b'\r'  # Define carriage return bytes
        leneol = len(eol)
        line = ''
        while True:
            c = self.ser.read(1)  # Read one byte
            if c:
                line += c  # Append to line
                if line[-leneol:] == eol:  # Break once EOL, in this case carriage return, is issued
                    break
            else:  # Break if nothing read back
                break
        return line[0:-leneol]  # Return line without EOL

    def _set_defaults(self):
        # Set station number to 001
        self.send_command('STN=1')
        # Set baudrate to 115200
        self.send_command('BAUD=7')
        # Set sample rate to 10Hz
        self.send_command('RATE=3')
        # Reset
        self.send_command('RST')
        # Issue extra _readline to clear buffer
        self._readline()

    def _stream_data(self):
        # Loop forever to receive data
        while True:
            # Ask for current strain
            time.sleep(0.1)
            data = self.send_command('SYS?')
            with self.__lock:
                if data != '':  # Returns nothing if serial stream times out
                    # Populate Strain Data Buffer (newest on top)
                    self.__dataStrain = np.roll(self.__dataStrain, 1, axis=0)
                    self.__dataStrain[0] = float(data)  # insert in first buffer entry
                    # Logging
                    logging.info('Strain: ' + str(float(data)))

    def get_data(self):
        # Method to return current strain buffer
        with self.__lock:
            return self.__dataStrain

    def close(self):
        # Method to disconnect object

        logging.info("Closing DCell comms {}".format(self.port))
        self.ser.close()
        if self.__thread is not None:
            self.__thread.join()


def interactive_testing(port='/dev/ttyUSB0'):
    # Method so interactively send commands and receive output
    # Useful for debugging

    # Initialize object
    dcell = DCellSerial(port=port)
    # Connect
    dcell.connect(start_streaming=False)  # Set streaming to false as the outputs can get confused

    print('Enter your commands below.\r\nInsert "exit" to leave the application.')

    while 1:
        # get keyboard input
        input = raw_input(">> ")
        if input == 'exit':
            dcell.close()
            exit()
        else:
            out = dcell.send_command(input)
            print(">>" + out)


def main():

    import argparse

    # Parameters:
    parser = argparse.ArgumentParser(description='DCell: Read from dcell and log.')
    parser.add_argument('-p', '--PORT', help='Serial Port Name (e.g. /dev/ttyUSB0)',
                        default='/dev/ttyUSB0')
    args = parser.parse_args()

    # Logging
    f = 'dcell-' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+ '.log'
    logging.basicConfig(filename=f, level=logging.DEBUG, format='%(asctime)s %(message)s')

    # Initialize object
    dcell = DCellSerial(port=args.PORT)
    # Connect and start streaming
    dcell.connect()

if __name__ == '__main__':
    main()
