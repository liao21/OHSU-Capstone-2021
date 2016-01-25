import numpy as np

def feature_extract(windowData):
    #compute features
    ssc_thresh=0.05
    zc_thresh=0.05

    nSamples,nChannels=windowData.shape

    MAV = np.zeros(nChannels)
    LEN = np.zeros(nChannels)
    ZC = np.zeros(nChannels)
    SSC = np.zeros(nChannels)
    VAR = np.zeros(nChannels)

    t=0.0
    for iChannel in range(0,nChannels):
        y=windowData[:,iChannel]
        dy=np.diff(y)
        MAV[iChannel]=np.mean(abs(y))
        LEN[iChannel]=np.sum(abs(dy))
        ZC[iChannel]=0
        SSC[iChannel]=0
        VAR[iChannel]=np.var(y)
        for iSample in range(1,nSamples-1):

            # Define criteria for crossing zero
            zeroCross=(y[iSample] - t > 0 and y[iSample + 1] - t < 0) or (y[iSample] - t < 0 and y[iSample + 1] - t > 0)
            overThreshold=abs(y[iSample] - t - y[iSample + 1] - t) > zc_thresh
            if zeroCross and overThreshold:
                # Count a zero cross
                ZC[iChannel]=ZC[iChannel] + 1
            
            # Define criteria for counting slope sign changes
            signChange = (y[iSample] > y[iSample - 1]) and (y[iSample] > y[iSample + 1]) or (y[iSample] < y[iSample - 1]) and (y[iSample] < y[iSample + 1])
            overThreshold=abs(y[iSample] - y[iSample + 1]) > ssc_thresh or abs(y[iSample] - y[iSample - 1]) > ssc_thresh
            if signChange and overThreshold:
                # Count a slope change
                SSC[iChannel]=SSC[iChannel] + 1
    
    # Normalize features so they are independant of the window size    
    Fs=200
    
    # MAV shouldn't be normalized
    #
    
    normMAV=MAV
    normLEN=LEN / (nSamples / Fs)
    normZC=ZC / (nSamples / Fs)
    normSSC=SSC / (nSamples / Fs)
    normVAR=VAR / (nSamples / Fs)
    #normVAR=np.min(normVAR,50)
    #normMAV=np.min(normMAV,50)
    features=np.vstack((normMAV,normLEN,normZC,normSSC))
    return features


#import matplotlib.pyplot as plt
#import math
#
#emg_buffer = np.zeros((100,8))
#sinArray = np.sin(2*math.pi*10*np.linspace(0,1,num=100))
#
#emg_buffer[:,:1] = np.reshape(sinArray,(100,1))
#plt.plot(sinArray)
#
#f = feature_extract(emg_buffer)
#print(f[:,:1])
