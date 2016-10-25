"""
Load an xml User Config file

Usage:
    from Utilities import UserConfig
    UserConfig.getUserConfigVar('bob',5)


Revisions:
2016OCT06 Armiger: Created

"""
import os
from datetime import datetime
import xml.etree.cElementTree as xmlTree
import logging

xmlRoot = None


def read_user_config(file):
    # function to read in xml file and store as dictionary
    global xmlRoot
    xmlRoot = xmlTree.parse(file).getroot()


def get_user_config_var(key, default_value):
    # Look through XML document root for matching key value and retutn entry as a string
    global xmlRoot
    
    if xmlRoot is None:
        logging.info('xmlRoot is unset')
        logging.info('Reading default xml config file: user_config.xml')
        read_user_config('../../user_config.xml')
    
    for element in xmlRoot.findall('add'):
        # child is an element, has tag and attributes
        xml_key = element.get('key')

        if xml_key == key:
            str_value = element.get('value')
            logging.info(key + ' : ' + str_value)
            
            if type(default_value) is str:
                return str_value
            elif type(default_value) is int:
                return int(str_value)
            elif type(default_value) is float:
                return float(str_value)
            elif type(default_value) is tuple:
                return tuple(float(i) for i in str_value.split(','))
            else:
                logging.warning('Unhandled type [{}] for default value for key = {}'.format(type(default_value), key))
    
    # Unmatched isn't a problem, parameter just happens to not be in xml, so use default
    # logging.warning(key + ' : UNMATCHED')
    
    logging.info(key + ' : ' + str(default_value) + ' (default)')
    return default_value


def setup_file_logging(prefix='MiniVIE_', log_level=logging.INFO):
    ######################
    # setup logging
    ######################

    # Logging info
    # Level 	When it's used
    # ------    ---------------
    # DEBUG 	Detailed information, typically of interest only when diagnosing problems.
    # INFO 	Confirmation that things are working as expected.
    # WARNING 	An indication that something unexpected happened, or indicative of some problem in the near future
    # ERROR 	Due to a more serious problem, the software has not been able to perform some function.
    # CRITICAL 	A serious error, indicating that the program itself may be unable to continue running.
    
    # start message log

    # create file handler which logs debug messages
    file_path = '.'
    file_name = prefix + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    fh = logging.FileHandler(os.path.join(file_path, file_name))
    fh.setLevel(logging.INFO)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    # Set formatting
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    # formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to logger
    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)

    # logging.basicConfig(filename='OpenNFU.log',format='%(asctime)s:%(levelname)s:%(message)s', \
    #                    level=numeric_level, datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('-----------------------------------------------')
    logging.info('Starting Log File "{}" with level: {}'.format(file_name, logging.getLevelName(log_level)))
    logging.info('-----------------------------------------------')
    logging.debug('DEBUG')
    logging.info('INFO')
    logging.warning('WARNING')
    logging.error('ERROR')
    logging.critical('CRITICAL')
    logging.info('-----------------------------------------------')

    '''
    Code snip for parsing command line

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    # assuming loglevel is bound to the string value obtained from the
    # command line argument. Convert to upper case to allow the user to
    # specify --log=DEBUG or --log=debug
    parser = argparse.ArgumentParser(description='Main OpenNFU function')
    parser.add_argument('--log', dest='loglevel',
                        default='INFO',
                        help='Set loglevel as DEBUG INFO WARNING ERROR CRITICAL (default is INFO)')
    args = parser.parse_args()
    '''


def main():

    # logging.basicConfig(level=logging.DEBUG)

    # Check reading parameter from default roc file
    # (must be done before call to readUserConfig(filename)
    get_user_config_var('rocTable', '')
    
    # get default config file.  This script should be run from python\minivie, 
    # but also support calling from module directory (Utilities)
    filename = "../../user_config.xml"
    if os.path.split(os.getcwd())[1] == 'Utilities':
        filename = '../' + filename
    read_user_config(filename)
    
    # check known types
    get_user_config_var('rocTable', '')
    get_user_config_var('FeatureExtract.zcThreshold', 0.0)
    get_user_config_var('mplVulcanXCommandPort', 9000)

    # check invalid types
    get_user_config_var('TEST_INVALID_rocTable', '')
    get_user_config_var('TEST_INVALID_FeatureExtract.zcThreshold', 0.0)
    get_user_config_var('TEST_INVALID_mplVulcanXCommandPort', 9000)
    get_user_config_var('rocTable', None)
    
    get_user_config_var('ELBOW_LIMITS', (0.0, 140.0))
    get_user_config_var('TEST_INVALID_ELBOW_LIMITS', (0.0, 140.0))

    logging.debug('End UserConfig Demo Script')
    
# Main Function (for demo)
if __name__ == "__main__":
    setup_file_logging('UserConfig_TEST_')
    logging.debug('Running UserConfig Demo Script')
    main()
