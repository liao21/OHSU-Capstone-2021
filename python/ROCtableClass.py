# -*- coding: utf-8 -*-
"""
Load an xml Roc file and store as a dictionary that can be 
referenced by the name of the ROC table entry

Created on Mon Mar  7 08:21:58 2016

@author: carrolm1

Revisions:
2016Aug11 David Samson
2016OCT05 Armiger: updated angle storage and added print / main functions

"""
import xml.etree.cElementTree as ET
import time
import numpy as np
    
class rocElem:
   def __init__(self, name):
       self.name = name # grasp name
       self.id = 0 # grasp ID number
       self.joints = [] # array of joints involved
       self.waypoints = [] # array of waypoints
       self.angles = {} # dictionary of angles for each waypoint
       self.impedance = {} # dictionary of impedances for each waypoint

# function to read in ROC xml file and store as dictionary       
def storeROC(file): 
    rocTableTree = ET.parse(file) # store ROC table as an ElementTree
    rocTable = {} # make dictionary of ROC grasps
    root = rocTableTree.getroot()
   
   # cycle through grasps in rocTableTree
    for table in root.findall('table'):
        # child is an element, has tag and attributes
        name = table.find('name').text
        # create a rocElem object for that grasp
        elem = rocElem(name)
        elem.id = int(table.find('id').text)
        elem.joints = [int(val) for val in table.find('joints').text.split(',')]
        # check each waypoint for angles and impedance measurements
        
        # initialize array that will be nWayPoints*nJoints
        angleArray = []
        elem.waypoints = []
        for waypoint in table.iter('waypoint'):
            index = waypoint.get('index')
            #bisect.insort(elem.waypoints, index) # insert waypoint into sorted list of waypoints
            elem.waypoints.append(index)
            
            # use index as key for angles and impedance dictionaries
            angleArray.append([float(val) for val in waypoint.find('angles').text.split(',')])
            #elem.impedance[index] = [float(val) for val in waypoint.find('impedance').text.split(',')]
        elem.angles = np.reshape(np.asarray(angleArray), [-1, len(elem.joints)])
        rocTable[name] = elem
    # return completed dictionary
    return rocTable

def printROC(rocElem):
    # print an element in the ROC tables
    print("ROC NAME = '" + rocElem.name + "'")
    print("ROC ID = " + str(rocElem.id))
    print("ROC JOINTS = [" + ' '.join(str(e) for e in rocElem.joints) + "]")
    print("ROC WAYPOINTS = [" + ' '.join(str(e) for e in rocElem.waypoints) + "]")
    print("ROC ANGLES " + str(rocElem.angles.shape) + " = ")
    for row in rocElem.angles:
        print(['{:.4f}'.format(i) for i in row])
        print('\n')

def getRocId(rocTable, id):
    # get a roc table entry by the ID
    
    for rocKey, rocElem in rocTable.items():
        if (rocElem.id == id):
            return rocElem
    return None    


if __name__ == "__main__":
    
    filename = "../WrRocDefaults.xml"
    rocTable = storeROC(filename)
    
    for rocKey, rocElem in sorted(rocTable.items()):
        printROC(rocElem)

    print("\n\nGet ROC By ID :" )   
    printROC(getRocId(rocTable, 1))
    
    
    # add delay if before console closes
    time.sleep(3)
        
