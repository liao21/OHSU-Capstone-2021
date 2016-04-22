# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 08:21:58 2016

@author: carrolm1
"""
import xml.etree.cElementTree as ET
import time

timeBegin = time.time()

# give temporary file to practice on
filename = '/Users/lydiacarroll/Documents/MiniVIE/minivie/GraspAndWholeArmRoc.xml'
    
class rocElem:
   def __init__(self, name):
       self.name = "" # grasp name
       self.id = 0 # grasp ID number
       self.joints = [] # array of joints involved
       self.waypoints = 0 # number of waypoints
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
        elem.id = table.find('id').text
        elem.joints = table.find('joints').text
        # check each waypoint for angles and impedance measurements
        for waypoint in table.iter('waypoint'):
            index = waypoint.get('index')
            # use index as key for angles and impedance dictionaries
            elem.angles[index] = waypoint.find('angles').text
            elem.impedance[index] = waypoint.find('impedance').text
        rocTable[name] = elem
    # return completed dictionary
    return rocTable
    
   
timeElapsed  = time.time() - timeBegin

def main():
    print(timeElapsed)
    print (storeROC(filename))
    
main()

        
    