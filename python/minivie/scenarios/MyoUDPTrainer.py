"""
Created on Tue Jul 19 11:16:36 2016

Python Class and methods for controlling the whole machine learning training process back end.

--VERBOSE  set to 2 or higher
Output timing information 

Most of the functionality is controlled by command line flags
Can also control training object almost entirely from UDP cues.
e.g. run: python MyoUDPTrainer -x, (-x skips handshake). 
--In matlab minivie:
>>  a = PnetClass(8050, 8051,'127.0.0.1')
>>  a.initialize
>>  a.putData(['<cue>' uint8(<val>)]) to send a training cue plus a value


Training builds on whatever saved training data is in the directory, so if you 
want to train from scratch, delete all of the files in 'TRAINING_DATA.hdf5'
folder, and then rerun training sequence (alternatively run delete() function).

TODO Add get state method that returns the current state of the program via UDP when requested
TODO Add acknowledgement UDP signals for when loops are ended with 'e' or 'q' signal

@author: D. Samson

Revisions:
2017Jan09 Samson: Initial Incorperation of pattern_rec
2017Jan16 Samson: Added plant support. Removed depreciated code 
"""

import os
import sys
import time
import math
import argparse
import socket
import errno
import random
import traceback

from enum import Enum

# Allow access to minivie packages from current path in scenarios folder
if os.path.split(os.getcwd())[1] == 'scenarios':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
elif os.path.split(os.getcwd())[1] == 'minivie':
    pass #do nothing
else:
    raise OSError('Could not find /python/minivie. Script run from unknown file location.')
    
print('Current path: ' + os.path.split(os.getcwd())[1])
    
from pattern_rec import TrainingData, FeatureExtract, Classifier

from inputs.myo import MyoUdp
from controls.plant import Plant, class_map
#from controls.plant import class_map

from mpl.unity import UnityUdp

if os.path.split(os.getcwd())[1] == 'scenarios':
    #change directory to minivie
    os.chdir('..')

print('Current path: ' + os.path.split(os.getcwd())[1])


def parse():
    """Parse command line arguments into argparse model.
    
    Command-line arguments:
    -h or --help -- ouput help text describing command-line arguments.
    -q or --QUADTRATIC -- Run QDA classifier as opposed to default LDA classifier. args.QUADRATIC returns bool of argument.
    -d or --DELETE -- Deletes saved data stored in \MiniVIEPath\python\training_data\ if available.
    -t or --TRAIN -- Instructs the trainer class how many feature extraction samples to collect for each pose while training.
    #--TRAIN is only used in the trainSingle() function which records training data for a single pose. 
    -l or TRAIN_LOOP -- Specify number of times to repeat training regime for standard training process.
    -p or --PREDICT -- Should the script run a pose predition loop after all training? number specifies how many cycles to predict for (-1 for infinite, 0 for none).
    -f or --FREQUENCY -- set the data collection frequency, as well as the data output frequency.
    -i or --UDP_IP -- set the IP address to communicate training cues on.
    -u or --UNITY_PORT -- set the port that python listens on for UDP packets from Unity.
    -y or --PYTHON_PORT -- set the port that python sends UDP packets on to Unity.
    -v or --VERBOSE -- specify how much console output the python program makes. 0 for minimum, 1 for some, 2 for more, etc.
    -e or --EXECUTE -- specify what main method to run when this script is called. Input is a string with the name of the method, which is then selected in a switch-like statement at the end of this file.
    -x or --DEBUG -- enter debug mode. Does things such as skip UDP handshake, ...(other feature to be added)
    
    Return Arguments:
    args (parser.parse_args()) -- command line arguments parsed into a dictionary for easy use.
    -- args is generally are stored into the MyoUDPTrainer object on initialization as instance data
    """

    # parse command-line arguments
    parser = argparse.ArgumentParser(description='Myo Trainer Command-line Arguments:')
    parser.add_argument('-q', '--QUADRATIC', help='Run quadratic analysis of data instead of linear',
                        action='store_true')
    parser.add_argument('-d', '--DELETE', help='Delete currently saved training data if any.', action='store_true')
    parser.add_argument('-t', '--TRAIN',
                        help='Run training regime at start of program. Specify number of sample per class', default=0,
                        type=int)
    parser.add_argument('-l', '--TRAIN_LOOP', help='Specify number of cycles to repeat each pose during training',
                        default=1, type=int)
    parser.add_argument('-p', '--PREDICT',
                        help='Run prediction sequence. Specify number of cycles to run for (-1 for infinite)',
                        default=0, type=int)
    parser.add_argument('-f', '--FREQUENCY', help='Set frequency to update at (Hz)', default=50, type=int)
    parser.add_argument('-i', '--UDP_IP', help='IP address to send controls to', default='127.0.0.1')
    parser.add_argument('-u', '--UNITY_PORT', help='UDP port to receive unity packets from', default=8051)
    parser.add_argument('-y', '--PYTHON_PORT', help='UDP port to send python controls to', default=8050)
    parser.add_argument('-v', '--VERBOSE', help='How much console information. 0=minimal, 1=some, 2=more, etc.',
                        default=1, type=int)
    parser.add_argument('-e', '--EXECUTE',
                        help='What "Main()" should this script execute: UnityTrainer, demo, main, etc.?', type=str,
                        default='main')
    parser.add_argument('-x', '--DEBUG', help='Enter DEBUG mode', action='store_true')
    # other args relating to creating new data/etc.

    return parser.parse_args()


def main(args):
    """
    Default execution case. Fully controllable training process via agnostically generatied UDP cues.
    
    For control from Matlab PnetClass:
    (goto MiniVIE)
    >> a = PnetClass(8050, 8051,'127.0.0.1')
    >> a.initialize
    >> a.putData([uint8(<data_to_transmit>)])
    
    At start of this method, this program expects a handhsake response (see handshake function).
    Then this program enters the main UDP flow control loop.
    
    UDP Cues for MyoUDPTrainer Functions
    (~ for no cue)
    Cue:                Function:                   Meaning:            Details:    
    fs                  save()                      "file save"         save training data to hdf5 file
    fl                  load()                      "file load"         load training data from hdf5 file
    fd                  delete()                    "file delete"       **Currently unimplemented** Delete the existing save data file
    fc                  copy()                      "file copy"         make a copy of the current training data file
    cd                  reset()                     "class defaults"    reset all training data to empty/defaults (doesn't affect saved data)
    cc<class>           clear(class)                "class clear"       remove all training data for specified <class>
    ca<class>           add_class(class)            "class add"         **Currently unimplemeneted** add <class> to available classes list
    cr<class>           remove_class(class)         "class remove"      **Currently unimplemeneted** remove <class> from available classes list
    cf                  fit()                       "class fit"         fit LDA model to training data
    os                  print(__str__())            "output string"     print out the to string of the MyoUDPTrainer object
    op                  output()                    "output plant"      update/emit plant based on current prediction
    ps                  predictSingle()             "predict single"    Output a single prediction from the LDA model based on the current EMG data
    pm<count>           predictMult(count)          "predict multiple"  Output multiple predictions from LDA model based on current EMG data
    ...                                                                 (<count> is optional. 'infinite' for -1, else, a uint8 for <count> value.)
    ts<cycles>          trainSingle(cycles)         "train single"      Train the currently selected pose by collecting <cycles> samples of EMG data
    ...                                                                 (<cycles> is optional. 1 uint8 for <cycles> value)
    ta<samples,cycles>  trainAll(samples, cycles)   "train all"         Run training regime for all poses. Collects <samples> samples of EMG data, and repeats all poses <cycles> times
    ...                                                                 (<samples> is optional; 1 uint8 for value at data[2]. <cycles> is optional (requires samples passed in); 1 uint8 at data[3].)
    tr                  trainContinuous()           "train record"      Train the current pose continuously until the 'e' UDP signal is recieved
    tn                  (next pose)                 "train next"        (not a function) increments current class counter by 1. (overflow causes a UDP reply 'o')
    tp                  (previous pose)             "train previous"    (not a function) decrements current class counter by 1. (underflow causes a UDP reply 'o')
    tf                  (first pose)                "train first"       (not a function) set current class counter to 0 (first pose)
    tl                  (last pose)                 "train last"        (not a function) set current class counter to len(motion_names)-1 (last pose)
    
    Others UDP Codes:
    code:               Meaning:                    Details:
    {ACK} (0x06)        "Acknowledged"
    {NAK} (0x15)        "Negative Acknowledge"
    o                   "counter out of bounds"     (sent when 'tn' or 'tp' is received and counter would progress past -1, or len(classes)) (i.e. counter at start or end of class list)
    q                   "quit (current loop)"
    
    """

    print('Running UDP driven trainer. Progress will only continue if proper UDP cues are returned.\n')

    # state machine variable. Same states are mirrored in Unity script.
    class STATES(Enum):
        waitingHandshake = 0
        waitingStart = 1
        setupRecord = 2
        waitingRecord = 3
        recording = 4
        cooldown = 5
        inactive = 6
        off = 7
        none = 8
        
    # initial state is waiting for Handshake from Unity
    state = STATES.waitingHandshake

    # Machine learning Myo UDP trainer controller
    trainer = MyoUDPTrainer(args)

    if not args.DEBUG:
        # handshake between unity and python
        trainer.handshake()
    else:
        print('Skipping UDP handshake for DEBUG mode.')

    state = STATES.waitingStart

    data, addr = None, None  # current UDP packet received from Unity
    curPose = 0  # index of the current pose being operated on

    # handle generic UDP cues
    print('Start of UDP flow control section.')
    while data is None or data[0] != ord('q'):  # 'q' UDP cue for "quit"
        try:
            print('Waiting for UDP data packet...')
            
            data, addr = trainer.receiveBlock()
            data = bytearray(data)
            #print out recieved data formatted according to python 2 or 3
            if sys.version_info[0] == 2:
                print('Received packet: "' + str(data) + '"')
            elif sys.version_info[0] == 3:
                print('Received packet: "' + str(data)[12:-2] + '"')

            if data[0] == ord('f'):  # file
                if data[1] == ord('s'):  # save
                    trainer.save()

                elif data[1] == ord('l'):  # load
                    trainer.load()

                elif data[1] == ord('d'):  # delete
                    trainer.delete()

                elif data[1] == ord('c'):  # copy
                    trainer.copy()

            elif data[0] == ord('c'):  # class (poses)
                if data[1] == ord('d'):  # defaults (reset to)
                    trainer.reset()
                
                elif data[1] == ord('c'):  # clear
                    className = data[2:].decode('utf-8')
                    trainer.clear_class(className)
                
                elif data[1] == ord('a'):  # add
                    className = data[2:].decode('utf-8')
                    trainer.add_class(className)

                elif data[1] == ord('r'):  # remove
                    className = data[2:].decode('utf-8')
                    trainer.remove_class(className)
                    
                elif data[1] == ord('f'):  # fit to model
                    trainer.fit()

            elif data[0] == ord('o'):  # output
                if data[1] == ord('s'):  # tostring
                    print(str(trainer))

                elif data[1] == ord('p'):  # plant
                    trainer.ouput()# output plant. not sure how this would be used...
                    pass

            elif data[0] == ord('p'):  # predict
                if data[1] == ord('m'):  # multiple
                    if len(data) == 3:
                        trainer.predictMult(data[2])
                    elif len(data) > 3 and data[2:].decode('utf-8').lower() == 'infinity':
                        #send UDP cue 'e' to end infinite prediction cycle
                        trainer.predictMult(-1)
                    else:
                        trainer.predictMult()  # use settings in object

                elif data[1] == ord('s'):  # single
                    id, status = trainer.predictSingle()  
                    print(trainer.TrainingData.motion_names[id])
                    print(status)

            elif data[0] == ord('t'):  # train 
            #(handles sequence for training poses, e.g. progressing to next pose, training current pose, etc.)
                
                if data[1] == ord('a'):  # all poses
                    if len(data) >= 3:
                        cycles = 1 if len(data) == 3 else data[3]
                        trainer.trainAll(data[2], cycles)
                    else:
                        trainer.trainAll()

                elif data[1] == ord('s'):  # single pose
                    if len(data) >= 3:
                        trainer.trainSingle(curPose, samples=data[2], pause=0)
                    else:
                        trainer.trainSingle(curPose, pause=0)
                
                elif data[1] == ord('r'):  # start recording current pose
                    #send UDP 'e' to end recording
                    trainer.trainContinuous(curPose)

                elif data[1] == ord('n'):  # (goto) next pose
                    if curPose + 1 < len(trainer.TrainingData.motion_names):
                        curPose += 1
                        print('Current pose set to "' + trainer.TrainingData.motion_names[curPose] + '."\n')
                    else:
                        # curPose = 0  #may want to delete this line
                        print('Already at last pose "' + trainer.TrainingData.motion_names[curPose] + '."\n')
                        trainer.send('o')  # pose overflow

                elif data[1] == ord('p'):  # (goto) previous pose
                    if curPose > 0:
                        curPose -= 1
                        print('Current pose set to "' + trainer.TrainingData.motion_names[curPose] + '."\n')
                    else:
                        # curPose = len(trainer.TrainingData.motion_names) - 1 #may want to delete this line.
                        print('Already at first pose "' + trainer.TrainingData.motion_names[curPose] + '."\n')
                        trainer.send('o')

                elif data[1] == ord('f'):  # (goto) first pose
                    curPose = 0
                    print('Current pose set to "' + trainer.TrainingData.motion_names[curPose] + '."\n')

                elif data[1] == ord('l'):  # (goto) last pose
                    curPose = len(trainer.TrainingData.motion_names) - 1
                    print('Current pose set to "' + trainer.TrainingData.motion_names[curPose] + '."\n')

            elif data[0] == ord('q'):       # quit the UDP loop
                print('Quit signal recieved.')

            else:
                print('Unrecognized data packet. Restarting control loop.\n')

        # error handling
        except Exception as err:  # print the exception, and continue running UDP flow control loop
            try:
                exc_info = sys.exc_info()
            finally:
                print('\nError occured in execution loop.')
                traceback.print_exception(*exc_info)
                print('')
                del exc_info
    
    # End of UDP flow control loop

    print('Exiting UDP flow control section.\n')

    trainer.close()
    # print('\nEnding program in 5 seconds...')
    # time.sleep(5)
    
    pass

        
class MyoUDPTrainer:
    """Python Class for managing machine learning and Myo training operations."""
    
    def __init__(self, args):
        
        self.TrainingData = TrainingData()
        self.FeatureExtract = FeatureExtract()
        self.Classifier = None
        
        #Not implemented in pattern_rec.TrainingData class
        #if args.DELETE:
        #    self.TrainingData.delete() #Currently unimplemented
        
        self.quadratic = args.QUADRATIC     # set Quadratic Discriminant Analysis mode. False means LDA mode
        self.tsamples = args.TRAIN          # how many samples per training each class
        self.tcycles = args.TRAIN_LOOP      # how many cycles of training each pose to repeat
        self.dt = 1.0 / args.FREQUENCY      # how frequently do training and prediction loops run
        self.verb = args.VERBOSE            # how much information output to the console
        self.pcycles = args.PREDICT         # how many cycles to predict for. setting to -1 means infinite cycles
        self.hMyo = MyoUdp()                # Signal Source get external bio-signal data
        self.hMyo.connect()
        self.ROCPath = '../../WrRocDefaults.xml'    # Path to ROC file for plant
        self.Plant = Plant(self.dt, self.ROCPath)   # Plant maintains current limb state (positions) during control
        self._MyoUDPTrainer__gain_value = 1         # Not sure about what this line does. Got an error from the plant without it though
        self.class_decision = 0     
        self.DataSink = UnityUdp()  # ("192.168.1.24")     # Sink is output to ouside world (in this case to VIE)
        
        self.UDP_IP = args.UDP_IP                   # IP address to communicate with unity through (directed to localhost).
        self.PYTHON_SEND_PORT = args.PYTHON_PORT    # from python send data to unity using this port
        self.UNITY_RECEIVE_PORT = args.UNITY_PORT   # from unity receive data in python using this port

        # UDP communication to and from Unity
        self.UnityReceiverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UnityReceiverSock.bind((self.UDP_IP, self.UNITY_RECEIVE_PORT))
        self.UnityReceiverSock.setblocking(0)
        # https://docs.python.org/2/library/socket.html consider settimeout(<small number>) instead of disabling blocking
        print('UDP Program Control IP: ' + str(self.UDP_IP))
        print('Listening to Port: ' + str(self.UNITY_RECEIVE_PORT))

        self.PythonSenderSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # print('PythonUDP UI IP: ' + str(self.UDP_IP))
        print('Sending to Port: ' + str(self.PYTHON_SEND_PORT))
        print('')

    def trainAll(self, samples=None, cycles=None):
        """
        Run training regime for all poses sequentially.
        
        Keyword Arguments:
        self -- pointer to this object
        samples -- (Optional) If passed in, overrides number of samples to collect for each pose. Otherwise uses number of samples specified in self.tsamples
        cycles -- (Optional) If passed in, overrides number of times to repeat training process
        """

        if samples == None:
            samples = self.tsamples
        if cycles == None:
            cycles = self.tcycles

        if samples > 0:
            print('\n\nBeginning training Regime in 5 seconds...')
            print('(Ready for first pose "' + self.TrainingData.motion_names[0] + '"')
            time.sleep(5)

            print('')
            for cycle in list(range(cycles)):
                print('Training Cycle #' + str(cycle) + '\n')
                for classNum, className in enumerate(self.TrainingData.motion_names):
                    self.trainSingle(classNum, samples)
        print('Finished training all poses.\n')
    
    def trainSingle(self, classID, samples=None, pause=3):
        """
        Run training regime for single specified pose.
        
        Keyword Arguments:
        self -- pointer to this object
        samples -- (Optional) If passed in, overrides number of samples to collect for each pose. Otherwise uses number of samples specified in self.tsamples
        pause -- (Optional) If passed in, set how long to pause before recording the Myo data. Otherwise default pause is 3 seconds
        """
        
        start = time.time()
        
        
        if samples == None:
            samples = self.tsamples

        className = self.TrainingData.motion_names[classID]
        
        if self.verb >= 0:
            print('pose: ' + self.TrainingData.motion_names[classID])
        time.sleep(pause)

        if self.verb == 0:
            print('Collecting EMG samples...')

        for i in list(range(samples)):
            loopStart = time.time()
            emgData = self.hMyo.get_data() * 0.01
            f_list, f_learn = self.FeatureExtract.get_features(emgData)
            
            #format for storing data
            f_list = f_list[0]
            f_learn = f_learn[0]

            f = f_learn
            
            self.TrainingData.add_data(f, classID, className)
            

            if self.verb >= 1:
                print('%8.4f %8.4f %8.4f %8.4f' % (f[0], f[8], f[16], f[24]))
            if self.verb >= 2:
                print('Get training data loop extraction time: ' + str(time.time() - loopStart) + 's')
                # if self.verb >= 3:
                # print('Emg Buffer:\n' + str(emgData))

            loopTime = time.time() - loopStart
            if loopTime < self.dt:
                time.sleep(self.dt - loopTime)
            else:
                print("Timing Overload")

        if self.verb == 0:
            print('Done.')

        if self.verb >= 2:
            print('Entire train single pose cycle execution time: ' + str(time.time() - start) + 's')

        if self.verb >= 0:
            print('')
    
    def trainContinuous(self, classID):
        """
        continuously train the currently set motion until quit signal recieved
        
        """
        
        start = time.time()
        
        #set length of pause/number of samples for trainSingle() function
        samples=1
        pause=0
        
        s = 0   #how many samples have been recorded
        
        data, addr = None, None  # current UDP packet received from Unity

        while data == None or ord(data[0]) != ord('e'):
            data, addr = self.receiveNoBlock()  # receive UDP data to allow for exiting infinite loop
            loopStart = time.time()
            self.trainSingle(classID, samples, pause)
            s += 1 #update cound of samples recorded
            
        if self.verb >= 2:
            print('Trained ' + self.TrainingData.motion_names[classID] + ' for ' + str(time.time() - start) + 's')
        if self.verb >= 1:
            print('Recorded ' + str(s) + ' samples')
        print('')
        
    def fit(self):
        """
        Fit data currently stored in self.TrainingData and self.TrainingClass to LDA or QDA model
        
        Keyword Arguments:
        self -- pointer to this object
        
        Training Data Format:
        self.TrainingData is the array X which lists out all of the samples of feature extracted data as a [N*32] array for N samples of training data
        self.TrainingClass is the array y which specifies which class each sample in X belongs to as a [N*1] array for N samples of training data.
        """

        if self.verb >= 1:
            print('Fitting data to ' + ('QDA' if self.quadratic else 'LDA') + ' model.')
        start = time.time()
        self.Classifier = Classifier(self.TrainingData)
        self.Classifier.fit() #want to pass in whether quadratic or linear

        if self.verb >= 2:
            print('Fit LDA model execution time: ' + str(time.time() - start) + 's')

        print('')
    
    def predictMult(self, cycles=None):
        """
        Run the LDA or QDA classifier prediction based on current myo data for multiple cycles.
        
        Keyword Arguments:
        self -- pointer to this object
        cycles -- (Optional) If passed in, overrides how many cycles to predict for. Otherwise uses number of cycles specified in self.pcycles
        -- setting cycles to 0 causes no predictions to be made. Setting cycles to -1 (or any negative number) causes infinite prediction cycles to occur
        """

        if cycles == None:
            cycles = self.pcycles

        data, addr = None, None  # current UDP packet received from Unity

        i = 0
        while i != cycles and (data == None or ord(data[0]) != ord('e')):
            data, addr = self.receiveNoBlock()  # receive UDP data to allow for exiting infinite loop
            loopStart = time.time()
            id, status = self.predictSingle()
            prediction = self.TrainingData.motion_names[id]
            if self.verb >= 1:
                print('prediction: ' + prediction)
            if self.verb >= 2:
                print(status)
                print(('QDA' if self.quadratic else 'LDA') + ' prediction execution time: ' + str(
                    time.time() - loopStart) + 's')

            #self.output(prediction, True)

            loopTime = time.time() - loopStart
            if loopTime < self.dt:
                time.sleep(self.dt - loopTime)
            else:
                print("Timing Overload")

            i += 1

        print('')
        
    def predictSingle(self):
        """
        Run the LDA or QDA classifier prediction based on current myo data for a single sample.
        
        Keyword Arguments:
        self -- pointer to this object
        
        Return Arguments:
        id -- class id of predicted pose
        status -- status message from prediction error checking
        """
        emgData = self.hMyo.get_data() * 0.01
        f_list, f_learn = self.FeatureExtract.get_features(emgData)
        
        id, status = self.Classifier.predict(f_learn)
        self.class_decision = id
        self.output(id)
        return (id, status)
    
    def output(self, decision_id=None):
        """
        Update plant model with current class decision, and output current joint angles over UDP
        **Needs to be tested**
        
        Keyword Arguements:
        self -- pointer to this object
        decision_id -- integer class decision value for current pose
        """
        
        if decision_id == None:
            decision_id = self.class_decision
            
        # initialize output
        #self.output = {'status': 'RUNNING', 'features': None, 'decision': 'None', 'vote': None}

        # get data / features
        #self.output['features'], f = self.FeatureExtract.get_features(self.SignalSource)

        # if simultaneously training the system, add the current results to the data buffer
        #if self.add_data:
        #    self.TrainingData.add_data(self.output['features'], self.training_id, self.training_motion)

        # classify
        #decision_id, self.output['status'] = self.SignalClassifier.predict(f)
        #if decision_id is None:
        #    return self.output

        # TODO: add majority vote

        # get decision name
        class_decision = self.TrainingData.motion_names[decision_id]
        #self.output['decision'] = class_decision

        # parse decision type as arm, grasp, etc
        class_info = class_map(class_decision)

        # Set joint velocities
        self.Plant.new_step()

        # pause if applicable
        #if self.is_paused('All'):
        #    self.output['status'] = 'PAUSED'
        #    return self.output
        #elif self.is_paused('Hand'):
        #    self.output['status'] = 'HAND PAUSED'

        # set the mapped class into either a hand or arm motion
        #pause_hand = self.is_paused('Hand') or self.is_paused('All')
        if class_info['IsGrasp']:# and not pause_hand:
            # the motion class is either a grasp type or hand open
            if class_info['GraspId'] is not None and self.Plant.GraspPosition < 0.2:
                # change the grasp state if still early in the grasp motion
                self.Plant.GraspId = class_info['GraspId']
            self.Plant.set_grasp_velocity(class_info['Direction'] * self.__hand_gain_value)

        #pause_arm = self.is_paused('Arm') or self.is_paused('All')
        if not class_info['IsGrasp']:# and not pause_arm:
            # the motion class is an arm movement
            self.Plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * self.__gain_value)

        self.Plant.update()

        # transmit output
        self.DataSink.send_joint_angles(self.Plant.JointPosition)
        
    def save(self, path=None):
        """
        Save the current data to the disk.
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides the path to save the data to. Otherwise save data to path at self.path
        (path currently unimplemeneted. Saves hdf5 file in current folder)
        """

        #if path == None:
        #    path = self.path

        start = time.time()

        print('Saving emg feature data to hdf5 file.')
        #trainFolder = os.path.join(path, 'training_data')

        #if not os.path.exists(trainFolder):
        #    os.makedirs(trainFolder)

        self.TrainingData.save() #want option to save to specified path

        if self.verb >= 2:
            print('Save training data execution time: ' + str(time.time() - start) + 's')

        print('')
    
    def load(self, path=None):
        """
        Load training data from disk.
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides path that training data is loaded from. Otherwise data is loaded from self.path
        (path currently unimplemeneted. Loads hdf5 file in current folder)
        """

        #if path == None:
        #    path = self.path
        
        start = time.time()
        
        #trainFolder = os.path.join(path, 'training_data')
        
        self.TrainingData.load() #want option to load from specified path
        
        if self.verb >= 2:
            print('Load training data execution time: ' + str(time.time() - start) + 's')
        
        print('')
        
    def delete(self, path=None):
        """
        Delete the current data from the disk.
        **Currently unimplemented in pattern_rec.TrainingData object**
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides the path to delete the data from. Otherwise deletes data from path at self.path
        (path currently unimplemeneted. Deletes hdf5 file in current folder)
        """

        #if path == None:
        #    path = self.path

        start = time.time()

        print('Saving emg feature data to hdf5 file.')
        #trainFolder = os.path.join(path, 'training_data')

        #if not os.path.exists(trainFolder):
        #    os.makedirs(trainFolder)

        self.TrainingData.delete() #want option to delete at specified path

        if self.verb >= 2:
            print('Delete training data execution time: ' + str(time.time() - start) + 's')

        print('')
    
    def copy(self, path=None):
        """
        copy training data from current saved file.
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides path that training data is copied to. Otherwise data is copied to self.path
        (path currently unimplemeneted. copies hdf5 file to current folder)
        """

        #if path == None:
        #    path = self.path
        
        start = time.time()
        
        #trainFolder = os.path.join(path, 'training_data')
        
        self.TrainingData.copy() #want option to copy to specified path
        
        if self.verb >= 2:
            print('Copy training data execution time: ' + str(time.time() - start) + 's')
        
        print('')
         
    def reset(self):
        """
        Clear training data. 
        Blank training data is stored into self.TrainingData, self.TrainingClass, and self.TrainingName.
        
        Keyword Arguments:
        self -- pointer to this object
        """

        # create new data from default
        print('resetting training data set to defaults.\n')
        self.TrainingData.reset()
        
    def add_class(self, toAdd):
        """
        Add a pose to the list of poses that are in the training set.
        **Currently unimplemented in pattern_rec.TrainingData object**
        
        Keyword Arguments:
        self -- pointer to this object
        newClass -- string that names the pose to add
        """
        
        start = time.time()
        
        print('Attempting to add new pose: ' + toAdd)
        #self.TrainingData.addClass(newClass)
        
        if self.verb >= 2:
            print('add class execution time: ' + str(time.time() - start) + 's')

        
        print('')
        
    def remove_class(self, toRemove):
        """
        Delete a pose from the list of poses that are in the training set.
        **Currently unimplemented in pattern_rec.TrainingData object**
        
        Keyword Arguments:
        self -- pointer to this object
        newClass -- string that names the pose to add
        """
        
        start = time.time()
        
        print('Attempting to remove pose: ' + toRemove)
        #id = self.TrainingData.motion_names.index(toRemove)
        #self.TrainingData.clear(id)
        #self.TrainingData.removeClass(id / toRemove)
        
        if self.verb >= 2:
            print('remove class execution time: ' + str(time.time() - start) + 's')

        print('')

    def clear_class(self, toClear):
        """
        Delete a pose from the list of poses that are in the training set.
        
        Keyword Arguments:
        self -- pointer to this object
        toClear -- string that names the pose to add
        """
        
        start = time.time()
        
        id = self.TrainingData.motion_names.index(toClear)
        self.TrainingData.clear(id)
        
        if self.verb >= 2:
            print('clear class execution time: ' + str(time.time() - start) + 's')
        
        print('')
        
    def close(self):
        """Cleanup currently opened UDP objects."""
        print('')
        print('Cleaning up...')
        print('')
        self.DataSink.close()
        self.hMyo.close()

    def send(self, message):
        """
        Send a UDP message to Unity from Python.
        
        Keyword Arguments:
        self -- pointer to this object
        message -- string to send to Unity via UDP
        """
        self.PythonSenderSock.sendto(bytearray(message, 'utf-8'), (self.UDP_IP, self.PYTHON_SEND_PORT))

    def receiveNoBlock(self, timeout=0.0):
        """
        Receive data from Unity while allowing timeout.
        
        Keyword Arguments:
        self -- pointer to this object
        timeout -- (Optional) If passed in, sets the amount of time the receiver will wait for before it times out, no data
        
        Return Arguments:
        data, addr -- data string and data address for message received from Unity. Set to None, None if timeout occurs
        
        Notes: 
        for more information see: https://docs.python.org/2/library/socket.html
        """

        # receiver that will return None, None if it doesn't receive immediately/within timout limit
        # self.UnityReceiverSock.setblocking(0)
        self.UnityReceiverSock.settimeout(timeout)

        try:
            data, addr = self.UnityReceiverSock.recvfrom(1024)  # buffer size is 1024 bytes
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK or errno.ETIMEDOUT:
                return None, None
            else:
                # a "real" error occurred
                print(e)
                sys.exit(1)
        else:
            # do stuff with data from receiver
            return data, addr

    def receiveBlock(self):
        """
        Receive data from Unity while while waiting indefinitely until received.
        
        Keyword Arguments:
        self -- pointer to this object
        
        Return Arguments:
        data, addr -- data string and data address for message received from Unity.
        
        Notes: 
        for more information see: https://docs.python.org/2/library/socket.html
        """

        # receiver that will wait until it receives data
        self.UnityReceiverSock.setblocking(1)
        return self.UnityReceiverSock.recvfrom(1024)  # buffer size is 1024 bytes

    def handshake(self):
        """Perform handshake with Unity over UDP to ensure that Unity and Python are synced"""

        # wait to receive data [A] and then send [A+1,B]
        # wait to receive data [B+1]
        # handhsake complete. Unity and Python are synced

        # IMPORTANT NOTE: if A=255, then the expected A+1=0 because only a single byte is checked

        # self.UnityReceiverSock.setblocking(1)
        acquainted = False  # has the handshake been successful

        while not acquainted:
            print('Attempting handshake with UDP driver.')

            data, addr = self.receiveBlock()
            data = bytearray(data)
            print('Received handshake request from Unity: ' + str(int(data[0])))

            # send response with random byte
            response = random.randint(0, 255)
            print('Sending response to Unity: ' + str((data[0] + 1) % 256) + ' ' + str(response))
            self.send(str((data[0] + 1) % 256) + ' ' + str(response))

            # wait for second response
            data, addr = self.receiveBlock()
            data = bytearray(data)
            print('Received handshake response from Unity: ' + str(int(data[0])))
            if data[0] == (response + 1) % 256:
                acquainted = True
            else:
                print('Failed handshake. Retrying...\n')
                continue

        print('Successful handshake between Unity and Python.\n')
        self.UnityReceiverSock.setblocking(0)

    def __str__(self):
        """
        Output current state of MyoUDPTrainer object as a string.
        
        Keyword Arguments:
        self -- pointer to this object
        
        Return Arguments:
        string -- string detailing this object. Lists class names and number of samples of training data per each class
        """

        # perhaps adjust output based on VERBOSE
        #sizes = [0] * len(self.TrainingData.motion_names)
        #for i in range(len(self.TrainingData.id)):
        #    sizes[self.TrainingData.id[i]] += 1
        
        totals = self.TrainingData.get_totals()

        string = 'Myo Trainer Object:\n'
        
        if self.verb >= 1:
            string += 'Classification type: '
            string += 'Quadratic ' if self.quadratic else 'Linear '
            string += 'Discriminant Analysis\n'
        
        #list out amount of training data samples per each pose
        for i, name in enumerate(self.TrainingData.motion_names):
            string += 'Class: ' + name + '\tSamples: ' + str(totals[i]) + '\n'

        return string    
    
  

if __name__ == "__main__":
    """Select a method to execute as main if specified in command line arguments."""

    args = parse()
    switch = args.EXECUTE
    if (switch == 'UnityTrainer'):
        unity_trainer(args)
    elif (switch == 'demo'):
        demo(args)
    elif (switch == 'main'):
        main(args)
    elif (switch == 'replay'):
        replay(args)
    else:
        print('Invalid main method requested. No method mapped to "' + switch + '."')
