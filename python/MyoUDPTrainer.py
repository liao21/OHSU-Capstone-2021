
"""
Created on Tue Jul 19 11:16:36 2016

Initial creation of the training methods for LDA classification in Python

--VERBOSE  set to 2 or higher
Output timing information 

Most of the functionality is controlled by command line flags, so if you want 
 to do a demo (plus timing info), you can run: 
“python MyoUDPTrainer.py --VERBOSE 2 --TRAIN 20  --PREDICT 1000”. 
Training builds on whatever saved training data is in the directory, so if you 
want to train from scratch, delete all of the files in the “\python\training_data\” 
folder, and then rerun the script with the train flag.


@author: D. Samson
"""

import sys
import time
import math
import numpy as np
from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp
from TrainingUdp import TrainingUdp
from feature_extract import feature_extract
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
import os
from os.path import isfile
import argparse
from sklearn.externals import joblib


def main():
	# get path to where this script is being run
	# any saved training data will be save here in a folder called "\training_data"
	path = os.path.dirname(os.path.abspath(__file__))
	
    #parse command-line arguments
	#want to combine train and number of samples
	#maybe debug should be true if verbose > 1
	parser = argparse.ArgumentParser(description='Myo Trainer Command-line Arguments:')
	parser.add_argument('-q', '--QUADRATIC', help='Run quadratic analysis of data instead of linear', action='store_true')
	parser.add_argument('-t', '--TRAIN', help='Run training regime at start of program. Specify number of sample per class', default=0, type=int)
	parser.add_argument('-p', '--PREDICT', help='Run prediction sequence. Specify number of cycles to run for', default=0, type=int)
	parser.add_argument('-f', '--FREQUENCY', help='Set frequency to update at (Hz)', default=50, type=int)
	#parser.add_argument('-i', '--UDP_IP', help='IP address to send controls to', default='127.0.0.1')
	#parser.add_argument('-p', '--UDP_PORT', help='UDP port to send controls to', default=10001)
	parser.add_argument('-v', '--VERBOSE', help='How much console information. 0=minimal, 1=some, 2=more, etc.', default=1, type=int)
	#args relating to creating new data/etc.
	
	args = parser.parse_args()
	
	
	# Manage args here
	
	# Set quadratic mode
	quadratic = args.QUADRATIC
	
	# Samples per class
	train = args.TRAIN

	# Delta time between cycles
	dt = 1.0/args.FREQUENCY

	# Verbosity of program output.
	verb = args.VERBOSE
	
	# Number of cycles to predict for
	pcycles = args.PREDICT
		
	
	# Create data objects

	# Signal Source get external bio-signal data
	hMyo = MyoUdp()

	# Training Data holds data labels 
	#hTrain = TrainingUdp()

	ROCFile = open(path + '\\..\\WrRocDefaults.xml', 'r')
	
	# Plant maintains current limb state (positions) during velocity control
	hPlant = Plant(dt, ROCFile)

	# Sink is output to ouside world (in this case to VIE)
	hSink = UnityUdp() #("192.168.1.24")


	# Start of main program execution
	print('')
	
		

	# Check if data already exists
	# Manipulate data as python arrays, then convert to numpy arrays when final size reached
	saved = isfile(path + '\\training_data\\X.pkl') and isfile(path + '\\training_data\\y.pkl') and isfile(path + '\\training_data\\className.pkl')
	if saved:
		# load from files
		print('Found saved training data. Loading training data from files.')
		TrainingData, TrainingClass, TrainingName = load(path)
		
	else:
		# create new files from default
		print('No training data found. Creating new set of training data.')
		TrainingData = []
		TrainingClass = []
		TrainingName = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp', 'No Movement']



	if train > 0:
		TrainingData, TrainingClass = trainAll(TrainingData, TrainingClass, TrainingName, hMyo, dt, verb, train)
		start = time.time()
		save(TrainingData, TrainingClass, TrainingName, path)
		if verb >= 2:
			print('Save training data execution time: ' + str(time.time() - start) + 's')
	
	if verb >= 1:
		print('\nFitting data to ' + ('QDA' if quadratic else 'LDA') + ' model.')
	start = time.time()
	clf = fit(TrainingData, TrainingClass, quadratic)
	if verb >= 2:
		print('Fit LDA model execution time: ' + str(time.time() - start) + 's')
	
	print('')
	
	if pcycles > 0:
		predict(TrainingName, clf, hPlant, hMyo, hSink, dt=dt, length=pcycles, verb=verb)
		
	print("")
	print("Cleaning up...")
	print("")
	hSink.close()
	hMyo.close()
	#hTrain.close()
	#hPlant.close()
	print('Ending program in 5 seconds...')
	time.sleep(5)
	pass


def trainAll(TrainingData, TrainingClass, TrainingName, hMyo, dt, verb=1, samples=20):
	print('\n\nBeginning training Regime in 5 seconds...')
	print('(Ready for first pose "Wrist Rotate In")')
	time.sleep(5)

	print('')
	for classNum, className in enumerate(TrainingName):
		TrainingData, TrainingClass = trainSingle(TrainingData, TrainingClass, TrainingName, classNum, hMyo, dt, verb, samples)
	
	return TrainingData, TrainingClass

	
def trainSingle(TrainingData, TrainingClass, TrainingName, classNum, hMyo, dt, verb=1, samples=20):
	print('pose: ' + TrainingName[classNum])
	time.sleep(3)
	
	if verb == 0:
		print('Collecting EMG samples...')
	
	for i in list(range(samples)):
		loopStart = time.time()
		emgData = hMyo.getData()*0.01
		f = (feature_extract(emgData)).tolist()[0]
		TrainingData.append(f)
		TrainingClass.append(classNum)
		
		if verb >= 1:
			print('%8.4f %8.4f %8.4f %8.4f' % (f[0], f[8], f[16], f[24]))
		if verb >= 2:
			print('Get training data loop extraction time: ' + str(time.time() - loopStart) + 's')
		#if verb >= 3:
			#print('Emg Buffer: \n' + str(hMyo.getData()))
		
		if time.time() - loopStart < dt:
			time.sleep(dt - (time.time() - loopStart))
		else:
			print("Timing Overload")
	
	if verb == 0:
		print('Done.')
	
	print('')
	return TrainingData, TrainingClass
	
	
def fit(TrainingData, TrainingClass, quadratic=False):
	if len(TrainingData) == 0 or len(TrainingClass) == 0:
		raise ValueError('Training Data or Class array(s) is empty. Did you forget to save training data?')
	if len(TrainingData) != len(TrainingClass):
		raise ValueError('Training Data and Training class arrays are incompatable sizes. Try generating new training data from scratch.')
		
	X = np.array(TrainingData)
	y = np.array(TrainingClass)
	#print('shape of X: ' + str(X.shape))
	#print('shape of y: ' + str(y.shape))
	if quadratic:
		clf = QuadraticDiscriminantAnalysis()
	else:
		clf = LinearDiscriminantAnalysis()
	clf.fit(X, y)
	
	return clf
	
	
def predict(TrainingName, clf, hPlant, hMyo, hSink, dt=0.5, length=1000, verb = 1):
	for i in list(range(length)):
		loopStart = time.time()
		prediction = TrainingName[clf.predict(feature_extract(hMyo.getData()*0.01))]
		if verb >= 1:
			print('prediction: ' + prediction)
		if verb >= 2:
			print('LDA prediction execution time: ' + str(time.time() - loopStart) + 's')
		
		output(hPlant, hMyo, hSink, TrainingName, prediction)

		if time.time() - loopStart < dt:
			time.sleep(dt - (time.time() - loopStart))
		else:
			print("Timing Overload")
		

def output(hPlant, hMyo, hSink, TrainingName, classDecision):
	# Move joints using classifier
	jointId, jointDir = hPlant.class_map(classDecision)
	
	# Set joint velocities
	hPlant.velocity[:hPlant.NUM_JOINTS] = [0.0] * hPlant.NUM_JOINTS
	if jointId:
		for i in jointId:
			hPlant.velocity[i] = jointDir

	hPlant.update()

	# perform joint motion update
	vals = hMyo.getAngles()
	hPlant.position[3] = vals[1] + math.pi/2

	# transmit output
	hSink.sendJointAngles(hPlant.position)
		
		
def save(TrainingData, TrainingClass, TrainingName, path):
	print('\n')
	print('Saving emg feature data to test file')
	
	if not os.path.exists(path + '\\training_data'):
		os.makedirs(path + '\\training_data')
	
	joblib.dump(np.array(TrainingData), path + '\\training_data\\X.pkl')
	joblib.dump(np.array(TrainingClass), path + '\\training_data\\y.pkl')
	joblib.dump(TrainingName, path + '\\training_data\\className.pkl')


def load(path):
	#need to error check
	TrainingData = joblib.load(path + '\\training_data\\X.pkl').tolist()
	TrainingClass = joblib.load(path + '\\training_data\\y.pkl').tolist()
	TrainingName = joblib.load(path + '\\training_data\\className.pkl')
	
	return TrainingData, TrainingClass, TrainingName

	
def addClass(newClass, TrainingName=[]):
	TrainingName.append(newClass)
	return TrainingName
	
	
if __name__ == "__main__":
	main()

