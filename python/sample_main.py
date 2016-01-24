# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

from pygame import time
import math

from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp

VERBOSE = 1;

# Create data objects    
myPlant = Plant()
hSink = UnityUdp("192.168.1.24")
hMyo = MyoUdp()

# represents the overhead associated with the main loop compared to the fixed rate output (50Hz)
numUpdates = 0
try: 
    # setup main loop control
    time_elapsed_since_last_action = 0
    clock = time.Clock()
    while True: # main loop
        numUpdates = numUpdates + 1
        
        # the following method returns the time since its last call in milliseconds
        # it is good practice to store it in a variable called 'dt'
        dt = clock.tick() 
    
        data = hMyo.getData()
        myPlant.update(dt)
        
        
        time_elapsed_since_last_action += dt
        # dt is measured in milliseconds, therefore 20 ms = 0.02 seconds = 50Hz
        if time_elapsed_since_last_action >= 20:
            print(("%8.4f" % myPlant.position[2], "%4d" % numUpdates ))
            vals = hMyo.getAngles()
            myPlant.position[3] = vals[1] + math.pi/2
            time_elapsed_since_last_action = 0 # reset it to 0 so you can count again
            hSink.sendJointAngles(myPlant.position)
            numUpdates = 0;
            
finally:
    print(hMyo.emg_buffer)
    hSink.close()
    hMyo.close()
