"""
Load an xml User Config file

Usage:
    from utilities import user_config
    user_config.get_user_config_var('my_param',5)


Revisions:
2016OCT06 Armiger: Created

"""
import os
from datetime import datetime
import xml.etree.cElementTree as xmlTree
import logging

xml_root = None
xml_tree = None
xml_file = None
xml_force_default = True  # If there is a problem with the xml, revert to just returning config value defaults


def read_user_config(file='../../user_config.xml', reload=False):
    # function to read in xml file and store as dictionary
    #
    # Note this function uses the xml as a global variable such that any function in the system can make a direct call
    # to access parameters
    #
    # Use the reload command to just re-read the xml file and not change the filename

    global xml_file, xml_root, xml_tree, xml_force_default
    if not reload:
        xml_file = file
    logging.info('Reading xml config file: {}'.format(xml_file))
    try:
        xml_tree = xmlTree.parse(xml_file)
        xml_root = xml_tree.getroot()
        xml_force_default = False
    except FileNotFoundError:
        xml_force_default = True
        logging.error('Failed to find file {} in {}. Param defaults will be used.'.format(xml_file, os.getcwd()))


def get_user_config_var(key, default_value):
    # Look through XML document root for matching key value and return entry as a string
    # Note the second argument is the a default value in the event the key or xml file is not found
    #

    # If there was a problem with the xml file, no point in parsing or loading further,
    if xml_force_default:
        return default_value

    # Assume file is not loaded, try to load it
    if xml_root is None:
        logging.info('xml_root is unset')
        read_user_config()

    for element in xml_root.findall('add'):
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


def set_user_config_var(key, value):
    # Look through XML document root for matching key value and update entry as string,
    # or create new entry if necessary
    #
    # Inputs: key - string, should match existing key from user config or new key will be written
    #         value - string/float/int or array/tuple of these, will always be formatted as string

    if xml_root is None:
        logging.info('xml_root is unset')
        read_user_config()

    # Format value as comma-separated list
    if type(value) is list or type(value) is tuple:
        str_value = ','.join([str(x) for x in value])
    elif type(value) is int or type(value) is float or type(value) is str:
        str_value = str(value)
    else:
        logging.warning('Unhandled type [{}] for value for key = {}'.format(type(value), key))
        return None

    # Initialize old string value
    old_str_value = 'NA'
    key_exists = False
    for element in xml_root.findall('add'):
        # child is an element, has tag and attributes
        xml_key = element.get('key')

        if xml_key == key:
            key_exists = True
            old_str_value = element.get('value') # Get old value
            element.set('value', str_value)  # Set new value

    # Add new key if it didn't exist
    if not key_exists:
        new_element = xmlTree.fromstring('<add key="{}" value="{}"/>'.format(key, str_value))
        xml_root.append(new_element)

    logging.info(key + ' : ' + old_str_value + ' (original)')
    logging.info(key + ' : ' + str_value + ' (new)')


def save(file='../../user_config.xml'):
    # Save out xml

    if xml_root is None:
        logging.info('xml_root is unset')
        read_user_config()

    # Check if file already exists, and save with incremented name
    if os.path.isfile(file):
        fname = os.path.splitext(file)[0]
        date_string =  datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        old_file = '{}_{}.xml'.format(fname, date_string)
        os.rename(file, old_file)
        logging.warning('Overwritten user configuration file {} moved to {}'.format(file, old_file))

    # Save
    indent(xml_root)  # Pretties up the writing
    xml_tree.write(file, encoding='utf-8', xml_declaration=True, default_namespace=None, method='xml')


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

    # Notes:  The logging level specified as inputs maps to the verbosity of the log file.  The log level of the console
    # is set to WARNING
    # TODO: It's unclear why the setLevel for the file handler appear to have no effect

    # start message log
    logger = logging.getLogger('')
    logger.setLevel(log_level)

    # create file handler which logs debug messages
    file_path = '.'
    file_name = prefix + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    fh = logging.FileHandler(os.path.join(file_path, file_name))
    #fh.setLevel(logging.DEBUG)
    fh.setLevel(logging.INFO)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    # Set formatting
    fh.setFormatter(logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"))
    ch.setFormatter(logging.Formatter("[%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"))

    # add the handlers to logger
    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)

    # logging.basicConfig(filename='OpenNFU.log',format='%(asctime)s:%(levelname)s:%(message)s', \
    #                    level=numeric_level, datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.critical('-----------------------------------------------')
    logging.critical('Starting Log File "{}" with level: {}'.format(file_name, logging.getLevelName(log_level)))
    logging.critical('-----------------------------------------------')

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


def indent(elem, level=0):
    # https://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    # Pretty printing of XML elements with proper indents

    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def main():
    # get default config file.  This script should be run from python\minivie, 
    # but also support calling from module directory (utilities)
    filename = "../../user_config.xml"
    new_filename = "../../test_new_user_config.xml"
    if os.path.split(os.getcwd())[1] == 'utilities':
        filename = '../' + filename
        new_filename = '../' + new_filename
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

    # overwrite old values
    set_user_config_var('FeatureExtract.sscThreshold', '0.01')
    set_user_config_var('FeatureExtract.zcThreshold', 0.01)

    # add new key-value pairs
    set_user_config_var('Test Int Value', 1)
    set_user_config_var('Test Float Value', 1.0)
    set_user_config_var('Test String Value', '1.0')
    set_user_config_var('Test List Value', [1, 2, 3])
    set_user_config_var('Test Tuple Value', ('1', '2', '3'))

    # save user config to new name
    save(file = new_filename)

    logging.debug('End UserConfig Demo Script')


# Main Function (for demo)
if __name__ == "__main__":
    setup_file_logging('UserConfig_TEST_')
    logging.debug('Running UserConfig Demo Script')
    main()
