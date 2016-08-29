# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

The Plant object should hold the state information for the limb system.  This 
Allows generating velocity commands that are locally integrated to update position 
as a funciton of time.  The update() method should be called repeatedly at fixed intervals
to advance the kinematic state

Revisions:
7/26/2016: Reverted changes back to the simple Joint dictionary since ROC table not working
8/11/2016: Overhaul work by David Samson to allow for ROC table based limb trajectories

@author: R. Armiger
"""

#To setup some testing variables in the python shell:
# from Plant_Overhaul import Plant
# ROCfile = open('C:\\git\\minivie\\WrRocDefaults.xml', 'r')
# from ROCtableClass import storeROC
# b = storeROC(ROCfile)     #setup ROC Table variable
# ROCfile = open('C:\\git\\minivie\\WrRocDefaults.xml', 'r')
# a = Plant(0.02, ROCfile)  #setup plant variable
# c = b['Cylindrical']      #setup sample rocElement



# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger
from ROCtableClass import storeROC
import math
from scipy.interpolate import interp1d  #TODO use interp1d to generate angle functions for each joint per each pose. 
# https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#d-interpolation-interp1d
import time
from bisect import bisect


VERBOSE = 1;
DEBUG = 0;
   
class Plant(object):

    def __init__(self,dt,file):
        self.NUM_JOINTS = 27;
        self.position = [0.0]*self.NUM_JOINTS
        self.velocity = [0.0]*self.NUM_JOINTS
        self.limit = [45.0 * math.pi / 180.0]*self.NUM_JOINTS
        self.dt = dt
        
        self.ROC = storeROC(file)
        self.curPose = 'No Movement'
        self.curPercent = 0.0           #percentage of ROC pose complete
        #self.lastPose = 'No Movement'
        self.dictPose = True            #is the current motion from the ROC Table or dictionary
        self.fromWpt = '0.000'
        self.toWpt = '0.000'
        self.fromJnts = [False]*self.NUM_JOINTS  #list specifying which joints are in lerp at start of interval
        self.toJnts = [False]*self.NUM_JOINTS    #list specifying which joints are in lerp at end of interval
        self.fromAngs = []              #joint angles at start of lerp interval
        self.toAngs = []                #joint angles at end of lerp interval
        #self.lerpStart = time.time()   #time lerp interval started
        #self.LerpLength = 0            #

        # TODO: this is a final mapping for upper arm, but a temporary mapping for Hand entries, which 
        # should come form a ROC table
        
        # ----------|-Class Name------------------|-----Joint ID-------|-Direction-|
        self.Joint={'No Movement'               : [                 [] , []     ],
                    'Shoulder Flexion'          : [                 [0],[+1]    ],
                    'Shoulder Extension'        : [                 [0],[-1]    ],
                    'Shoulder Adduction'        : [                 [1],[+1]    ],
                    'Shoulder Abduction'        : [                 [1],[-1]    ],
                    'Humeral Internal Rotation' : [                 [2],[+1]    ],
                    'Humeral External Rotation' : [                 [2],[-1]    ],
                    'Elbow Flexion'             : [                 [3],[+1]    ],
                    'Elbow Extension'           : [                 [3],[-1]    ],
                    'Wrist Rotate In'           : [                 [4],[+1]    ],
                    'Wrist Rotate Out'          : [                 [4],[-1]    ],
                    'Wrist Adduction'           : [                 [5],[+1]    ],
                    'Wrist Abduction'           : [                 [5],[-1]    ],
                    'Wrist Flex In'             : [                 [6],[+1]    ],
                    'Wrist Extend Out'          : [                 [6],[-1]    ],
                    'Hand Open'                 : [ list(range(7,26+1)),[-1]*20 ],
                    'Spherical Grasp'           : [ list(range(7,26+1)),[+1]*20 ]
                    }

        # Implement ROC based hand commands 
        #self.Joint = storeROC(file)  # dictionary of rocElems, key = grasp name
          
        if DEBUG:
            # debug, set a joint to move
            self.velocity[4] = 30.0 * math.pi / 180.0

    def update(self, class_decision=None):
        if class_decision == None:
            class_decision = self.curPose
        
        self.dictPose = class_decision not in self.ROC
         
        if class_decision == self.curPose:# or class_decision == self.lastPose:
            #bc length of ROC poses are not specified, assuming that dt ~ %ofROC per each cycle. i.e. each pose is 1 second long
            if self.dictPose:
            #do basic dictionary control
                pass
            else:
                #do ROC based control
                if self.curPercent + dt <= float(self.toWpt):
                    #do normal ROC interp within current waypoints
                    pass
                else:
                    #update from and to waypoints/joints/angles and then do ROC interp
                    pass
                
        else:
            #set fromAngs to cur angles and toAngs to nearest waypoint angles

            pass
        
        #update state for next update 
        #self.lastPose = self.curPose
        self.curPose = class_decision
        #self.lerpStart = time.time()
        
        
        # # perform time integration based on elapsed time, dt
        
        # for i,item in enumerate(self.position):  
            # self.position[i] = self.position[i] + self.velocity[i]*self.dt;
        
            # # TODO: only works symmetrically
            # if abs(self.position[i]) > self.limit[i] :
                # # Saturate at either high or low limit
                # self.position[i] = math.copysign(self.limit[i],self.position[i])
                
                # if DEBUG:
                    # # Debug only 
                    # self.velocity[i] = -self.velocity[i]

                        
    def getWptInt(self, elapsedPercent, wptInit=None, pose=None):
        #return start/end waypoints that capture the elapsed time
        if elapsedPercent < 0:
            raise ValueError('Elapsed percent must be greater than 0. Value passed: ' + str(elapsedPercent))
        
        if pose == None:
            pose = self.curPose
        
        if wptInit != None:
            #add offset time from start of pose motion to wptInit
            elapsedPercent += float(wptInit)
        
        wptList = self.ROC[pose].waypoints
        
        i = bisect([float(i) for i in wptList], elapsedPercent)
        
        if i > len(wptList)-1:
            wptStart = wptList[-1]
            wptEnd = wptList[-1]
        elif i == len(wptList)-1:
            wptStart = wptList[-2]
            wptEnd = wptList[-1]
        else:
            wptStart = wptList[i-1]
            wptEnd = wptList[i]

                
        return wptStart, wptEnd
        
    def lerp(self, elapsedPercent, intSize=1):
        #construct full length joint arrays to do lerp on
        lerpFrom = [(self.fromAngs[i] if self.fromJnts[i] else self.position[i]) for i in list(range(self.NUM_JOINTS))]
        lerpTo = [(self.toAngs[i] if self.toJnts[i] else self.position[i]) for i in list(range(self.NUM_JOINTS))]
        lerpCurrent = [((lerpTo[i]-lerpFrom[i])/intSize)*elapsedPercent + lerpFrom[i] for i in list(range(self.NUM_JOINTS))]
        return lerpCurrent
        
    def lerpGeneric(self, elapsedPercent, lerpFrom, lerpTo, intSize=1):
        lerpCurrent = [((lerpTo[i]-lerpFrom[i])/intSize)*elapsedPercent + lerpFrom[i] for i in list(range(len(lerpTo)))]
        return lerpCurrent
    
    
    ####KEEP FOR SEMI-BACKWARDS COMPATIBILITY#### (need to update code that uses this so that direction is an array with len(JointId))
    def class_map(self, class_name):
        #return JointId, Direction    
    #   'No Movement' is not necessary in dict_Joint with '.get default return
        #JointId, Direction = self.Joint.get(class_name,[ [], 0 ])
        JointId, Direction = self.Joint[class_name]
    
        return JointId, Direction

        
    def joint_state(self, class_name):
        #return the current joint angle state given the next class decision
        
        self.update(class_name)
        #<>
        
        return self.position
    
        
    def getClosestWaypoint(self, pose):
        bestWpt = None
        bestErr = None
        print('Getting Closest Waypoint.')
        for i in self.ROC[pose].joints:
            position = [self.position[i-1] for i in self.ROC[pose].joints]
        
        for waypoint in self.ROC[pose].angles:
            err = compareArrays(self.ROC[pose].angles[waypoint], position)
            if bestErr == None or err < bestErr:
                bestErr = err
                bestWpt = waypoint
        
        return bestWpt, bestErr



def arrayDiff(arr1, arr2):
    #used to compare current joint positions with ROC waypoints to find closest match
    if len(arr1) != len(arr2):
        raise ValueError('Lengths of arrays to compare is different.')

    error = 0       
    for i, angle in enumerate(arr1):
        err = (angle - arr2[i])
        err = err*err
        error += err
    
    return error**0.5