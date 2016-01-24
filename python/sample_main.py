# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger

from pygame import time
import math
import time as tm
from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp

VERBOSE = 1;

# Create data objects    
myPlant = Plant()
hSink = UnityUdp("192.168.1.24")
hMyo = MyoUdp()#("192.168.1.3")

# represents the overhead associated with the main loop compared to the fixed rate output (50Hz)
numUpdates = 0
try: 
    # setup main loop control
    time_elapsed_since_last_action = 0
    clock = time.Clock()
    print("Running...")
    while True: # main loop
        numUpdates = numUpdates + 1
        
        # the following method returns the time since its last call in milliseconds
        # it is good practice to store it in a variable called 'dt'
        dt = clock.tick() 
    
        #tm.sleep(0.001)
        myPlant.update(dt)
        
        
        time_elapsed_since_last_action += dt
        # dt is measured in milliseconds, therefore 20 ms = 0.02 seconds = 50Hz
        if time_elapsed_since_last_action >= 20:

            # perform joint update
            vals = hMyo.getAngles()
            myPlant.position[3] = vals[1] + math.pi/2
            
            # transmit output
            hSink.sendJointAngles(myPlant.position)
            
            if VERBOSE:
                print(("%4d" % numUpdates, "%8.4f" % myPlant.position[3], "%8.4f" % myPlant.position[4] ))

            # reset timing counter vars
            numUpdates = 0;
            time_elapsed_since_last_action = 0 # reset it to 0 so you can count again
            
finally:
    print(hMyo.emg_buffer)
    hSink.close()
    hMyo.close()
