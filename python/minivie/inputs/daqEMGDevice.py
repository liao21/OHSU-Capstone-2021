import nidaqmx
import numpy as np
import threading
import logging
import time
from inputs.signal_input import SignalInput

class DaqEMGDevice(SignalInput):

    def __init__(self, id, num_samples=50):

        # Initialize superclass
        super(DaqEMGDevice, self).__init__()

        # logger
        self.log_handlers = None

        # 8 channel max for myo armband
        self.num_channels = 8
        self.num_samples = num_samples

        #device id
        self.id = id

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use getData to access since it is thread-safe
        self.__dataEMG = np.zeros((num_samples, 8))

        # Internal values
        self.__battery_level = -1  # initial value is unknown
        self.__count_emg = 0
        self.__time_emg = 0.0
        self.__rate_emg = 0.0

        # Initialize connection parameters
        self.__lock = None
        self.__thread = None

    def connect(self):

        #system = nidaqmx.system.System.local()
        #for device in system.devices:
            #name = str(device)
            #self.id = name[7:len(name)-1]+'/ai0:7'

        # Create thread-safe lock so that user based reading of values and thread-based
        # writing of values do not conflict
        self.__lock = threading.Lock()

        # Create a thread for processing new incoming data
        self.__thread = threading.Thread(target=self.read_packet)
        self.__thread.name = 'DaqEMGDeviceRcv'
        self.__thread.start()

    def read_packet(self):
        while True:
            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(self.id)
                data = task.read(number_of_samples_per_channel=5)
                self.output = data

            if self.log_handlers is not None:
                self.log_handlers(self.output)

            with self.__lock:

                # Populate EMG Data Buffer (newest on top)
                self.__dataEMG = np.roll(self.__dataEMG, len(self.output[0][:]), axis=0)
                for i in range(len(self.output[0][:])):
                    for s in range(len(self.output)):
                        self.__dataEMG[i:i+1, s:s+1] = self.output[s][i:i+1]# insert into buffer entry

                # compute data rate
                if self.__count_emg == 0:
                    # mark time
                    self.__time_emg = time.time()

                self.__count_emg += 5  # 5 data points per packet

                t_now = time.time()
                t_elapsed = t_now - self.__time_emg

                if t_elapsed > 3.0:
                    # compute rate (every second)
                    self.__rate_emg = self.__count_emg / t_elapsed
                    self.__count_emg = 0  # reset counter

    def get_data(self):
        """ Return data buffer [nSamples][nChannels] """
        with self.__lock:
            return self.__dataEMG

    def get_angles(self):
        """ Return Euler angles computed from Myo quaternion """
        # convert the stored quaternions to angles (no angles for daq)
        with self.__lock:
            return None

    def get_rotationMatrix(self):
        """ Return rotation matrix computed from Myo quaternion (no rotation matrix for daq)"""
        with self.__lock:
            return None

    def get_imu(self):
        """ Return IMU data as a dictionary (not imu data for daq)
        result['quat'] = (qw qx qy qz)
        result['accel'] = (ax ay az)
        result['gyro'] = (rx ry rz)
        """
        with self.__lock:
            return {'quat': None , 'accel': None, 'gyro': None}

    def get_battery(self):
        # Return the battery value (no battery for daq) (0-100)
        with self.__lock:
            return -1

    def get_data_rate_emg(self):
        # Return the emg data rate
        with self.__lock:
            return self.__rate_emg

    def get_status_msg(self):
        # return string formatted status message
        # with data rate and battery percentage
        # E.g. 200Hz 99%
        battery = self.get_battery()
        if battery < 0:
            battery = '--'
        return '{:.0f}Hz {}%'.format(self.get_data_rate_emg(),battery)

    def close(self):
        """ Cleanup"""
        logger.info("\n\nClosing DaqEMGDevice@ {}".format(self.addr))


        if self.__thread is not None:
            self.__thread.join()