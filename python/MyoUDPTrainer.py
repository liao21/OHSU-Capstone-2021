
"""
Created on Tue Jul 19 11:16:36 2016

Initial creation of the training methods for LDA classification in Python

@author: D. Samson
"""

import sys
import time
#import math
#import time
import numpy as np
from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp
from TrainingUdp import TrainingUdp
from feature_extract import feature_extract
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis




#VERBOSE = 1    #arg passed in

#frequency in Hz
freq = 50.0
dt = 1.0/freq
#dt = 0.02  # seconds per loop.  50Hz update

# Create data objects

# Singal Source get external bio-signal data
hMyo = MyoUdp()

# Training Data holds data labels 
hTrain = TrainingUdp()

# Plant maintains current limb state (positions) during velocity control
#hPlant = Plant(dt)

## Sink is output to ouside world (in this case to VIE)
hSink = UnityUdp() #("192.168.1.24")



# construct as python arrays, then convert to numpy arrays
TrainingData = [] #np.array([[]])
TrainingClass = [] #np.array([])
TrainingName = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp', 'No Movement']


print('\n\nBeginning training Regime in 5 seconds...')
print('(Ready for first pose "Wrist Rotate In")')
time.sleep(5)

print('\n')
for index, name in enumerate(TrainingName):
	print('Pose: ' + name)
	time.sleep(3)
	for i in list(range(20)):
		loopStart = time.time()
		emgData = hMyo.getData()*0.01
		f = (feature_extract(emgData)).tolist()[0]
		print('%8.4f %8.4f %8.4f %8.4f' % (f[0], f[8], f[16], f[24]))
		#print(f)
		#print('Emg Buffer: \n' + str(hMyo.getData()))
		TrainingData.append(f)
		TrainingClass.append([index])
		
		if time.time() - loopStart < dt:
			time.sleep(dt - (time.time() - loopStart))
		else:
			print("Timing Overload")





X = np.array(TrainingData)
y = np.array(TrainingClass)
print('shape of X: ' + str(X.shape))
print('shape of y: ' + str(y.shape))
clf = LinearDiscriminantAnalysis()
clf.fit(X, y)

for i in list(range(1000)):
	print('prediction: ' + TrainingName[clf.predict(feature_extract(hMyo.getData()*0.01))])
	time.sleep(dt)

print('\n')
	

#print("")
#print("EMG Buffer:")
#print(hMyo.getData())
#print("Last timeElapsed was: ", timeElapsed)
#print("")
#print("Cleaning up...")
#print("")
hSink.close()
hMyo.close()
hTrain.close()
#file.close()     #close file  
