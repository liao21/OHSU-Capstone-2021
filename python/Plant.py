# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

@author: R. Armiger
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger
from ROCtableClass import storeROC
import math

VERBOSE = 1;
DEBUG = 1;


   
class Plant(object):

    def __init__(self,dt,file):
        self.NUM_JOINTS = 27;
        self.position = [0.0]*self.NUM_JOINTS
        self.velocity = [0.0]*self.NUM_JOINTS
        self.limit = [45.0 * math.pi / 180.0]*self.NUM_JOINTS
        self.dt = dt

        # ----------|-Class Name------------------|-----Joint ID-------|-Direction-|
#        self.Joint={'No Movement'               : [                  [], 0 ],
#                    'Shoulder Flexion'          : [                 [0],+1 ],
#                    'Shoulder Extension'        : [                 [0],-1 ],
#                    'Shoulder Adduction'        : [                 [1],+1 ],
#                    'Shoulder Abduction'        : [                 [1],-1 ],
#                    'Humeral Internal Rotation' : [                 [2],+1 ],
#                    'Humeral External Rotation' : [                 [2],-1 ],
#                    'Elbow Flexion'             : [                 [3],+1 ],
#                    'Elbow Extension'           : [                 [3],-1 ],
#                    'Wrist Rotate In'           : [                 [4],+1 ],
#                    'Wrist Rotate Out'          : [                 [4],-1 ],
#                    'Wrist Adduction'           : [                 [5],+1 ],
#                    'Wrist Abduction'           : [                 [5],-1 ],
#                    'Wrist Flex In'             : [                 [6],+1 ],
#                    'Wrist Extend Out'          : [                 [6],-1 ],
#                    'Hand Open'                 : [ list(range(7,26+1)),-1 ],
#                    'Spherical Grasp'           : [ list(range(7,26+1)),+1 ]
#                    }

        # Implement ROC based hand commands 
        self.Joint = storeROC(file)  # dictionary of rocElems, key = grasp name
          
        if DEBUG:
            # debug, set a joint to move
            self.velocity[4] = 30.0 * math.pi / 180.0

    def update(self):
        # perform time integration based on elapsed time, dt
        
        for i,item in enumerate(self.position):  
            self.position[i] = self.position[i] + self.velocity[i]*self.dt;
        
            # TODO: only works symmetrically
            if abs(self.position[i]) > self.limit[i] :
                # Saturate at either high or low limit
                self.position[i] = math.copysign(self.limit[i],self.position[i])
                
                if DEBUG:
                    # Debug only 
                    self.velocity[i] = -self.velocity[i]

    def class_map(self, class_name):
        #return JointId, Direction    
    #   'No Movement' is not necessary in dict_Joint with '.get default return
        JointId, Direction = self.Joint.get(class_name,[ [], 0 ])
    
        return JointId, Direction
