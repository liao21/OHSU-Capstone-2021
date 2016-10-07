# -*- coding: utf-8 -*-
"""
Load an xml User Config file

Revisions:
2016OCT06 Armiger: Created

"""
import xml.etree.cElementTree as ET
import logging

# works in Python 2 & 3
class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})): pass

class userConfig(Singleton):
    def __init__(self, filename):
       self.filename = filename 
       self.readUserConfig(filename) 

    # function to read in ROC xml file and store as dictionary       
    def readUserConfig(self,file):
        xmlTree = ET.parse(file) # store ROC table as an ElementTree
        self.xmlRoot = xmlTree.getroot()
    
    def getUserConfigVar(self,key,defaultValue) :
        # Look through XML document root for matching key value and retutn entry as a string
        
        for element in self.xmlRoot.findall('add'):
            # child is an element, has tag and attributes
            xmlKey = element.get('key')

            if xmlKey == key :
                strValue = element.get('value')
                print(key + ' : ' + strValue)
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
                    logging.warning('Unknown type [' + str(type(defaultValue)) + '] for default value for key = ' + key)
        
        # Unmatched isn't a problem, parameter just happens to not be in xml, so use default
        #logging.warning(key + ' : UNMATCHED')
        
        print(key + ' : ' + str(defaultValue) + ' (default)')
        logging.info(key + ' : ' + str(defaultValue) + ' (default)')
        return defaultValue

    
# Main Function (for demo)
if __name__ == "__main__":
    
    filename = "../user_config.xml"
    UC = userConfig(filename)
    
    UC.getUserConfigVar('rocTable','')
    UC.getUserConfigVar('FeatureExtract.zcThreshold',0.0)
    UC.getUserConfigVar('mplVulcanXCommandPort',9000)

    UC.getUserConfigVar('_rocTable','')
    UC.getUserConfigVar('_FeatureExtract.zcThreshold',0.0)
    UC.getUserConfigVar('_mplVulcanXCommandPort',9000)
    
    elbowLim = UC.getUserConfigVar('ELBOW_LIMITS',(0.0, 140.0))
    print(type(elbowLim[0]))
    print(elbowLim[1])
    elbowLim = UC.getUserConfigVar('_ELBOW_LIMITS',(0.0, 140.0))
    print(type(elbowLim[0]))
    print(elbowLim[1])
    
    