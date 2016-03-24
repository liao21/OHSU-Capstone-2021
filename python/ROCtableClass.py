# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 08:21:58 2016

@author: carrolm1
"""
import xml.etree.cElementTree as ET
import time

timeBegin = time.time()

# give temporary file to practice on
filename = 'C:\git\minivie\GraspAndWholeArmRoc.xml'
rocTableTree = ET.parse(filename) # store ROC table as an ElementTree
rocTable = {} # make dictionary of ROC grasps
root = rocTableTree.getroot()

i = 0
    
class rocElem:
   def __init__(self, name):
       self.name = "" # grasp name
       self.id = 0 # grasp ID number
       self.joints = [] # array of joints involved
       self.waypoints = 0 # number of waypoints
       self.angles = {} # dictionary of angles for each waypoint
       self.impedance = {} # dictionary of impedances for each waypoint
       
       
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
   
timeElapsed  = time.time() - timeBegin
print(timeElapsed)
        
    