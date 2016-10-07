# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

The Plant object should hold the state information for the limb system.  This
Allows generating velocity commands that are locally integrated to update position
as a funciton of time.  The update() method should be called repeatedly at fixed intervals
to advance the kinematic state

Revisions:
2016JUL26: Reverted changes back to the simple Joint dictionary since ROC table not working
2016OCT07: Added joint limit from xml file

@author: R. Armiger
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger
import math
from UserConfigXml import userConfig

VERBOSE = 1;
DEBUG = 0;

class Plant(object):

    def __init__(self,dt,file):

        self.JOINT = {\
            'SHOULDER_FE'       : 0, \
            'SHOULDER_AB_AD'    : 1, \
            'HUMERAL_ROT'       : 2, \
            'ELBOW'             : 3, \
            'WRIST_ROT'         : 4, \
            'WRIST_AB_AD'       : 5, \
            'WRIST_FE'          : 6, \
            'INDEX_AB_AD'       : 7, \
            'INDEX_MCP'         : 8, \
            'INDEX_PIP'         : 9, \
            'INDEX_DIP'         : 10, \
            'MIDDLE_AB_AD'      : 11, \
            'MIDDLE_MCP'        : 12, \
            'MIDDLE_PIP'        : 13, \
            'MIDDLE_DIP'        : 14, \
            'RING_AB_AD'        : 15, \
            'RING_MCP'          : 16, \
            'RING_PIP'          : 17, \
            'RING_DIP'          : 18, \
            'LITTLE_AB_AD'      : 19, \
            'LITTLE_MCP'        : 20, \
            'LITTLE_PIP'        : 21, \
            'LITTLE_DIP'        : 22, \
            'THUMB_CMC_AB_AD'   : 23, \
            'THUMB_CMC_FE'      : 24, \
            'THUMB_MCP'         : 25, \
            'THUMB_DIP'         : 26, \
            'NUM_JOINTS'        : 27}

        JOINT = self.JOINT

        self.position = [0.0]*JOINT['NUM_JOINTS']
        self.velocity = [0.0]*JOINT['NUM_JOINTS']

        # Load limits from xml config file
        UC = userConfig(filename)
        self.lowerLimit = [0.0] * JOINT['NUM_JOINTS']
        self.upperLimit = [30.0] * JOINT['NUM_JOINTS']
        
        for (name,id) in JOINT.items():
            if name != 'NUM_JOINTS':
                limit = UC.getUserConfigVar(name+'_LIMITS',(0.0, 30.0))
                self.lowerLimit[id] = limit[0] * math.pi / 180
                self.upperLimit[id] = limit[1] * math.pi / 180

        self.dt = dt

        # TODO: this is a final mapping for upper arm, but a temporary mapping for Hand entries, which 
        # should come form a ROC table

        # ----------|-Class Name------------------|-----Joint ID------------|-Direction-|
        self.Class={'No Movement'               : [                     []  , 0 ],
                    'Shoulder Flexion'          : [JOINT['SHOULDER_FE']     ,+1 ],
                    'Shoulder Extension'        : [JOINT['SHOULDER_FE']     ,-1 ],
                    'Shoulder Adduction'        : [JOINT['SHOULDER_AB_AD']  ,+1 ],
                    'Shoulder Abduction'        : [JOINT['SHOULDER_AB_AD']  ,-1 ],
                    'Humeral Internal Rotation' : [JOINT['HUMERAL_ROT']     ,+1 ],
                    'Humeral External Rotation' : [JOINT['HUMERAL_ROT']     ,-1 ],
                    'Elbow Flexion'             : [JOINT['ELBOW']           ,+1 ],
                    'Elbow Extension'           : [JOINT['ELBOW']           ,-1 ],
                    'Wrist Rotate In'           : [JOINT['WRIST_ROT']       ,+1 ],
                    'Wrist Rotate Out'          : [JOINT['WRIST_ROT']       ,-1 ],
                    'Wrist Adduction'           : [JOINT['WRIST_AB_AD']     ,+1 ],
                    'Wrist Abduction'           : [JOINT['WRIST_AB_AD']     ,-1 ],
                    'Wrist Flex In'             : [JOINT['WRIST_FE']        ,+1 ],
                    'Wrist Extend Out'          : [JOINT['WRIST_FE']        ,-1 ],
                    'Hand Open'                 : [ list(range(7,26+1))     ,-1 ],
                    'Spherical Grasp'           : [ list(range(7,26+1))     ,+1 ]
                    }

        # Implement ROC based hand commands
        #self.Joint = storeROC(file)  # dictionary of rocElems, key = grasp name

    def update(self):
        # perform time integration based on elapsed time, dt

        for i,item in enumerate(self.position):
            self.position[i] = self.position[i] + self.velocity[i]*self.dt;

            # Apply limits
            # Saturate at high limit
            if self.position[i] > self.upperLimit[i] : self.position[i] = self.upperLimit[i]

            # Saturate at low limit
            if self.position[i] < self.lowerLimit[i] : self.position[i] = self.lowerLimit[i]

    def class_map(self, class_name):
        #return JointId, Direction
        #   'No Movement' is not necessary in dict_Joint with '.get default return
        #JointId, Direction = self.Joint.get(class_name,[ [], 0 ])
        JointId, Direction = self.Class[class_name]

        return JointId, Direction

# Main Function (for demo)
if __name__ == "__main__":
    
    filename = "../user_config.xml"
    
    p = Plant(0.02,filename)
        
    print(p.lowerLimit)
    print(p.upperLimit)
    
    