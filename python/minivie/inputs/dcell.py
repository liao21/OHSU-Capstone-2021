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
import os
import threading
import logging
import numpy as np
from datetime import datetime
from inputs.signal_input import SignalInput
import h5py
import serial


class DCellSerial(SignalInput):
    """
        Class for receiving DCell strain data via RS485 serial connection

    """

    def __init__(self, port='/dev/ttyUSB0', num_samples=50):

        # Initialize superclass
        super(DCellSerial, self).__init__()

        # Initialize object properties, does not actually connect to port
        self.port = port  # port name ex: 'COM4' for windows
        self.ser = None  # placeholder for pySerial object
        self.__lock = None  # thread lock
        self.__thread = None  # thread
        self.__dataStrain = np.zeros((num_samples, 1))  # strain data buffer
        self.__stream_sleep_time = 0.1

        # Set up logging
        self.enable_data_logging = False  # Enables logging data stream to disk
        # t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # self._h5filename = t + '_DCELL_LOG.hdf5'
        # self._h5file = h5py.File(self._h5filename, 'w')
        # self._h5file.close()
        self._log_counter = 1

    def connect(self, start_streaming=True):
        # Method to connect to serial port and optionally start streaming
        try:
            import serial.rs485
        except ImportError:
            logging.warning('Failed to load module: serial.rs485')

        logging.info("Setting up DCell serial comms {}".format(self.port))

        # configure the serial connections for RS485 protocol
        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            #parity=serial.PARITY_NONE,
            #stopbits=serial.STOPBITS_ONE,
            #bytesize=serial.EIGHTBITS,
            #xonxoff=False,
            #rtscts=True,
            #dsrdtr=False,
            timeout=1
        )
        self.ser.rs485_mode = serial.rs485.RS485Settings()
       
        # Check that port opened
        if self.ser.isOpen():  # Check if open
            logging.info('DCell serial port opened: ' + self.ser.name)  # Check which port was really opened
        else:
            logging.info('DCell serial port was not opened')

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
        cmd = '!001:' + command_string + '\r'
        logging.debug(cmd)
        self.ser.write(cmd.encode())
        # Every command has an output
        out = self._readline()
        return out

    def _readline(self):
        # Method to read incoming serial data, expects each output to end with EOL carriage return
        eol_byte = b'\r'  # Define carriage return bytes
        eol_string = eol_byte.decode()
        leneol_string = len(eol_string)
        line = ''
        #line = bytearray()
        #line = b''
        while True:
            c_byte = self.ser.read(1)  # Read one byte
            if c_byte:
                # line += str(c)
                c_string = c_byte.decode("ascii","replace")
                # print('byte:')
                # print(c_byte)
                # print('byte.decode("ascii","replace"):')
                # print(c_string)
                # print('byte[0]')
                # print(c_byte[0])
               
               
                line += c_string 
                if c_byte == eol_byte:  # Break once EOL, in this case carriage return, is issued
                    logging.debug('Breaking because of carriage return')
                    break
                    
            else:  # Break if nothing read back
                #time.sleep(0.05) # dcell manual says response should come within 50ms
                # timeout occurs on ser.read
                logging.debug('Breaking because nothing read back')
                break
                
        #print(line[0:-leneol])  # Return line without EOL
        return line[0:-leneol_string]  # Return line without EOL

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
            # Sleep
            time.sleep(self.__stream_sleep_time)
            # Record start time of this loop
            stream_loop_start_time = time.time()
            # Ask for strain
            data = self.send_command('SYS?')

            if data != '':  # Returns nothing if serial stream times out
                # Populate Strain Data Buffer (newest on top)
                data = float(data)
                with self.__lock:
                    self.__dataStrain = np.roll(self.__dataStrain, 1, axis=0)
                    self.__dataStrain[0] = data  # insert in first buffer entry
                self._log_data(data)

            # Update sleep time
            self._set_stream_sleep_time(stream_loop_start_time, 0.1)

    def _set_stream_sleep_time(self, stream_loop_start_time, target_dt):
        # Update loop sleep time to account for processing time
        stream_loop_time_elapsed = time.time() - stream_loop_start_time
        if stream_loop_time_elapsed < target_dt:
            self.__stream_sleep_time = target_dt - stream_loop_time_elapsed
        else:
            self.__stream_sleep_time = 0.0
            rate = 1.0/target_dt
            logging.info('DCell Running Behind {0:.2f} Hz'.format(rate))

    def get_data(self):
        # Method to return current strain buffer
        with self.__lock:
            return self.__dataStrain

    def _log_data(self, data):
        # Method to log all data values as hdf5
        # Should append to file each time
        if self.enable_data_logging:
            # Armiger 12/3/2017:  Adjusting to simple logging due to possibility of corrupt hdf5
            logging.info('DCELL: ' + str(data))

            # self._h5file = h5py.File(self._h5filename, 'r+')
            # t = datetime.now()
            # g1 = self._h5file.create_group('Log_{0:05d}'.format(self._log_counter))
            # g1.create_dataset('strain', data=[data], shape=(1, 1))
            # encoded = [a.encode('utf8') for a in str(t)]  # Need to encode strings
            # g1.create_dataset('timestamp', data=encoded, shape=(len(encoded), 1))
            # self._log_counter += 1
            # self._h5file.close()

    def close(self):
        # Method to disconnect object

        logging.info("Closing DCell comms {}".format(self.port))
        self.ser.close()
        if self.__thread is not None:
            self.__thread.join()

    def stop(self):
        self.close()


def interactive_testing(port='/dev/ttyUSB0'):
    # Method so interactively send commands and receive output
    # Useful for debugging

    print('Starting Interactive Mode\r')

    # Initialize object
    dcell = DCellSerial(port=port)
    # Connect
    dcell.connect(start_streaming=False)  # Set streaming to false as the outputs can get confused

    print('Enter your commands below.\r\nInsert "exit" to leave the application.')

    while 1:
        # get keyboard input
        t_input = input(">> ")
        if t_input == 'exit':
            dcell.close()
            exit()
        else:
            out = dcell.send_command(t_input)
            print(">>" + out)


def main():

    import argparse

    # Parameters:
    parser = argparse.ArgumentParser(description='DCell: Read from dcell and log.')
    parser.add_argument('-p', '--PORT', help='Serial Port Name (e.g. /dev/ttymxc2)',
                        default='/dev/ttymxc2')

    # other common port values
    # dev/ttyUSB0
    # COM4
    # dev/ttymxc2

    args = parser.parse_args()
    
    # Logging
    f = 'dcell-' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+ '.log'
    logging.basicConfig(filename=f, level=logging.DEBUG, format='%(asctime)s %(message)s')

    # Initialize object
    dcell = DCellSerial(port=args.PORT)
    # Connect and start streaming
    dcell.enable_data_logging = True
    dcell.connect()


if __name__ == '__main__':
    interactive_testing('/dev/ttymxc2')
    #main()
