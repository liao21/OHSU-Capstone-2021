import datetime as dt
import time
import h5py
import logging


class DataLogger(object):
    """
        Class for logging raw binary data from streaming source

        Revisions:
            2016OCT23 Armiger: Created
    """

    def __init__(self, filename=None, num_channels=8, data_type='i1'):

        """Initialize DataLogger class with information about the destination file and the type of data to be logged

            if filename is unspecified, a name with datestamp will be generated on hdf5 file creation

            typically this will be called for logging emg data in which the number of channels is specified

            Data type of the emg data should be specified to ensure minimal file size


        """
        if filename is None:
            filename = 'myo_raw_data_' + dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".hdf5"

        self.num_channels = num_channels
        self.current_label = -1

        logging.info('Creating DataLogger file: {}: '.format(filename))

        print('H5PY Version ' + h5py.__version__)
        # Raw data logging
        d = {'file_name': '', 'base_file': None, 'group': None, 'time': None, 'emg': None, 'label': None, 'index': -1}
        d['file_name'] = filename
        d['base_file'] = h5py.File(d['file_name'], 'w', libver='latest', swmr=False)
        d['base_file'].create_dataset('description', data='Myo Armband Raw EMG Data')
        d['base_file'].create_dataset('num_channels', data=self.num_channels)
        d['group'] = d['base_file'].create_group('data')
        d['time'] = d['group'].create_dataset('time_stamp', (1,), maxshape=(None,), dtype='float')
        d['emg'] = d['group'].create_dataset('emg_data', (1, num_channels), maxshape=(None, 8), dtype=data_type)
        d['label'] = d['group'].create_dataset('class_label', (1,), maxshape=(None,), dtype='i1')
        d['index'] = -1

        self.raw_file = d

    def add_sample(self, data):
        logging.debug('Adding new sample')

        raw = self.raw_file
        raw['index'] += 1
        raw['time'].resize((raw['index'] + 1,))
        raw['emg'].resize((raw['index'] + 1, self.num_channels))
        raw['label'].resize((raw['index'] + 1,))

        raw['time'][raw['index']] = time.time()
        raw['emg'][raw['index'], :] = data
        raw['label'][raw['index']] = self.current_label

    def close(self):
        """ Cleanup socket """
        logging.info('Closing RAW data logger')
        self.raw_file['base_file'].close()
