# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 16:25:14 2016

Perform feature extraction, veoctorized

@author: R. Armiger
"""

import numpy as np

def feature_extract(y):
    #compute features
    zc_thresh = 0.15
    ssc_thresh = 0.15

    # Number of Samples
    n = y.shape[0]

    # Normalize features so they are independant of the window size    
    Fs=200

    t=0.0
    
    # Compute derivative
    dEmg = np.diff(y,axis=0)
    
    # Compute MAV across all samples (axis=0)
    MAV = np.mean(abs(y),0)     # MAV shouldn't be normalized
    LEN = np.sum(abs(dEmg),axis=0) * Fs / n
    # Criteria for crossing zero
    # zeroCross=(y[iSample] - t > 0 and y[iSample + 1] - t < 0) or (y[iSample] - t < 0 and y[iSample + 1] - t > 0)
    # overThreshold=abs(y[iSample] - t - y[iSample + 1] - t) > zc_thresh
    # if zeroCross and overThreshold:
    #     # Count a zero cross
    #     ZC[iChannel]=ZC[iChannel] + 1
    ZC = np.sum(\
         ((y[0:n-1,:] - t > 0) & (y[1:n,:] - t < 0) | \
         (y[0:n-1,:] - t < 0) & (y[1:n,:] - t > 0)) & \
         (abs(y[0:n-1,:] - t - y[1:n,:] - t) > zc_thresh)
         ,axis=0) * Fs / n

    # Criteria for counting slope sign changes
    # signChange = (y[iSample] > y[iSample - 1]) and (y[iSample] > y[iSample + 1]) or (y[iSample] < y[iSample - 1]) and (y[iSample] < y[iSample + 1])
    # overThreshold=abs(y[iSample] - y[iSample + 1]) > ssc_thresh or abs(y[iSample] - y[iSample - 1]) > ssc_thresh
    # if signChange and overThreshold:
    #     # Count a slope change
    #     SSC[iChannel]=SSC[iChannel] + 1
    SSC = np.sum(\
          ((y[1:n-1,:] > y[0:n-2,:]) & (y[1:n-1,:] > y[2:n,:]) | \
          (y[1:n-1,:] < y[0:n-2,:]) & (y[1:n-1,:] < y[2:n,:])) & \
          ((abs(y[1:n-1,:] - y[2:n,:]) > ssc_thresh) | (abs(y[1:n-1,:] - y[0:n-2,:]) > ssc_thresh)) \
          ,axis=0) * Fs / n

         
    #VAR = np.var(y,axis=0) * Fs / n
    
    features=np.vstack((MAV,LEN,ZC,SSC))
    return features


#import matplotlib.pyplot as plt
#import math
#import timeit
#
#NUM = 2000
#emg_buffer = np.zeros((NUM,8))
#sinArray = np.sin(2*math.pi*10*np.linspace(0,1,num=NUM))
#
#emg_buffer[:,:1] = np.reshape(sinArray,(NUM,1))
#emg_buffer[:,:7] = np.reshape(sinArray,(NUM,1))
#plt.plot(sinArray)
#
#
#start_time = timeit.default_timer()
## code you want to evaluate
#f = feature_extract(emg_buffer)
## code you want to evaluate
#elapsed = timeit.default_timer() - start_time
#print(elapsed)
#
#print(f)


