# -*- coding: utf-8 -*-
"""
Load an xml Reduced Order Control (ROC) file and store as a dictionary that can be 
referenced by the name of the ROC table entry

Created on Mon Mar  7 08:21:58 2016

@author: carrolm1

Revisions:
2016Aug11 David Samson
2016OCT05 Armiger: updated angle storage and added print / main functions

"""
import logging
import xml.etree.cElementTree as ET
import time
import numpy as np
from scipy.interpolate import interp1d

class rocElem:
   name = '' # grasp name
   id = 0 # grasp ID number
   joints = [] # array of joints involved
   waypoints = [] # array of waypoints
   angles = {} # dictionary of angles for each waypoint
   impedance = {} # dictionary of impedances for each waypoint

# function to read in ROC xml file and store as dictionary       
def readRoc(file): 
    rocTableTree = ET.parse(file) # store ROC table as an ElementTree
    rocTable = {} # make dictionary of ROC grasps
    root = rocTableTree.getroot()
   
   # cycle through grasps in rocTableTree
    for table in root.findall('table'):
        # child is an element, has tag and attributes
        name = table.find('name').text
        # create a rocElem object for that grasp
        elem = rocElem()
        elem.name = name
        elem.id = int(table.find('id').text)
        
        # Note the joint ids here are (-1) so that indices are 0-based for python
        elem.joints = [int(val)-1 for val in table.find('joints').text.split(',')]
        # check each waypoint for angles and impedance measurements
        
        # initialize array that will be nWayPoints*nJoints
        angleArray = []
        elem.waypoints = []
        for waypoint in table.iter('waypoint'):
            index = float(waypoint.get('index'))
            #bisect.insort(elem.waypoints, index) # insert waypoint into sorted list of waypoints
            elem.waypoints.append(index)
            
            # use index as key for angles and impedance dictionaries
            angleArray.append([float(val) for val in waypoint.find('angles').text.split(',')])
            #elem.impedance[index] = [float(val) for val in waypoint.find('impedance').text.split(',')]
        elem.angles = np.reshape(np.asarray(angleArray), [-1, len(elem.joints)])
        rocTable[name] = elem
    # return completed dictionary
    return rocTable

def printRoc(rocElem):

    if rocElem is None: return

    # print an element in the ROC tables
    print("ROC NAME: '{}'".format(rocElem.name))
    print("ROC ID: " + str(rocElem.id))
    print("ROC JOINTS: [" + ' '.join(str(e) for e in rocElem.joints) + "]")
    print("ROC WAYPOINTS: [" + ' '.join(str(e) for e in rocElem.waypoints) + "]")
    print("ROC ANGLES " + str(rocElem.angles.shape) + " :")
    for row in rocElem.angles:
        print(['{:6.3f}'.format(i) for i in row])
    print('\n')

def getRocId(rocTable, id):
    # get a roc table entry by the ID
    
    for rocKey, rocElem in rocTable.items():
        if (rocElem.id == id):
            return rocElem
    logging.warning('Invalid ROC ID : {}'.format(id))
    return None    

def getRocValues(rocElem, val):
    
    x = np.array(rocElem.waypoints);
    y = rocElem.angles;
    newAngles = interp1d(x,y,axis=0,kind='linear')(val)
    return newAngles


def main():

    filename = "../../WrRocDefaults.xml"
    rocTable = readRoc(filename)
    
    for rocKey, rocElem in sorted(rocTable.items()):
        printRoc(rocElem)

    print("\n\nDEMO Get ROC By ID:")
    printRoc(getRocId(rocTable, 1))
    
    # Get out of range ROC ID
    print("\n\nDEMO Get ROC By [INVALID] ID:" )   
    printRoc(getRocId(rocTable, 99))

    print("\n\nDEMO Get ROC Vals:")
    newVals = getRocValues(getRocId(rocTable, 1), 0.1)
    print(['{:6.3f}'.format(i) for i in newVals])
    
# Main Function (for demo)
if __name__ == "__main__":
    main()
