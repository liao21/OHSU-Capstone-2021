# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:38:47 2016

@author: armigrs1
"""

# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

import math

VERBOSE = 1;
DEBUG = 1;
   
class Plant(object):

    def __init__(self,dt):
        NUM_JOINTS = 27;
        self.position = [0.0]*NUM_JOINTS
        self.velocity = [0.0]*NUM_JOINTS
        self.limit = [45.0 * math.pi / 180.0]*NUM_JOINTS
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
