# -*- coding: utf-8 -*-
"""
Test threading with locks. Without the lock, counters 1 and 2 get updated out of synch and 
reading the values in the main loop returns different values.  One lock is in place before the
counter increments and another lock is placed around the read operation. 

@author: R. Armiger
"""
import threading
import time


class BackgroundUpdater(object):
    """ Class for receiving Myo Armband data via UDP"""
    def __init__(self):

        self.runThread = True
        self.__counter1 = 0
        self.__counter2 = 0

        # Create threadsafe lock
        self.lock = threading.Lock()
        
        # Create a thread for processing new data
        # Create two threads as follows
        self.thread = threading.Thread(target=self.counter)
        self.thread.start()

    def counter(self):
        """ Convert incoming bytes to emg, quaternion, accel, and ang rate """

        # Loop forever to recv data
        while self.runThread:
            # without a lock here the conters would have different values between reads
            with self.lock:
                self.__counter1 += 1
                self.__counter2 += 1

    def get_values(self):
        # without a lock here the counters would have different values between reads
        with self.lock:
            a1 = self.__counter1
            time.sleep(0.01)
            a2 = self.__counter2
            return a1, a2
# main
h = BackgroundUpdater()

for i in range(100):

    A, B = h.get_values()
    
    print("A={} B={}".format(A, B))
    
    if A != B:
        print("ERROR")
        h.runThread = False
        break

h.runThread = False
h.thread.join()
