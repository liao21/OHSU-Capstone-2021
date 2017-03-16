"""
Created on Tue Jan 26 2017

Python translation of CpchSerial.m in MATLAB minivie

@author: D. Samson
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
import struct

class CpchSerial(CpcHeadstage):
    """
    Class for interfacing CPCH via serial port
    
    This class is used to interface the JHU/APL Conventional Prosthetics Control Headstage (CPCH)
    via a USB-RS485 adaptor.  The adaptor is based on the FTDI chipset and drivers for the device 
    can be found here:  
    http://www.ftdichip.com/Drivers/VCP.htm
    Note the Virtual Com Port (VCP) drivers should be used (as opposed to the D2XX Direct Drivers)
    
    Typical Baud rate for the device is 921600 bps
    
    ##########TO UPDATE FOR PYTHON##########
    # % Example Usage:
    # obj = Inputs.CpchSerial('COM11',...
        # uint16(hex2dec('FFFF')),uint16(hex2dec('FFFF')));
    # fprintf('Adding Filters\n');
    # Fs = 1000;
    # obj.addfilter(Inputs.HighPass(10,8,Fs));
    # h.addfilter(Inputs.Notch(60.*(1:4),5,Fs));
    # obj.NumSamples = 2000;
    # obj.initialize();
    
    # % Get raw data.  [numSamples x numChannels]
    # data = obj.getData();
    
    # % Get data with filters applied
    # filteredData = obj.getFilteredData();
    
    # DEBUG: Send sequence data as last single ended channel
    # TODO: maintain sequence as an additional variable
    
    # Oct-2011 Helder: Created
    # 13Mar2012 Armiger: Improved efficiancy of data processing from raw
    # bytes to data vals.  Added support for singleEnded data streaming
    """
    
    def __init__(self, comPort='COM1', bioampMask=int('0xFFFF', 16), gpiMask=int('0x0000', 16)):
        """

        """
        
        assert type(comPort) is str
        assert bioampMask.bit_length() <= 16 and bioampMask >= 0    #check if 16-bit int and unsigned
        assert gpiMask.bit_length() <= 16 and gpiMask >= 0          #check if 16-bit int and unsigned
        
        #Initialize superclass
        super(CpchSerial, self).__init__()
        
        #public access variables
        self.SerialPort = comPort # Port must be capable of 921600 baud
        self.BioampMask = bioampMask
        self.GPIMask = gpiMask
        
        self.EnableDataLogging = 0  # Enables logging data stream to disk
        
        # Gain values form normalized values
        self.GainSingleEnded = 10
        self.GainDifferential = 0.00489
        
        # private set access variables
        self.CountTotalMessages = 0
        self.CountBadLength = 0
        self.CountBadChecksum = 0
        self.CountBadStatus = 0
        self.CountBadSequence = 0
        self.CountAdcError = 0
        
        # private access variables
        self.hLogFile = None  # Handle to optional log file
        self.SerialObj = []
        self.DataBuffer = []  #list of bytearrays
        self.SerialBuffer = bytearray([])  #bytearray
        self.PrevDataFrameID = -1
        self.BioampCnt = 0
        self.GPICnt = 0
        self.ChannelMask = []
        self.StartTime = time.time()
        self.IsRunning = False

        self.ChannelIds = list(range(32))
        self.SampleFrequency = 1000
        self.NumSamples = 3000
        self.NumChannels = 32

    def initialize(self):
        #Initialize the serial object
        
        bits = self.BioampMask.bit_length
        # max_bits = 8 if (bits > 0 and bits <= 8) else 16 if (bits > 8 and bits <= 16) else None
        max_bits = 16
        self.BioampCnt = bin(self.BioampMask).count("1")
        
        bits = self.GPIMask.bit_length
        # max_bits = 8 if (bits > 0 and bits <= 8) else 16 if (bits > 8 and bits <= 16) else None
        max_bits = 16
        self.GPICnt = bin(self.GPIMask).count("1")
        
        # buffer to hold collected data
        self.DataBuffer = np.empty([3000, 32], dtype=np.double)
        
        try:
            self.SerialObj = serial.Serial(
                port=self.SerialPort,
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
            print('[%s] Port Opened: %s' % (__file__, self.SerialPort.upper()))

        except Exception as exp:
            print('[%s] Port FAILED' % __file__)
            raise exp
            
        # Transmit STOP message in case data is flowing so the system can sanely start
        msg = self.EncodeStopMsg()
        self.SerialObj.write(msg)
        
        while True:
            time.sleep(0.1) # delay here to ensure all bytes have time for receipt
            bytesAvailable = self.SerialObj.in_waiting
            if bytesAvailable:
                self.SerialObj.read(bytesAvailable)
            else:
                break

        # Get CPCH ID
        # Read param to verify the message.  Note that this must be
        # read back to ensure the message structure is correct since
        # not all channels can (or will) return data.  Unrequested channels
        # are unreturned by the system.
        msg = self.EncodeConfigReadMsg(1)
        self.SerialObj.write(msg)
        # Check response
        r = bytearray(self.SerialObj.read(7))   #cast string to more portable bytearray
        rcnt = len(r)

        # Do this after the first read so that we can establish if any
        # response was given
        assert rcnt > 0, 'No response from CPCH. Check power, check connections'
        
        msgId = self.msgIdConfigurationReadResponse
        assert rcnt == 7, 'Wrong number of bytes returned. Expected [%r], received [%r]' % (rcnt , 7)
        assert r[0] == msgId, 'Bad response message id.  Expected [%r], received [%r]' % (msgId, r[0])
        assert r[1] == 1, 'Bad parameter id. Expected [%r], received [%r]'% (1, r[1])
        assert self.XorChksum(r)[0] == 0, 'Bad checksum'
        u32Parameter = 0
        for i in reversed(r[2:5]):
            u32Parameter = (u32Parameter << 8) + i
        print('[%s] Device ID = %d' % (__file__, u32Parameter))
        
        # Reconfigure the CPCH
        # msg example: [ 4    2  255  255    0    0  249]
        # 4 = write param
        # 2 = param type 2 (active channels)
        
        # Send Request
        channel_config = (self.GPIMask << 16) + self.BioampMask #bitshift(uint32(obj.GPIMask), 16) + uint32(obj.BioampMask);
        msg = self.EncodeConfigWriteMsg(2, channel_config)
        self.SerialObj.write(msg)#fwrite(obj.SerialObj, msg, 'uint8');
        
        # Check response
        r = bytearray(self.SerialObj.read(3))   #[r, rcnt] = fread(obj.SerialObj, 3, 'uint8');
        rcnt = len(r)
        
        msgId = self.msgIdConfigurationWriteResponse
        assert rcnt == 3, 'Wrong number of bytes returned'
        assert r[0] == msgId, 'Bad response message id. Expected %d, got %d' % (msgId, r[0])
        assert (r[1] & 1) == 1,'Configuration Write Failed'
        
        # Read param to verify the message.  Note that this must be
        # read back to ensure the message structure is correct since
        # not all channels can (or will) return data.  Unrequested channels
        # are unreturned by the system.
        msg = self.EncodeConfigReadMsg(2);
        self.SerialObj.write(msg)   #fwrite(obj.SerialObj, msg, 'uint8');
        # Check response
        r = bytearray(self.SerialObj.read(7)) #[r, rcnt] = fread(obj.SerialObj, 7, 'uint8');
        rcnt = len(r)
        
        msgId = self.msgIdConfigurationReadResponse
        assert rcnt == 7, 'Wrong number of bytes returned'
        assert r[0] == msgId, 'Bad response message id'
        
        frameB = self.DecodeMsg(r, self.BioampCnt, self.GPICnt)
        
        assert frameB.Mask == channel_config ,'Defined channel mask does not match returned mask. Expected: uint32[%d] Got:uint32[%d]' % (channel_config, frameB.Mask)
        
        self.ChannelMask = [int(i) for i in format(frameB.Mask, '0' + str(self.DataBuffer.shape[1]) + 'b')]
        
        pass
        
    def start(self):
        '''
        Start the data streaming
        '''
        self.StartTime = time.time()
        print('[%s] Starting CPCH with %d differential and %d single-ended inputs...' % (__file__, self.BioampCnt, self.GPICnt))

        if self.SerialObj.closed:
            self.SerialObj.open()

        if not self.SerialObj.closed:
            msg = self.EncodeStartMsg()

            bytesAvailable = self.SerialObj.in_waiting
            if bytesAvailable:
                self.SerialObj.read(bytesAvailable)

            self.SerialObj.write(msg)
            self.IsRunning = True

        pass

    def getData(self, numSamples=None, idxChannel=None):
        numSamples = numSamples or self.NumSamples
        idxChannel = idxChannel or self.ChannelIds

        # Start device if not already running
        if self.SerialObj.closed or not self.IsRunning:
            self.start()

        # Check for new data
        numAvailable = self.SerialObj.in_waiting
        if numAvailable == 0:
            data = self.DataBuffer[-self.NumSamples:, :]
            return data

        # Read samples from serial buffer and place in internal bufer
        # (potentially with leftover remaining bytes)
        r = bytearray(self.SerialObj.read(numAvailable))
        rawBytes = self.SerialBuffer + r

        payloadSize = 2*(self.BioampCnt + self.GPICnt)
        msgSize = payloadSize + 6

        # Align the data bytes. If all's well the first byte of the
        # remainder should be a start char which is saved for the next
        # time the buffer is read
        d = self.AlignDataBytes(rawBytes, msgSize)
        alignedData = d['dataAligned']
        remainderBytes = d['remainderBytes']

        # Store remaining bytes for the next read
        self.SerialBuffer = remainderBytes

        # No new data
        if not alignedData:
            data = self.DataBuffer[-self.NumSamples:, :]
            return data

        # Check validation parameters(chksum, etc)
        d = self.ValidateMessages(alignedData, payloadSize)
        validData = d['validData']
        errorStats = d['errorStats']

        self.CountTotalMessages = self.CountTotalMessages + len(alignedData)
        self.CountBadChecksum = self.CountBadChecksum + errorStats['sumBadChecksum']
        self.CountBadStatus = self.CountBadStatus + errorStats['sumBadStatus']
        self.CountBadSequence = self.CountBadSequence + errorStats['sumBadSequence']
        self.CountAdcError = self.CountAdcError + errorStats['sumAdcError']

        numValidSamples = len(validData)
        numBytes = len(validData[0])

        assert msgSize == numBytes

        # Extract the signals
        d = self.GetSignalData(validData, self.BioampCnt, self.GPICnt)
        diffDataI16 = d['diffDataInt16']
        seDataU16 = d['seDataU16']

        # Perform scaling
        deDataNormalized = []
        for tup in diffDataI16:
            deDataNormalized.append([float(x)*self.GainDifferential for x in tup])

        seDataNormalized = []
        for tup in seDataU16:
            seDataNormalized.append([float(x)/1024.0*self.GainSingleEnded for x in tup])

        # Send sequence data as last single ended channel

        # Log data

        # Update internal formatted data buffer

        # Return the most recently requested data

        pass
