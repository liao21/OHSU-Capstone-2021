"""
Created on Tue Jan 26 2017

Python translation of CpcHeadstage.m in MATLAB minivie

@author: D. Samson
"""

import struct
import sys


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
        self.msgIdStartStreaming = 1
        self.msgIdStopStreaming  = 2
        self.msgIdStatusRequest  = 3
        self.msgIdConfigurationWrite = 4
        self.msgIdConfigurationRead = 5
        self.msgIdCpcData = 128
        self.msgIdStopStreamingResponse = 129
        self.msgIdStatusData = 130
        self.msgIdConfigurationReadResponse = 131
        self.msgIdConfigurationWriteResponse = 132
    
    def EncodeStartMsg(self):
        msg = bytearray()
        msg += struct.pack('B', 1)
        msg += struct.pack('B', self.XorChksum(msg)[0])
        return msg

    def EncodeStopMsg(self):
        msg = bytearray()
        msg += struct.pack('B', 2)
        msg += struct.pack('B', self.XorChksum(msg)[0])
        return msg

    def EncodeStatusMsg(self):
        msg = bytearray()
        msg += struct.pack('B', 3)
        msg += struct.pack('B', self.XorChksum(msg)[0])
        return msg

    def XorChksum(self, msg, poly=0b101001101):
        """
        XOR checksum of msg using 0xA6 default polynomial
        
        Input Arguments:
        self -- reference to this object
        msg -- bytearray to be checksummed
        poly -- integer of taps in the polynomial
        
        Return Arguments:
        check -- checksum result byte

        Modified 3/15/17 by COP to handle lists of messages
        """
        
        assert type(msg) is bytearray or type(msg) is list
        assert type(poly) is int
        assert (poly.bit_length() - 1) % 8 == 0  # must be an multiple-of-8-bit polynomial

        # Put msg into list if passed as bytearray
        if type(msg) is bytearray:
            msg = [msg]

        vals = []
        for this_msg in msg:
            # convert msg from bytearray to single int
            val = 0
            for byte in this_msg:
                val = (val << 8) + byte

            pBits = poly.bit_length()

            val <<= pBits - 1   # pad input with a byte for the remainder

            vBits = val.bit_length()

            for i in reversed(list(range(pBits - 1, vBits))):
                if val >> i == 1:
                    val ^= poly << ((i + 1) - pBits)

            vals.append(int(val))
        return vals
        
    def EncodeConfigReadMsg(self, indx):
        msg = bytearray()
        msg = msg + struct.pack('B',5)
        msg = msg + struct.pack('B',indx)
        msg = msg + struct.pack('B',self.XorChksum(msg)[0])
        return msg
    
    def EncodeConfigWriteMsg(self, indx, payload):
            endian = sys.byteorder  #[~, ~, endian] = computer()
            
            msg = bytearray()
            msg = msg + struct.pack('B',4)
            msg = msg + struct.pack('B',indx)
            
            if (endian == 'big'):
                msg = msg + struct.pack('<I', payload)  #msg(3:6) = typecast(swapbytes(uint32(payload)), 'uint8')
            else:
                msg = msg + struct.pack('I', payload)   #msg(3:6) = typecast(uint32(payload), 'uint8')
            
            msg = msg + struct.pack('B',self.XorChksum(msg)[0])
            return msg
    
    def DecodeMsg(self, msg, diffCnt, seCnt):
            endian = sys.byteorder  #[~, ~, endian] = computer();
            
            msgx = bytearray(msg)
            
            frame = type('Frame', (object, ), {})() #generate object to hold frame data
            
            frame.Type = msgx[0]
            
            if msg[0] == 128:       # 1KHz CPCH Data Stream
                frame.Status.CommErrCnt = msgx[1]
                frame.Status.MsgIDErr   = ((msgx[2] >> 0) & 1) != 0
                frame.Status.ChksumErr  = ((msgx[2] >> 1) & 1) != 0
                frame.Status.LengthErr  = ((msgx[2] >> 3) & 1) != 0
                frame.Status.ADCErr     = ((msgx[2] >> 7) & 1) != 0
                
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
                frame.Status.CommErrCnt = msgx[1]
                frame.Status.MsgIDErr   = ((msgx[2] >> 0) & 1) != 0 #(bitget(msgx(3), 1)) ~= 0
                frame.Status.ChksumErr  = ((msgx[2] >> 1) & 1) != 0 #(bitget(msgx(3), 2)) ~= 0
                frame.Status.LengthErr  = ((msgx[2] >> 2) & 1) != 0 #(bitget(msgx(3), 3)) ~= 0
                frame.Status.ADCErr     = ((msgx[2] >> 3) & 1) != 0 #(bitget(msgx(3), 4)) ~= 0
                
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

    def AlignDataBytes(self, dataStream, msgSize):
        d = self.ByteAlignFast(dataStream, msgSize)
        return d

    def ByteAlignFast(self, dataStream, msgSize):

        # Find all start chars ('128') and index the next set of bytes
        # off of these starts.  This could lead to overlapping data
        # but valid data will be verified using the checksum
        bytePattern = [128, 0, 0]
        idxStartBytes = [i for i, x in enumerate(dataStream) if x == 128]

        if not idxStartBytes:
            print('No start sequence [' + ' '.join(str(x) for x in bytePattern) + '] found in data stream of length %d.  Try resetting CPCH' % (len(dataStream)))

        # Check if there are too few bytes between the last start
        # character and the end of the buffer
        idxStartBytesInRange = [x for x in idxStartBytes if x <= len(dataStream) - msgSize]
        if not idxStartBytesInRange:
            # No full messages found
            d = {'dataAligned':  [], 'remainderBytes': dataStream}
            return d

        remainderBytes = dataStream[idxStartBytesInRange[-1] + msgSize:]

        # Align the data based on the validated start characters
        dataAligned = []
        for i in idxStartBytesInRange:
            dataAligned.append(dataStream[i: i + msgSize])

        # Return data
        d = {'dataAligned': dataAligned, 'remainderBytes': remainderBytes}
        return d

    def ValidateMessages(self, alignedData, expectedLength):
        """
        Validate a matrix of messages using a criteria of checksum,
        appropriate message length, and status bytes

        Aligned data should be a list of length = numMessages,
        with each element being bytearray of length = numBytesPerMessage
        """

        # Compute CRC
        computedChecksum = self.XorChksum(alignedData)

        # Find validated data by ensuring it is the correct length and has correct checksum
        # Status byte upper four bits are set to zero
        isValidStatusByte = [not(x[2] & 240) for x in alignedData]
        isAdcError = [bool(int('{0:08b}'.format(x[2])[3])) for x in alignedData]
        isValidLength = [x[4] == expectedLength for x in alignedData]
        isValidChecksum = [not bool(x) for x in computedChecksum]
        isValidData = isValidChecksum and isValidLength and isValidStatusByte

        validData = [x for i, x in enumerate(alignedData) if isValidData[i]]

        # No valid data in packet
        if not validData:
            return

        # Check sequence bytes in batch operation
        sequenceRow = [float(x[3]) for x in validData]
        sequenceExpected = [(x + sequenceRow[0]) % 256 for x in range(len(validData))]
        isValidSequence = [(sequenceExpected[i] - sequenceRow[i]) == 0.0 for i, x in enumerate(sequenceRow)]

        sumBadStatus = isValidStatusByte.count(False)
        sumBadLength = isValidLength.count(False)
        sumBadChecksum = isValidChecksum.count(False)
        sumBadSequence = isValidSequence.count(False)
        sumAdcError = isAdcError.count(False)

        errorStats = {'sumBadStatus': sumBadStatus, 'sumBadLength': sumBadLength, 'sumBadChecksum': sumBadChecksum, 'sumBadSequence': sumBadSequence, 'sumAdcError': sumAdcError}
        d = {'validData': validData, 'errorStats': errorStats}
        return d

    def GetSignalData(self, validData, diffCnt, seCnt):
        # Typecast the data to the appropriate data size

        # Get data size
        num_valid_samples = len(validData)

        # Convert the valid data to Int16int
        payloadIdxStart = 5
        payloadIdxEnd = payloadIdxStart + 2*diffCnt # Diff data starts after header
        deDataU8 = [x[payloadIdxStart:payloadIdxEnd] for x in validData]
        string_num_int16 = str((payloadIdxEnd - payloadIdxStart)/2)
        diffDataInt16 = [struct.unpack(string_num_int16 + 'h', x) for x in deDataU8]

        payloadIdxStart = 5 + 2 * diffCnt  # se data starts after diff data
        payloadIdxEnd = payloadIdxStart + 2 * seCnt
        seDataU8 = [x[payloadIdxStart:payloadIdxEnd] for x in validData]
        string_num_uint16 = str((payloadIdxEnd - payloadIdxStart) / 2)
        seDataU16 = [struct.unpack(string_num_uint16 + 'H', x) for x in seDataU8]

        d = {'diffDataInt16': diffDataInt16, 'seDataU16': seDataU16}
        return d
