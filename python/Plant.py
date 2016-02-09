# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

@author: R. Armiger
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

import math

VERBOSE = 1;
DEBUG = 1;
   
class Plant(object):

    def __init__(self,dt):
        self.NUM_JOINTS = 27;
        self.position = [0.0]*self.NUM_JOINTS
        self.velocity = [0.0]*self.NUM_JOINTS
        self.limit = [45.0 * math.pi / 180.0]*self.NUM_JOINTS
        self.dt = dt

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

    def class_map(self,class_name):
        # TODO: Need a better way to handle this mapping
        JointId = [];
        Direction = 0;
        #return JointId, Direction    
    
    
    
        if class_name == 'No Movement':
            JointId = [];
            Direction = 0;
        elif class_name == 'Shoulder Flexion':
            JointId = 0
            Direction = +1;
        elif class_name == 'Shoulder Extension':
            JointId = 0;
            Direction = -1;
        elif class_name == 'Shoulder Adduction':
            JointId = 1;
            Direction = +1;
        elif class_name == 'Shoulder Abduction':
            JointId = 1;
            Direction = -1;
        elif class_name == 'Humeral Internal Rotation':
            JointId = 2;
            Direction = +1;
        elif class_name =='Humeral External Rotation':
            JointId = 2;
            Direction = -1;
        elif class_name == 'Elbow Flexion':
            JointId = 3;
            Direction = +1;
        elif class_name == 'Elbow Extension':
            JointId = 3;
            Direction = -1;
        elif class_name == 'Wrist Rotate In':
            JointId = 4;
            Direction = +1;
        elif class_name == 'Wrist Rotate Out':
            JointId = 4;
            Direction = -1;
        elif class_name == 'Wrist Adduction':
            JointId = 5;
            Direction = +1;
        elif class_name == 'Wrist Abduction':
            JointId = 5;
            Direction = -1;
        elif class_name == 'Wrist Flex In':
            JointId = 6;
            Direction = +1;
        elif class_name == 'Wrist Extend Out':
            JointId = 6;
            Direction = -1;
        elif class_name == 'Hand Open':
            JointId = [7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]
            Direction = -1;
        elif class_name == 'Spherical Grasp':
            JointId = [7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]
            Direction = +1;
        else :
            # check standard grasps, otherwise unmatched
            JointId = [];
            Direction = [];
            
        if type(JointId) is int:
            JointId = [JointId]
        return JointId, Direction
