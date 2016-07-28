
"""
Created on Tue Jul 19 11:16:36 2016

Initial creation of the training methods for LDA classification in Python

--VERBOSE  set to 2 or higher
Output timing information 

Most of the functionality is controlled by command line flags
e.g. if you want to do a demo (plus timing info), you can run: 
“python MyoUDPTrainer.py --VERBOSE 2 --TRAIN 20  --PREDICT 1000”. 
Training builds on whatever saved training data is in the directory, so if you 
want to train from scratch, delete all of the files in the “\python\training_data\” 
folder, and then rerun the script with the train flag (alternatively run delete() function).

WIP add delete flag to run delete method instead of manually deleting saved data
WIP change path behavior so that all paths use self.path
WIP add UDP communication to/from unity for training cues and other functionality

@author: D. Samson
"""

import sys
import time
import math
import numpy as np
from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp
#from TrainingUdp import TrainingUdp
from feature_extract import feature_extract
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
import os
from os.path import isfile
import argparse
from sklearn.externals import joblib


def demo():
	# get path to where this script is being run
	# any saved training data will be save here in a folder called "\training_data"
	path = os.path.dirname(os.path.abspath(__file__))
	args = parse()
	
	print('parsed args')
	# Machine learning Myo UDP trainer controller
	trainer = MyoUDPTrainer(path, args.QUADRATIC, args.TRAIN, args.FREQUENCY, args.VERBOSE, args.PREDICT)

	print('')

	#trainer.delete()
	trainer.load()
	#trainer.addClass('randomClass')
	trainer.trainAll()
	#trainer.removeClass('randomClass')
	trainer.save()
	trainer.fit()
	
	print('')
	print(str(trainer))
	
	print('Running prediction model:')
	trainer.predict()
	
	trainer.close()
	print('\nEnding program in 5 seconds...')
	time.sleep(5)

	
def parse():
	#parse command-line arguments
	parser = argparse.ArgumentParser(description='Myo Trainer Command-line Arguments:')
	parser.add_argument('-q', '--QUADRATIC', help='Run quadratic analysis of data instead of linear', action='store_true')
	parser.add_argument('-t', '--TRAIN', help='Run training regime at start of program. Specify number of sample per class', default=0, type=int)
	parser.add_argument('-p', '--PREDICT', help='Run prediction sequence. Specify number of cycles to run for (-1 for infinite)', default=0, type=int)
	parser.add_argument('-f', '--FREQUENCY', help='Set frequency to update at (Hz)', default=50, type=int)
	#parser.add_argument('-i', '--UDP_IP', help='IP address to send controls to', default='127.0.0.1')
	#parser.add_argument('-p', '--UDP_PORT', help='UDP port to send controls to', default=10001)
	parser.add_argument('-v', '--VERBOSE', help='How much console information. 0=minimal, 1=some, 2=more, etc.', default=1, type=int)
	#other args relating to creating new data/etc.
	
	return parser.parse_args()

	
def main():
	# get path to where this script is being run
	# any saved training data will be save here in a folder called "\training_data"
	path = os.path.dirname(os.path.abspath(__file__))
	args = parse()
	
	# Machine learning Myo UDP trainer controller
	trainer = MyoUDPTrainer(path, args.QUADRATIC, args.TRAIN, args.FREQUENCY, args.VERBOSE, args.PREDICT)
	
	
	pass

	
class MyoUDPTrainer:
	
	
	def __init__(self, path, quad = False, train = 0, freq = 50, verb = 1, plength = 0):
		self.TrainingData = []	# List of all feature extracted samples
		self.TrainingClass = [] # List of class indices that each sample belongs to
		self.TrainingName = []	# Name of each class
		
		self.path = path		# path to script location. Saved data will be saved/accessed from here.
		self.quadratic = quad	# set Quadratic Discriminant Analysis mode. False means LDA mode
		self.tsamples = train	# how many samples per training each class
		self.dt = 1.0/freq		# how frequently do training and prediction loops run
		self.verb = verb		# how much information output to the console
		self.pcycles = plength	# how many cycles to predict for. setting to -1 means infinite cycles
		self.hMyo = MyoUdp()	# Signal Source get external bio-signal data
		self.ROCFile = open(self.path + '\\..\\WrRocDefaults.xml', 'r')	# ROC file for possible motion classes
		self.hPlant = Plant(self.dt, self.ROCFile)			# Plant maintains current limb state (positions) during velocity control
		self.hSink = UnityUdp() #("192.168.1.24")	# Sink is output to ouside world (in this case to VIE)
		self.clf = None			# Fit training data model
		

	def trainAll(self, samples=None):
		if samples == None:
			samples = self.tsamples
			
		if samples > 0:
			print('\n\nBeginning training Regime in 5 seconds...')
			print('(Ready for first pose "Wrist Rotate In")')
			time.sleep(5)

			print('')
			for classNum, className in enumerate(self.TrainingName):
				self.trainSingle(classNum, samples)

	
	def trainSingle(self, classNum, samples=None):
		if samples == None:
			samples = self.tsamples
			
		print('pose: ' + self.TrainingName[classNum])
		time.sleep(3)
		
		if self.verb == 0:
			print('Collecting EMG samples...')
		
		for i in list(range(samples)):
			loopStart = time.time()
			emgData = self.hMyo.getData()*0.01
			f = (feature_extract(emgData)).tolist()[0]
			self.TrainingData.append(f)
			self.TrainingClass.append(classNum)
			
			if self.verb >= 1:
				print('%8.4f %8.4f %8.4f %8.4f' % (f[0], f[8], f[16], f[24]))
			if self.verb >= 2:
				print('Get training data loop extraction time: ' + str(time.time() - loopStart) + 's')
			#if self.verb >= 3:
				#print('Emg Buffer:\n' + str(emgData))
			
			loopTime = time.time() - loopStart
			if loopTime < self.dt:
				time.sleep(self.dt - loopTime)
			else:
				print("Timing Overload")
		
		if self.verb == 0:
			print('Done.')
		
		print('')
	
	
	def fit(self):
		
		if self.verb >= 1:
			print('Fitting data to ' + ('QDA' if self.quadratic else 'LDA') + ' model.')
		start = time.time()
		
		if len(self.TrainingData) == 0 or len(self.TrainingClass) == 0:
			raise ValueError('Training Data or Class array(s) is empty. Did you forget to save training data?')
		if len(self.TrainingData) != len(self.TrainingClass):
			raise ValueError('Training Data and Training class arrays are incompatable sizes. Try generating new training data from scratch.')
			
		X = np.array(self.TrainingData)
		y = np.array(self.TrainingClass)
		# if self.verb >= 3
			# print('Training data Numpy arrays')
			# print('shape of X: ' + str(X.shape))
			# print('shape of y: ' + str(y.shape))
		if self.quadratic:
			self.clf = QuadraticDiscriminantAnalysis()
		else:
			self.clf = LinearDiscriminantAnalysis()
		self.clf.fit(X, y)
		
		if self.verb >= 2:
			print('Fit LDA model execution time: ' + str(time.time() - start) + 's')
	
	
	#maybe break up into predictSingle and predictAll
	def predict(self, cycles=None):
		if cycles == None:
			cycles = self.pcycles
			
		i = 0
		while i != cycles:
			loopStart = time.time()
			prediction = self.TrainingName[self.clf.predict(feature_extract(self.hMyo.getData()*0.01))]
			if self.verb >= 1:
				print('prediction: ' + prediction)
			if self.verb >= 2:
				print(('QDA' if self.quadratic else 'LDA') + ' prediction execution time: ' + str(time.time() - loopStart) + 's')
			
			self.output(prediction)

			loopTime = time.time() - loopStart
			if loopTime < self.dt:
				time.sleep(self.dt - loopTime)
			else:
				print("Timing Overload")
			
			i += 1

			
	def output(self, classDecision):
		# Move joints using classifier
		try:
			jointId, jointDir = self.hPlant.class_map(classDecision)

			# Set joint velocities
			self.hPlant.velocity[:self.hPlant.NUM_JOINTS] = [0.0] * self.hPlant.NUM_JOINTS
			if jointId:
				for i in jointId:
					self.hPlant.velocity[i] = jointDir

			self.hPlant.update()

			# perform joint motion update
			vals = self.hMyo.getAngles()
			self.hPlant.position[3] = vals[1] + math.pi/2

			# transmit output
			self.hSink.sendJointAngles(self.hPlant.position)
	
		except:
			print('Class "' + classDecision + '" not available from ROC table.')
			#jointId, jointDir = [[],0]
			pass	
	
	
	def save(self, path=None):
		if path == None:
			path = self.path
			
		start = time.time()
		
		print('\nSaving emg feature data to test file')
		
		if not os.path.exists(path + '\\training_data'):
			os.makedirs(path + '\\training_data')
		
		joblib.dump(np.array(self.TrainingData), path + '\\training_data\\X.pkl')
		joblib.dump(np.array(self.TrainingClass), path + '\\training_data\\y.pkl')
		joblib.dump(self.TrainingName, path + '\\training_data\\className.pkl')
		
		if self.verb >= 2:
			print('Save training data execution time: ' + str(time.time() - start) + 's')


	def load(self, path=None):
		if path == None:
			path = self.path
		
		# Check if data already exists
		# Manipulate data as python arrays, then convert to numpy arrays when final size reached
		saved = isfile(path + '\\training_data\\X.pkl') and isfile(path + '\\training_data\\y.pkl') and isfile(path + '\\training_data\\className.pkl')
		if saved:
			# load from files
			print('Found saved training data. Loading training data from files.')
			self.TrainingData = joblib.load(path + '\\training_data\\X.pkl').tolist()
			self.TrainingClass = joblib.load(path + '\\training_data\\y.pkl').tolist()
			self.TrainingName = joblib.load(path + '\\training_data\\className.pkl')	
		else:
			print('No training data found.')
			self.create(path)
			
		#perform error checks here:
		#if error: self.create()
		pass
			

	def delete(self, path=None):
		print('Deleting saved data.')
		
		if path == None:
			path = self.path
	
		if isfile(path + '\\training_data\\X.pkl'):
			os.remove(path + '\\training_data\\X.pkl')
		if isfile(path + '\\training_data\\y.pkl'):
			os.remove(path + '\\training_data\\y.pkl')
		if isfile(path + '\\training_data\\className.pkl'):
			os.remove(path + '\\training_data\\className.pkl')


	def create(self, path=None):
		if path == None:
			path = self.path
	
		# create new data from default
		print('Creating new set of training data.')
		self.TrainingData = []
		self.TrainingClass = []
		#TrainingName should be loaded from the current ROC file, or start blank, and then addClass for each class
		self.TrainingName = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp', 'No Movement']
		
		#save empty arrays to files @ path\\training_data\\<array>
		pass
			
	
	def close(self):
		print('')
		print('Cleaning up...')
		print('')
		self.hSink.close()
		self.hMyo.close()
	
	
	def addClass(self, newClass):
		if newClass not in self.TrainingName:
			self.TrainingName.append(newClass)
		else:
			raise ValueError('Cannot add class "' + newClass + '" to training set. Class already exists in object.')


	def removeClass(self, toRemove):
		print('Attemptint to remove class "' + toRemove +'."')
		
		newData = []
		newClass = []
		newName = []
		remIndex = None
		
		for i in range(len(self.TrainingName)):
			if self.TrainingName[i] != toRemove:
				newName.append(self.TrainingName[i])
			else:
				if remIndex == None:
					remIndex = i
				else:
					raise ValueError('Multiple instances of class "' + toRemove + '" in training class list.')
		
		if remIndex == None:
			raise ValueError('No class named "' + toRemove + '" was found in current training data.')
		else:
			for i in range(len(self.TrainingClass)):
				if self.TrainingClass[i] != remIndex:
					newClass.append(self.TrainingClass[i])
					newData.append(self.TrainingData[i])
		
		self.TrainingData = newData
		self.TrainingClass = newClass
		self.TrainingName = newName


	def __str__(self):
		#perhaps adjust output based on VERBOSE
		sizes = [0]*len(self.TrainingName)
		for i in range(len(self.TrainingClass)):
			sizes[self.TrainingClass[i]] += 1
			
		string = 'Myo Trainer Object\n'
		for i, name in enumerate(self.TrainingName):
			string += 'Class: ' + name + '\tSamples: ' + str(sizes[i]) + '\n'
		
		return string		

		
if __name__ == "__main__":
	demo() #run demo trainer
	#main() #run unity communicator
	pass

