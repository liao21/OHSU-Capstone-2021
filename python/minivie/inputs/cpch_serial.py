#!/usr/bin/env python
"""
Created on Tue Jan 26 2017

Python translation of CpchSerial.m in MATLAB minivie

@author: D. Samson
Updated 3-21-17 by Connor Pyles
"""

# Before usage, do the following:
#
# install pyserial: python -m pip install pyserial
#
# make sure any connections to COM object are closed, otherwise will get permission denied error

import numpy as np
import serial
from inputs.cpc_headstage import CpcHeadstage
import time
import logging
import threading


class CpchSerial(CpcHeadstage):
    """
    Class for interfacing CPCH via serial port
    
    This class is used to interface the JHU/APL Conventional Prosthetics Control Headstage (CPCH)
    via a USB-RS485 adaptor.  The adaptor is based on the FTDI chipset and drivers for the device 
    can be found here:  
    http://www.ftdichip.com/Drivers/VCP.htm
    Note the Virtual Com Port (VCP) drivers should be used (as opposed to the D2XX Direct Drivers)
    
    Typical Baud rate for the device is 921600 bps
    """
    
    def __init__(self, port='COM5', bioamp_mask=int('0xFFFF', 16), gpi_mask=int('0x0000', 16)):
        """

        """
        
        assert type(port) is str
        assert bioamp_mask.bit_length() <= 16 and bioamp_mask >= 0  # check if 16-bit int and unsigned
        assert gpi_mask.bit_length() <= 16 and gpi_mask >= 0  # check if 16-bit int and unsigned
        
        #Initialize superclass
        super(CpchSerial, self).__init__()
        
        #public access variables
        self.serial_port = port  # Port must be capable of 921600 baud
        self.bioamp_mask = bioamp_mask
        self.gpi_mask = gpi_mask
        self.channel_ids = list(range(32))
        self.sample_frequency = 1000
        self.num_samples = 3000
        self.num_channels = 32
        
        self.enable_data_logging = False  # Enables logging data stream to disk
        
        # Gain values form normalized values
        self.gain_single_ended = 10
        self.gain_differential = 0.00489
        
        # private set access variables
        self._count_total_messages = 0
        self._count_bad_length = 0
        self._count_bad_checksum = 0
        self._count_bad_status = 0
        self._count_bad_sequence = 0
        self._count_adc_error = 0
        
        # private access variables
        self._serial_obj = None
        self._data_buffer = []  #list of bytearrays
        self._serial_buffer = bytearray([])  #bytearray
        self._prev_data_frame_id = -1
        self._bioamp_cnt = 0
        self._gpi_cnt = 0
        self._channel_mask = []
        self._start_time = time.time()
        self._is_running = False
        self.__valid_message_count = 0
        self.__valid_byte_count = 0
        self.__byte_count = 0
        self.__byte_available_count = 0
        self.__aligned_byte_count = 0
        self.__valid_message_rate = 0.0
        self.__valid_byte_rate = 0.0
        self.__byte_rate = 0.0
        self.__byte_available_rate = 0.0
        self.__aligned_byte_rate = 0.0
        self.__time_stream_reference = time.time()
        self.__stream_sleep_time = 0.02
        self._stream_duration = float("inf")

        # Initialize threading parameters
        self._stream_on_thread = True
        self.__lock = None
        self.__thread = None

    def connect(self):
        # Initialize the serial object

        bits = self.bioamp_mask.bit_length
        # max_bits = 8 if (bits > 0 and bits <= 8) else 16 if (bits > 8 and bits <= 16) else None
        max_bits = 16
        self._bioamp_cnt = bin(self.bioamp_mask).count("1")
        
        bits = self.gpi_mask.bit_length
        # max_bits = 8 if (bits > 0 and bits <= 8) else 16 if (bits > 8 and bits <= 16) else None
        max_bits = 16
        self._gpi_cnt = bin(self.gpi_mask).count("1")
        
        # buffer to hold collected data
        self._data_buffer = np.empty([3000, 32], dtype=np.double)
        
        try:
            self._serial_obj = serial.Serial(
                port=self.serial_port,
                baudrate=921600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout = 1,
                xonxoff = False,     #disable software flow control
                rtscts = False,      #disable hardware (RTS/CTS) flow control
                dsrdtr = False,      #disable hardware (DSR/DTR) flow control
                writeTimeout = 1,    #timeout for write
            )
            print('[%s] Port Opened: %s' % (__file__, self.serial_port.upper()))

        except Exception as exp:
            print('[%s] Port FAILED' % __file__)
            raise exp
            
        # Transmit STOP message in case data is flowing so the system can sanely start
        msg = self.encode_stop_msg()
        self._serial_obj.write(msg)

        while True:
            time.sleep(0.1) # delay here to ensure all bytes have time for receipt
            bytes_available = self._serial_obj.in_waiting
            if bytes_available:
                self._serial_obj.read(bytes_available)
            else:
                break

        # Get CPCH ID
        # Read param to verify the message.  Note that this must be
        # read back to ensure the message structure is correct since
        # not all channels can (or will) return data.  Unrequested channels
        # are unreturned by the system.
        msg = self.encode_config_read_msg(1)
        self._serial_obj.write(msg)
        # Check response
        r = bytearray(self._serial_obj.read(7))   #cast string to more portable bytearray
        rcnt = len(r)

        # Do this after the first read so that we can establish if any
        # response was given
        assert rcnt > 0, 'No response from CPCH. Check power, check connections'
        
        msgId = self.msg_id_configuration_read_response
        assert rcnt == 7, 'Wrong number of bytes returned. Expected [%r], received [%r]' % (rcnt , 7)
        assert r[0] == msgId, 'Bad response message id.  Expected [%r], received [%r]' % (msgId, r[0])
        assert r[1] == 1, 'Bad parameter id. Expected [%r], received [%r]'% (1, r[1])
        assert self.xor_chksum(r)[0] == 0, 'Bad checksum'
        u32_parameter = 0
        for i in reversed(r[2:5]):
            u32_parameter = (u32_parameter << 8) + i
        print('[%s] Device ID = %d' % (__file__, u32_parameter))
        
        # Reconfigure the CPCH
        # msg example: [ 4    2  255  255    0    0  249]
        # 4 = write param
        # 2 = param type 2 (active channels)
        
        # Send Request
        channel_config = (self.gpi_mask << 16) + self.bioamp_mask #bitshift(uint32(obj.GPIMask), 16) + uint32(obj.BioampMask);
        msg = self.encode_config_write_msg(2, channel_config)
        self._serial_obj.write(msg)#fwrite(obj.SerialObj, msg, 'uint8');
        
        # Check response
        r = bytearray(self._serial_obj.read(3))   #[r, rcnt] = fread(obj.SerialObj, 3, 'uint8');
        rcnt = len(r)
        
        msgId = self.msg_id_configuration_write_response
        assert rcnt == 3, 'Wrong number of bytes returned'
        assert r[0] == msgId, 'Bad response message id. Expected %d, got %d' % (msgId, r[0])
        assert (r[1] & 1) == 1,'Configuration Write Failed'
        
        # Read param to verify the message.  Note that this must be
        # read back to ensure the message structure is correct since
        # not all channels can (or will) return data.  Unrequested channels
        # are unreturned by the system.
        msg = self.encode_config_read_msg(2);
        self._serial_obj.write(msg)   #fwrite(obj.SerialObj, msg, 'uint8');
        # Check response
        r = bytearray(self._serial_obj.read(7)) #[r, rcnt] = fread(obj.SerialObj, 7, 'uint8');
        rcnt = len(r)
        
        msgId = self.msg_id_configuration_read_response
        assert rcnt == 7, 'Wrong number of bytes returned'
        assert r[0] == msgId, 'Bad response message id'
        
        frameframe_b = self.decode_msg(r, self._bioamp_cnt, self._gpi_cnt)
        
        assert frameframe_b.Mask == channel_config ,'Defined channel mask does not match returned mask. Expected: uint32[%d] Got:uint32[%d]' % (channel_config, frameframe_b.Mask)
        
        self._channel_mask = [int(i) for i in format(frameframe_b.Mask, '0' + str(self._data_buffer.shape[1]) + 'b')]

    def start(self):
        # Start the data streaming

        self._start_time = time.time()
        print('[%s] Starting CPCH with %d differential and %d single-ended inputs...' % (__file__, self._bioamp_cnt, self._gpi_cnt))

        if self._serial_obj.closed:
            self._serial_obj.open()

        if not self._serial_obj.closed:
            msg = self.encode_start_msg()

            bytes_available = self._serial_obj.in_waiting
            if bytes_available:
                self._serial_obj.read(bytes_available)

            self._serial_obj.write(msg)
            self._is_running = True

        if self._stream_on_thread:
            # Create thread-safe lock so that user based reading of values and thread-based
            # writing of values do not conflict
            self.__lock = threading.Lock()

            # Create a thread for processing new incoming data
            self.__thread = threading.Thread(target=self._stream_data)
            self.__thread.name = 'CPCHSerial'
            self.__thread.start()
        else:
            # Run without thread, mainly for profiling purposes
            self.__lock = None
            self._stream_data()

    def get_data(self, num_samples=None, idx_channel=None):
        # Return data from internal buffer

        num_samples = num_samples or self.num_samples
        idx_channel = idx_channel or self.channel_ids

        # Start device if not already running
        if self._serial_obj.closed or not self._is_running:
            self.start()

        # Return data from buffer
        data = self._data_buffer[-1*num_samples:, idx_channel]
        return data

    def _stream_data(self):
        # Loop to receive data
        start_time = time.time()
        while (time.time() - start_time) < self._stream_duration:
            # Every 20 ms should be roughly 20 messages
            time.sleep(self.__stream_sleep_time)

            # Check for new data
            num_available = self._serial_obj.in_waiting

            if num_available == 0:
                #print('No data available from serial buffer, internal buffer not updated.')
                pass
            else:
                if self._stream_on_thread:
                    with self.__lock:
                        self._read_serial_buffer()
                else:
                    self._read_serial_buffer()

    def _read_serial_buffer(self):
        # Record start time of this loop
        stream_loop_start_time = time.time()

        # Read samples from serial buffer and place in internal bufer
        # (potentially with leftover remaining bytes)
        num_available = self._serial_obj.in_waiting
        r = bytearray(self._serial_obj.read(num_available))
        raw_bytes = self._serial_buffer + r

        payload_size = 2 * (self._bioamp_cnt + self._gpi_cnt)
        msg_size = payload_size + 6

        # Align the data bytes. If all's well the first byte of the
        # remainder should be a start char which is saved for the next
        # time the buffer is read
        d = self.align_data_bytes(raw_bytes, msg_size)
        aligned_data = d['data_aligned']
        remainder_bytes = d['remainder_bytes']

        num_aligned_bytes = sum([len(x) for x in aligned_data])
        num_remainder_bytes = len(remainder_bytes)
        # DEBUG
        # print('Byte Align Fast Debug:')
        # print('Num Bytes In: ' + str(len(raw_bytes)))
        # print('Num Aligned Bytes Out: ' + str(num_aligned_bytes))
        # print('Num Remainder Bytes Out: ' + str(num_remainder_bytes))
        # print('Num Total Bytes Out: ' + str(num_aligned_bytes + num_remainder_bytes))

        # Store remaining bytes for the next read
        self._serial_buffer = remainder_bytes

        # No new data
        if not aligned_data:
            print('No aligned data available from serial buffer, internal buffer not updated.')
            self._set_stream_sleep_time(stream_loop_start_time, 0.02)
            return

        # Check validation parameters(chksum, etc)
        d = self.validate_messages(aligned_data, payload_size)
        valid_data = d['valid_data']
        error_stats = d['error_stats']

        self._count_total_messages += len(aligned_data)
        self._count_bad_checksum += error_stats['sum_bad_checksum']
        self._count_bad_status += error_stats['sum_bad_status']
        self._count_bad_sequence += error_stats['sum_bad_sequence']
        self._count_adc_error += error_stats['sum_adc_error']

        num_valid_samples = len(valid_data)
        num_valid_bytes_per_message = [len(x) for x in valid_data]
        num_valid_bytes = sum(num_valid_bytes_per_message)
        num_aligned_bytes = sum([len(x) for x in aligned_data])
        num_bytes = len(raw_bytes)

        for this_num in num_valid_bytes_per_message:
            assert msg_size == this_num

        # Extract the signals
        d = self.get_signal_data(valid_data, self._bioamp_cnt, self._gpi_cnt)
        diff_data_i16 = d['diff_data_int16']
        se_data_u16 = d['se_data_u16']

        # Perform scaling
        # Convert to numpy ndarrays
        de_data_normalized = np.array(diff_data_i16, dtype='float') * self.gain_differential
        se_data_normalized = np.array(se_data_u16, dtype='float') / 1024.0 * self.gain_single_ended

        # Send sequence data as last single ended channel
        # TODO : Need to debug with seDatacoming in. Is this only for debug purposes?

        # Log data
        if self.enable_data_logging:
            # TODO: Make Py3 compatible
            # logging.info('Raw Bytes: ' + str(float(raw_bytes[:])))
            pass

        # Update internal formatted data buffer
        # These channel mappings are updated based on the channel mask
        de_channel_idx = [int(x) for x in '{0:016b}'.format(self.bioamp_mask)] + [0] * 16
        de_channel_idx = [i for i, x in enumerate(de_channel_idx) if bool(x)]
        se_channel_idx = [0] * 16 + [int(x) for x in '{0:016b}'.format(self.gpi_mask)]
        se_channel_idx = [i for i, x in enumerate(se_channel_idx) if bool(x)]

        if num_valid_samples > self._data_buffer.shape[0]:
            # Replace entire buffer
            self._data_buffer[:, de_channel_idx] = de_data_normalized[:, -self._data_buffer.shape[0]:]
            self._data_buffer[:, se_channel_idx] = se_data_normalized[:, -self._data_buffer.shape[0]:]
        else:
            # Check for buffer overrun
            self._data_buffer = np.roll(self._data_buffer, -1 * num_valid_samples, axis=0)
            buffer_sample_idx = range(self._data_buffer.shape[0] - num_valid_samples, self._data_buffer.shape[0])
            for i, buffer_channel_idx in enumerate(de_channel_idx):
                self._data_buffer[buffer_sample_idx, buffer_channel_idx] = de_data_normalized[:, i]
            for i, buffer_channel_idx in enumerate(se_channel_idx):
                self._data_buffer[buffer_sample_idx, buffer_channel_idx] = se_data_normalized[:, i]

        # Compute data rate
        if self.__valid_message_count == 0:
            # mark time
            self.__time_stream_reference = stream_loop_start_time - self.__stream_sleep_time  # Need to account for sleep time prior to start_time measured

        self.__valid_message_count += num_valid_samples
        self.__valid_byte_count += num_valid_bytes
        self.__byte_count += num_bytes
        self.__byte_available_count += num_available
        self.__aligned_byte_count += num_aligned_bytes

        t_now = time.time()
        t_elapsed = t_now - self.__time_stream_reference

        if t_elapsed > 5.0:
            # compute rate (every second)
            self.__valid_message_rate = self.__valid_message_count / t_elapsed
            self.__valid_byte_rate = self.__valid_byte_count / t_elapsed
            self.__byte_rate = self.__byte_count / t_elapsed
            self.__byte_available_rate = self.__byte_available_count / t_elapsed
            self.__aligned_byte_rate = self.__aligned_byte_count / t_elapsed

            self.__valid_message_count = 0
            self.__valid_byte_count = 0
            self.__byte_count = 0
            self.__byte_available_count = 0
            self.__aligned_byte_count = 0

            print(
            'CPC Valid Message Rate: {0:.2f} kHz, (Expected:  1.00 kHz)'.format(self.__valid_message_rate / 1000.0))
            # print('Available Message Rate: {0:.2f} kHz'.format(self.__byte_available_rate / 1000.0))
            # print('Raw Byte Rate: {0:.2f} kHz'.format(self.__byte_rate / 1000.0))
            # print('Aligned Raw Byte Rate: {0:.2f} kHz'.format(self.__aligned_byte_rate / 1000.0))
            # print('CPC Valid Byte Rate:   {0:.2f} kHz, (Expected: 38.00 kHz)'.format(self.__valid_byte_rate / 1000.0))

        # Update sleep time
        self._set_stream_sleep_time(stream_loop_start_time, 0.02)

    def _set_stream_sleep_time(self, stream_loop_start_time, target_dt):
        # Update loop sleep time to account for processing time
        stream_loop_time_elapsed = time.time() - stream_loop_start_time
        if stream_loop_time_elapsed < target_dt:
            self.__stream_sleep_time = target_dt - stream_loop_time_elapsed
        else:
            self.__stream_sleep_time = 0.0
            rate = 1.0/target_dt
            print('CPC Running Behind {0:.2f} Hz'.format(rate))

    def close(self):
        # Method to disconnect object
        logging.info("Closing CPC Serial comms {}".format(self.serial_port))
        self._serial_obj.close()

    def stop(self):
        self.close()


def run_stream_profile():
    # Method to run profile on data streaming to determine slowest function calls
    import cProfile
    import pstats

    # Initialize object
    obj = CpchSerial()
    obj.enable_data_logging = True
    # Remove threading to allow for profiling
    obj._stream_on_thread = False
    # Set stream duration to make sure it stops streaming
    obj._stream_duration = 1.0

    # Connect
    obj.connect()

    # Run profiler
    sort_mode = 'cumulative'
    cProfile.runctx('obj.start()', globals(), locals(), 'cpc_profile')

    # Can view "snakeviz signal_viewer_profile" from terminal
    # snakeviz profile_name


def main():

    import argparse
    from datetime import datetime
    import time

    # Parameters:
    parser = argparse.ArgumentParser(description='CPCH: Read from CPCH and log.')
    parser.add_argument('-p', '--PORT', help='Serial Port Name (e.g. /dev/ttyUSB0)',
                        default='COM5')
    args = parser.parse_args()

    # Logging
    f = 'cpch-' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+ '.log'
    logging.basicConfig(filename=f, level=logging.DEBUG, format='%(asctime)s %(message)s')

    # Initialize object
    obj = CpchSerial(port=args.PORT)
    obj.enable_data_logging = True
    # Connect and start streaming
    obj.connect()
    obj.start()

    # for i in range(50):
    #     time.sleep(0.1)
    #     d = obj.get_data()
    #     print('New Data')
    #     print(d)


if __name__ == '__main__':
    main()