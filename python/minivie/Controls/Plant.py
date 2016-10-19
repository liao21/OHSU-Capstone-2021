# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

The Plant object should hold the state information for the limb system.  This
Allows generating velocity commands that are locally integrated to update position
as a function of time.  The update() method should be called repeatedly at fixed intervals
to advance the kinematic state

Usage:

from the python\minivie folder:

from Controls import Plant

Plant.main()

Revisions:
2016JUL26: Reverted changes back to the simple Joint dictionary since ROC table not working
2016OCT07: Added joint limit from xml file

@author: R. Armiger
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger
import os
import math
import time
import logging
import numpy as np
from enum import IntEnum
import MPL.RocTableClass as ROC
from Utilities import UserConfig as UC

# for demo
from MPL.UnityUdp import UnityUdp as hSink


class MplJointEnum(IntEnum):
    '''
        Allows enumeration reference for joint angles
        
        Example:
        
        MplJointEnum(1).name
        'SHOULDER_AB_AD'
                
        
    '''
    SHOULDER_FE       = 0
    SHOULDER_AB_AD    = 1
    HUMERAL_ROT       = 2
    ELBOW             = 3
    WRIST_ROT         = 4
    WRIST_AB_AD       = 5
    WRIST_FE          = 6
    INDEX_AB_AD       = 7
    INDEX_MCP         = 8
    INDEX_PIP         = 9
    INDEX_DIP         = 10
    MIDDLE_AB_AD      = 11
    MIDDLE_MCP        = 12
    MIDDLE_PIP        = 13
    MIDDLE_DIP        = 14
    RING_AB_AD        = 15
    RING_MCP          = 16
    RING_PIP          = 17
    RING_DIP          = 18
    LITTLE_AB_AD      = 19
    LITTLE_MCP        = 20
    LITTLE_PIP        = 21
    LITTLE_DIP        = 22
    THUMB_CMC_AB_AD   = 23
    THUMB_CMC_FE      = 24
    THUMB_MCP         = 25
    THUMB_DIP         = 26
    NUM_JOINTS        = 27


class Plant(object):
    '''
        The main state-space integrator for the system.
        Allows setting velocity commands and then as long as they execute
        the arm will move in that direction.  position parameters will be updated
        automatically so that position commands can be send to output devices
        Additionally limits are handled here as well as roc table lookup
    '''
    def __init__(self,dt,rocFilename):

        mpl = MplJointEnum
        self.JointPosition = np.zeros(mpl.NUM_JOINTS)
        self.JointVelocity = np.zeros(mpl.NUM_JOINTS)

        # Load limits from xml config file
        self.lowerLimit = [0.0] * mpl.NUM_JOINTS
        self.upperLimit = [30.0] * mpl.NUM_JOINTS
        
        for i in range(mpl.NUM_JOINTS):
            limit = UC.getUserConfigVar(mpl(i).name +'_LIMITS',(0.0, 30.0))
            self.lowerLimit[i] = limit[0] * math.pi / 180
            self.upperLimit[i] = limit[1] * math.pi / 180

        self.dt = dt

        self.rocTable = ROC.readRoc(rocFilename)

        # currently selected ROC for arm motion
        self.RocId = ''
        self.RocPosition = 0.0
        self.RocVelocity = 0.0
        
        # currently selected ROC for hand motion
        self.GraspId = ''
        self.GraspPosition = 0.0
        self.GraspVelocity = 0.0
        
    def classMap(self, class_name):
        # Map a pattern recognition class name to a joint command
        #
        # The objective of this funciton is to decide how to interpret a class decision 
        # as a movement action.
        #
        # return JointId, Direction, IsGrasp, Grasp
        #
        #   'No Movement' is not necessary in dict_Joint with '.get default return
        #JointId, Direction = self.Joint.get(class_name,[ [], 0 ])
        
        classInfo = {'IsGrasp':0, 'JointId':None,'Direction':0,'GraspId':None }
        mpl = MplJointEnum
        # Map classes to joint id and direction of motion
        # Class Name: IsGrasp, JointId, Direction, GraspId
        cLookup =  {'No Movement'               : [0, None                , 0 , None],
                    'Shoulder Flexion'          : [0, mpl.SHOULDER_FE     ,+1 , None],
                    'Shoulder Extension'        : [0, mpl.SHOULDER_FE     ,-1 , None],
                    'Shoulder Adduction'        : [0, mpl.SHOULDER_AB_AD  ,+1 , None],
                    'Shoulder Abduction'        : [0, mpl.SHOULDER_AB_AD  ,-1 , None],
                    'Humeral Internal Rotation' : [0, mpl.HUMERAL_ROT     ,+1 , None],
                    'Humeral External Rotation' : [0, mpl.HUMERAL_ROT     ,-1 , None],
                    'Elbow Flexion'             : [0, mpl.ELBOW           ,+1 , None],
                    'Elbow Extension'           : [0, mpl.ELBOW           ,-1 , None],
                    'Wrist Rotate In'           : [0, mpl.WRIST_ROT       ,+1 , None],
                    'Wrist Rotate Out'          : [0, mpl.WRIST_ROT       ,-1 , None],
                    'Wrist Adduction'           : [0, mpl.WRIST_AB_AD     ,+1 , None],
                    'Wrist Abduction'           : [0, mpl.WRIST_AB_AD     ,-1 , None],
                    'Wrist Flex In'             : [0, mpl.WRIST_FE        ,+1 , None],
                    'Wrist Extend Out'          : [0, mpl.WRIST_FE        ,-1 , None],
                    'Hand Open'                 : [1, None                ,-1 , None],
                    'Spherical Grasp'           : [1, None                ,+1 , 'Spherical']
                    }
       
        if class_name in cLookup:
            classInfo['IsGrasp'], classInfo['JointId'], classInfo['Direction'], classInfo['GraspId'] = cLookup[class_name]
        else:
            logging.warn('Unmatched class name {}'.format(class_name))
 
        return classInfo
        
    def newStep(self):
        # set all velocities to 0 to prepare for a new timestep 
        # Typically followed by a call to setVelocity
        nJoints = MplJointEnum.NUM_JOINTS
        # reset velocity
        self.JointVelocity[:] = 0.0  
        self.RocVelocity = 0.0
        self.GraspVelocity = 0.0

    def setRocVelocity(self,rocVelocity):
        # set the velocities of the roc
        self.RocVelocity = rocVelocity

    def setGraspVelocity(self,graspVelocity):
        # set the velocities of the grasp roc
        self.GraspVelocity = graspVelocity
        
    def setJointVelocity(self,jointId, jointVelocity):
        # set the velocities of the list of joint ids
        if jointId is not None:
            self.JointVelocity[jointId] = jointVelocity

    def update(self):
        # perform time integration based on elapsed time, dt

        # integrate roc values
        self.RocPosition += self.RocVelocity*self.dt
        self.GraspPosition += self.GraspVelocity*self.dt
        # Apply limits
        self.RocPosition = np.clip(self.RocPosition,0,1)
        self.GraspPosition = np.clip(self.GraspPosition,0,1)

        # integrate joint positions from velocity commands
        self.JointPosition += self.JointVelocity*self.dt;

        # set positions based on roc commands
        # hand positions will always be roc
        if self.RocId in self.rocTable :
            newVals = ROC.getRocValues( self.rocTable[self.RocId] , self.RocPosition)
            self.JointPosition[self.rocTable[self.RocId].joints] = newVals
        if self.GraspId in self.rocTable :
            newVals = ROC.getRocValues( self.rocTable[self.GraspId] , self.GraspPosition)
            self.JointPosition[self.rocTable[self.GraspId].joints] = newVals
        
        # Apply limits
        self.JointPosition = np.clip(self.JointPosition,self.lowerLimit,self.upperLimit)

def main():

    # get default roc file.  This should be run from python\minivie as home, but 
    # also support calling from module directory (Utilities)
    rocFilename = "../../WrRocDefaults.xml"
    if os.path.split(os.getcwd())[1] == 'Controls':
        rocFilename = '../' + rocFilename
      
    dt = 0.02
    p = Plant(dt, rocFilename)
    
    sink = hSink()
    sink.connect()
    
    print('LOWER LIMITS:')
    print(p.lowerLimit)
    print('UPPER LIMITS:')
    print(p.upperLimit)

    timeBegin = time.time()
    while time.time() < (timeBegin + 1.5): # main loop
        time.sleep(dt)
        class_name = 'Shoulder Flexion'
        classInfo = p.classMap(class_name)

        # Set joint velocities
        p.newStep()
        # set the mapped class
        p.setJointVelocity(classInfo['JointId'],classInfo['Direction'])    
        # set a few other joints with a new velocity
        p.setJointVelocity([MplJointEnum.ELBOW, MplJointEnum.WRIST_AB_AD],2.5)
        
        # set a grasp state        
        #p.GraspId = 'rest'
        p.GraspId = 'Spherical'
        p.setGraspVelocity(0.5)
        
        p.update()
        
        sink.sendJointAngles(p.JointPosition)

        # Print first 7 joints
        ang = ''.join('{:6.1f}'.format(k*180/math.pi) for k in p.JointPosition[:7] )
        print('Angles (deg):' + ang + ' | Grasp Value: {:6.3f}'.format(p.GraspPosition))

    sink.close()
    
# Main Function (for demo)
if __name__ == "__main__":
    main()