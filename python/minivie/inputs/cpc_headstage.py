"""
Created on Tue Jan 26 2017

Python translation of CpcHeadstage.m in MATLAB minivie

@author: D. Samson
Updated 3-21-17 by Connor Pyles
"""

import struct
import sys
import numpy as np
from operator import xor


class CpcHeadstage(object):
    """
    # Base class for CPCH
    # Contains methods for creating and parsing messages
    # as well as parsing streaming data
    # 14Mar2012 Armiger: Created
    # 15Jan2013 Armiger: Updated signal parsing to search for only start
    # characters ('128') since start sequence [128 0 0] cannot be relied
    # upon if transmission errors occur
    """
    
    def __init__(self):
        self.msg_id_start_streaming = 1
        self.msg_id_stop_streaming = 2
        self.msg_id_status_request = 3
        self.msg_id_configuration_write = 4
        self.msg_id_configuration_read = 5
        self.msg_id_cpc_data = 128
        self.msg_id_stop_streaming_response = 129
        self.msg_id_status_data = 130
        self.msg_id_configuration_read_response = 131
        self.msg_id_configuration_write_response = 132
        self.crc_table = self._cpch_crc_gen()
    
    def encode_start_msg(self):
        msg = bytearray()
        msg += struct.pack('B', 1)
        msg += struct.pack('B', self.xor_chksum(msg)[0])
        return msg

    def encode_stop_msg(self):
        msg = bytearray()
        msg += struct.pack('B', 2)
        msg += struct.pack('B', self.xor_chksum(msg)[0])
        return msg

    def encode_status_msg(self):
        msg = bytearray()
        msg += struct.pack('B', 3)
        msg += struct.pack('B', self.xor_chksum(msg)[0])
        return msg

    def xor_chksum(self, msg):
        """
        XOR checksum of msg (using 0xA6 default polynomial?)
        
        Input Arguments:
        msg -- bytearray to be checksummed
        poly -- integer of taps in the polynomial
        
        Return Arguments:
        r -- 0 when good checksum

        Modified 3/15/17 by COP to handle lists of messages
        """
        
        assert type(msg) is bytearray or type(msg) is list

        # Put msg into list if passed as bytearray
        if type(msg) is bytearray:
            msg = [msg]
        # Let's convert to ndarray to speed things up
        msg = np.transpose(np.array(msg, dtype = np.uint8))

        r = np.array([0]*msg.shape[1], dtype=np.uint8)
        for byte_idx in range(msg.shape[0]):
            msg_row = msg[byte_idx, :]
            xor_result = np.bitwise_xor(r, msg_row)
            r_new = [self.crc_table[int(x)] for x in xor_result]
            r[:] = r_new

        return r

    @staticmethod
    def _cpch_crc_gen():
        t = [CpcHeadstage._p_cpch_crc_gen(k) for k in range(256)]
        return t

    @staticmethod
    def _p_cpch_crc_gen(package, poly='101001101'):
        # Convert package from integer to bytes
        x = "{0:08b}".format(package)
        # Add 1s
        x += '1'*8
        # Put in lists so they are mutable
        x = list(x)
        poly = list(poly)

        # Calculate xr
        xr = x[0:9]
        for k in range(len(x)-8):
            if xr[0] == poly[0]:
                xr = [str(xor(int(xr[idx]), int(poly[idx]))) for idx, bit in enumerate(xr)]

            xr[0:8] = xr[1:9]

            if k < len(x) - 9:
                xr[8] = x[k+9]

        not_xr = [not int(x) for x in xr]
        not_xr = [str(int(x)) for x in not_xr]
        r = int(''.join(not_xr[0:8]), 2)
        return r
        
    def encode_config_read_msg(self, indx):
        msg = bytearray()
        msg = msg + struct.pack('B',5)
        msg = msg + struct.pack('B',indx)
        msg = msg + struct.pack('B', self.xor_chksum(msg)[0])
        return msg
    
    def encode_config_write_msg(self, indx, payload):
            endian = sys.byteorder  #[~, ~, endian] = computer()
            
            msg = bytearray()
            msg = msg + struct.pack('B',4)
            msg = msg + struct.pack('B',indx)
            
            if (endian == 'big'):
                msg = msg + struct.pack('<I', payload)  #msg(3:6) = typecast(swapbytes(uint32(payload)), 'uint8')
            else:
                msg = msg + struct.pack('I', payload)   #msg(3:6) = typecast(uint32(payload), 'uint8')
            
            msg = msg + struct.pack('B', self.xor_chksum(msg)[0])
            return msg

    @staticmethod
    def decode_msg(msg, diff_cnt, se_cnt):
            endian = sys.byteorder  #[~, ~, endian] = computer();
            
            msgx = bytearray(msg)
            
            frame = type('Frame', (object, ), {})() #generate object to hold frame data
            
            frame.Type = msgx[0]
            
            if msg[0] == 128:       # 1KHz CPCH Data Stream
                frame.Status.Comm_Err_Cnt = msgx[1]
                frame.Status.Msd_ID_Err = ((msgx[2] >> 0) & 1) != 0
                frame.Status.Chksum_Err = ((msgx[2] >> 1) & 1) != 0
                frame.Status.Length_Err = ((msgx[2] >> 3) & 1) != 0
                frame.Status.ADC_Err = ((msgx[2] >> 7) & 1) != 0
                
                frame.Sequence = msg[3]
                frame.DataBytes = msg[4]
                #######NEED TO ACTUALLY BE SENDING DATA BEFORE THIS CAN BE TRANSLATED TO PYTHON########
                #######THIS SECTION IS STILL USING MATLAB SYNTAX#######
                # de = typecast(msgx(6:(6 + 2*diffCnt - 1)), 'int16')
                # se = typecast(msgx((6+2*diffCnt):((6+2*diffCnt) + 2*seCnt - 1)), 'uint16')
                
                # if (endian == 'B'):
                    # de = swapbytes(de)
                    # se = swapbytes(se)
                
                # EMG_GAIN = 50  #TODO abstract
                # frame.DiffData = EMG_GAIN * double(de) ./ 512
                # frame.SEData = double(se) ./ 1024
                
            elif msg[0] == 129:        # Async. Stop Sream Response
                frame = []  # Contains no data, only ID & Chksum
                
            elif msg[0] == 130:        # Async. Status Response
                frame.Status.Comm_Err_Cnt = msgx[1]
                frame.Status.Msd_ID_Err = ((msgx[2] >> 0) & 1) != 0 #(bitget(msgx(3), 1)) ~= 0
                frame.Status.Chksum_Err = ((msgx[2] >> 1) & 1) != 0 #(bitget(msgx(3), 2)) ~= 0
                frame.Status.Length_Err = ((msgx[2] >> 2) & 1) != 0 #(bitget(msgx(3), 3)) ~= 0
                frame.Status.ADC_Err = ((msgx[2] >> 3) & 1) != 0 #(bitget(msgx(3), 4)) ~= 0
                
            elif msg[0] == 131:        # Async. Config Read Response
                frame.ID = msgx[1]
                    
                m = 0
                for i in reversed(msgx[2:-1]):
                    m = (m << 8) + i
                
                if (endian == 'big'):
                    m = struct.unpack("<I", struct.pack(">I", m))[0]
                
                frame.Mask = m
                
                
                
            elif msg[0] == 132:       # Async. Config Write Response
                frame.Success = ((msgx[2] >> 0) & 1) != 0 #(bitget(msgx(3), 1)) ~= 0
                
            else:
                print('Unkonwn message id: %d',msg(1))
            
            
            return frame

    def align_data_bytes(self, data_stream, msg_size):
        d = self.byte_align_fast(data_stream, msg_size)
        return d

    @staticmethod
    def byte_align_fast(data_stream, msg_size):

        # Find all start chars ('128') and index the next set of bytes
        # off of these starts.  This could lead to overlapping data
        # but valid data will be verified using the checksum
        byte_pattern = [128, 0, 0]
        idx_start_bytes = [i for i, x in enumerate(data_stream) if x == 128]

        if not idx_start_bytes:
            print('No start sequence [' + ' '.join(str(x) for x in byte_pattern) + '] found in data stream of length %d.  Try resetting CPCH' % (len(data_stream)))

        # Check if there are too few bytes between the last start
        # character and the end of the buffer
        idx_start_bytes_in_range = [x for x in idx_start_bytes if x <= len(data_stream) - msg_size]
        if not idx_start_bytes_in_range:
            # No full messages found
            d = {'data_aligned':  [], 'remainder_bytes': data_stream}
            return d

        # Check start bytes to make sure they are separated by correct message size
        check_msg_sizes = True
        while check_msg_sizes:
            for i, this_start_idx in enumerate(idx_start_bytes_in_range):
                if i == len(idx_start_bytes_in_range) - 1:
                    check_msg_sizes = False  # All msg sizes checked
                    continue
                if not (idx_start_bytes_in_range[i+1] - this_start_idx) == msg_size:
                    del idx_start_bytes_in_range[i+1]
                    break  # break for loop to re-enter again now that start byte list has been modified

        remainder_bytes = data_stream[idx_start_bytes_in_range[-1] + msg_size:]

        # Align the data based on the validated start characters
        data_aligned = []
        for i in idx_start_bytes_in_range:
            data_aligned.append(data_stream[i: i + msg_size])

        # Return data
        d = {'data_aligned': data_aligned, 'remainder_bytes': remainder_bytes}
        return d

    def validate_messages(self, aligned_data, expected_length):
        """
        Validate a matrix of messages using a criteria of checksum,
        appropriate message length, and status bytes

        Aligned data should be a list of length = numMessages,
        with each element being bytearray of length = numBytesPerMessage
        """

        # Compute CRC
        computed_checksum = self.xor_chksum(aligned_data)

        # Find validated data by ensuring it is the correct length and has correct checksum
        # Status byte upper four bits are set to zero
        is_valid_status_byte = [not(x[2] & 240) for x in aligned_data]
        is_adc_error = [bool(int('{0:08b}'.format(x[2])[3])) for x in aligned_data]
        is_valid_length = [x[4] == expected_length for x in aligned_data]
        is_valid_checksum = [not bool(x) for x in computed_checksum]
        is_valid_data = [a and b and c for a, b, c in zip(is_valid_checksum, is_valid_length, is_valid_status_byte)]
        #is_valid_data = is_valid_checksum and is_valid_length and is_valid_status_byte

        valid_data = [x for i, x in enumerate(aligned_data) if is_valid_data[i]]

        # No valid data in packet
        if not valid_data:
            return

        # Check sequence bytes in batch operation
        sequence_row = [float(x[3]) for x in valid_data]
        # print(sequence_row)
        sequence_expected = [(x + sequence_row[0]) % 256 for x in range(len(valid_data))]
        is_valid_sequence = [(sequence_expected[i] - sequence_row[i]) == 0.0 for i, x in enumerate(sequence_row)]

        sum_bad_status = is_valid_status_byte.count(False)
        sum_bad_length = is_valid_length.count(False)
        sum_bad_checksum = is_valid_checksum.count(False)
        sum_bad_sequence = is_valid_sequence.count(False)
        sum_adc_error = is_adc_error.count(True)

        error_stats = {'sum_bad_status': sum_bad_status, 'sum_bad_length': sum_bad_length, 'sum_bad_checksum': sum_bad_checksum, 'sum_bad_sequence': sum_bad_sequence, 'sum_adc_error': sum_adc_error}
        d = {'valid_data': valid_data, 'error_stats': error_stats}
        return d

    @staticmethod
    def get_signal_data(valid_data, diff_cnt, se_cnt):
        # Typecast the data to the appropriate data size

        # Get data size
        num_valid_samples = len(valid_data)

        # Convert the valid data to Int16int
        payload_idx_start = 5
        payload_idx_end = payload_idx_start + 2 * diff_cnt # Diff data starts after header
        de_data_u8 = [x[payload_idx_start:payload_idx_end] for x in valid_data]
        string_num_int16 = str(int((payload_idx_end - payload_idx_start)/2))

        diff_data_int16 = []
        for x in de_data_u8:
            # print('DE Message: ' + str(x))
            new_val = struct.unpack(string_num_int16 + 'h', x)
            # print('DE Converted: ' + str(new_val))
            diff_data_int16.append(new_val)

        payload_idx_start = 5 + 2 * diff_cnt  # se data starts after diff data
        payload_idx_end = payload_idx_start + 2 * se_cnt

        se_data_u8 = [x[payload_idx_start:payload_idx_end] for x in valid_data]
        string_num_uint16 = str(int((payload_idx_end - payload_idx_start) / 2))
        # se_data_u16 = [struct.unpack(string_num_uint16 + 'H', x) for x in se_data_u8]
        se_data_u16 = []
        for x in se_data_u8:
            # print('SE Message: ' + str(x))
            new_val = struct.unpack(string_num_uint16 + 'H', x)
            # print('SE Converted: ' + str(new_val))
            se_data_u16.append(new_val)

        d = {'diff_data_int16': diff_data_int16, 'se_data_u16': se_data_u16}
        return d
