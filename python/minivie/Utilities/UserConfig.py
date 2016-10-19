# -*- coding: utf-8 -*-
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
import xml.etree.cElementTree as ET
import logging

xmlRoot = None
# function to read in ROC xml file and store as dictionary       
def readUserConfig(file):
    global xmlRoot
    xmlTree = ET.parse(file) # store ROC table as an ElementTree
    xmlRoot = xmlTree.getroot()
    
def getUserConfigVar(key,defaultValue) :
    # Look through XML document root for matching key value and retutn entry as a string
    global xmlRoot
    
    if xmlRoot is None:
        logging.info('xmlRoot is unset')
        logging.info('Reading default xml config file: user_config.xml')
        readUserConfig('../../user_config.xml')
    
    for element in xmlRoot.findall('add'):
        # child is an element, has tag and attributes
        xmlKey = element.get('key')

        if xmlKey == key :
            strValue = element.get('value')
            logging.info(key + ' : ' + strValue)
            
            if type(defaultValue) is str:
                return strValue
            elif type(defaultValue) is int:
                return int(strValue)
            elif type(defaultValue) is float:
                return float(strValue)
            elif type(defaultValue) is tuple:
                return tuple( float(i) for i in strValue.split(','))
            else:
                logging.warning('Unhandled type [{}] for default value for key = {}'.format(type(defaultValue), key))
    
    # Unmatched isn't a problem, parameter just happens to not be in xml, so use default
    #logging.warning(key + ' : UNMATCHED')
    
    logging.info(key + ' : ' + str(defaultValue) + ' (default)')
    return defaultValue

def setupFileLogging(prefix='MiniVIE_', loglevel=logging.INFO ):
    ######################
    # setup logging
    ######################

    # Logging info
    # Level 	When it's used
    # ------    ---------------
    # DEBUG 	Detailed information, typically of interest only when diagnosing problems.
    # INFO 	Confirmation that things are working as expected.
    # WARNING 	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. 'disk space low'). The software is still working as expected.
    # ERROR 	Due to a more serious problem, the software has not been able to perform some function.
    # CRITICAL 	A serious error, indicating that the program itself may be unable to continue running.
    
    # start message log
    fileName = prefix + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    logPath = '.'
        
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    #logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(loglevel)

    fileHandler = logging.FileHandler("{0}/{1}".format(logPath, fileName))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    #logging.basicConfig(filename='OpenNFU.log',format='%(asctime)s:%(levelname)s:%(message)s', \
    #                    level=numeric_level, datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('-----------------------------------------------')
    logging.info('Starting Log with level: {}'.format(loglevel))
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

    #logging.basicConfig(level=logging.DEBUG)
    setupFileLogging('UserConfig_TEST_')
    logging.debug('Running UserConfig Demo Script')

    # get default config file.  This should be run from python\minivie as home, but 
    # also support calling from module directory (Utilities)
    filename = "../../user_config.xml"
    if os.path.split(os.getcwd())[1] == 'Utilities':
        filename = '../' + filename
    readUserConfig(filename)
    
    # check known types
    getUserConfigVar('rocTable','')
    getUserConfigVar('FeatureExtract.zcThreshold',0.0)
    getUserConfigVar('mplVulcanXCommandPort',9000)

    # check invalid types
    getUserConfigVar('_rocTable','')
    getUserConfigVar('_FeatureExtract.zcThreshold',0.0)
    getUserConfigVar('_mplVulcanXCommandPort',9000)
    getUserConfigVar('rocTable',None)
    
    elbowLim = getUserConfigVar('ELBOW_LIMITS',(0.0, 140.0))
    elbowLim = getUserConfigVar('_ELBOW_LIMITS',(0.0, 140.0))

    logging.debug('End UserConfig Demo Script')
    
# Main Function (for demo)
if __name__ == "__main__":
    main()
