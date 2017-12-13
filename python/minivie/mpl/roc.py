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
import xml.etree.cElementTree as xmlTree
import numpy as np
from scipy.interpolate import interp1d


class RocElement:
    name = ''  # grasp name
    id = 0  # grasp ID number
    joints = []  # array of joints involved
    waypoints = []  # array of waypoints
    angles = {}  # dictionary of angles for each waypoint
    impedance = {}  # dictionary of impedances for each waypoint


# function to read in ROC xml file and store as dictionary
def read_roc_table(file):
    import os, sys
    try:
        roc_table_tree = xmlTree.parse(file)  # store ROC table as an ElementTree
    except FileNotFoundError:
        # unrecoverable
        logging.critical('Failed to find file {} in {}. Program Halted.'.format(file, os.getcwd()))
        sys.exit(1)

    roc_table = {}  # make dictionary of ROC grasps
    root = roc_table_tree.getroot()

    # cycle through grasps in roc_table_tree
    for table in root.findall('table'):
        # child is an element, has tag and attributes
        name = table.find('name').text
        # create a rocElem object for that grasp
        elem = RocElement()
        elem.name = name
        elem.id = int(table.find('id').text)

        # Note the joint ids here are (-1) so that indices are 0-based for python
        elem.joints = [int(val) - 1 for val in table.find('joints').text.split(',')]
        # check each waypoint for angles and impedance measurements

        # initialize array that will be nWayPoints*nJoints
        angle_array = []
        elem.waypoints = []
        for waypoint in table.iter('waypoint'):
            index = float(waypoint.get('index'))
            # bisect.insort(elem.waypoints, index) # insert waypoint into sorted list of waypoints
            elem.waypoints.append(index)

            # use index as key for angles and impedance dictionaries
            angle_array.append([float(val) for val in waypoint.find('angles').text.split(',')])
            # elem.impedance[index] = [float(val) for val in waypoint.find('impedance').text.split(',')]
        elem.angles = np.reshape(np.asarray(angle_array), [-1, len(elem.joints)])
        roc_table[name] = elem
    # return completed dictionary
    return roc_table


def print_roc(roc_elem):
    if roc_elem is None:
        return

    # print an element in the ROC tables
    print("ROC NAME: '{}'".format(roc_elem.name))
    print("ROC ID: " + str(roc_elem.id))
    print("ROC JOINTS: [" + ' '.join(str(e) for e in roc_elem.joints) + "]")
    print("ROC WAYPOINTS: [" + ' '.join(str(e) for e in roc_elem.waypoints) + "]")
    print("ROC ANGLES " + str(roc_elem.angles.shape) + " :")
    for row in roc_elem.angles:
        print(['{:6.3f}'.format(i) for i in row])
    print('\n')


def get_roc_id(roc_table, roc_id):
    # get a roc table entry by the ID

    for roc_key, roc_elem in roc_table.items():
        if roc_elem.id == roc_id:
            return roc_elem
    logging.warning('Invalid ROC ID : {}'.format(roc_id))
    return None


def get_roc_values(roc_elem, val):
    x = np.array(roc_elem.waypoints)
    y = roc_elem.angles
    new_angles = interp1d(x, y, axis=0, kind='linear')(val)
    return new_angles


def main():
    filename = "../../WrRocDefaults.xml"
    roc_table = read_roc_table(filename)

    for rocKey, rocElem in sorted(roc_table.items()):
        print_roc(rocElem)

    print("\n\nDEMO Get ROC By ID:")
    print_roc(get_roc_id(roc_table, 1))

    # Get out of range ROC ID
    print("\n\nDEMO Get ROC By [INVALID] ID:")
    print_roc(get_roc_id(roc_table, 99))

    print("\n\nDEMO Get ROC Values:")
    new_values = get_roc_values(get_roc_id(roc_table, 1), 0.1)
    print(['{:6.3f}'.format(i) for i in new_values])


# Main Function (for demo)
if __name__ == "__main__":
    main()
