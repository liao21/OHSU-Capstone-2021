"""
Created on Tue Jul 19 11:16:36 2016

Initial creation of the training methods for LDA classification in Python

--VERBOSE  set to 2 or higher
Output timing information 

Most of the functionality is controlled by command line flags
e.g. if you want to do a demo (plus timing info), you can run: 
'python MyoUDPTrainer.py --EXECUTE demo --VERBOSE 2 --TRAIN 20 --PREDICT 1000'
Training builds on whatever saved training data is in the directory, so if you 
want to train from scratch, delete all of the files in the 'python\training_data\'
folder, and then rerun the script with the train flag (alternatively run delete() function).

WIP add delete flag to run delete method instead of manually deleting saved data
WIP change path behavior so that all paths use self.path
WIP add UDP communication to/from unity for training cues and other functionality

@author: D. Samson
"""

# perhaps import only into necessary scripts, rather than importing all at the beginning
import os
import sys
import time
import math
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.externals import joblib
from os.path import isfile
import argparse
import socket
import errno
import random
import traceback

from controls.plant import Plant
from inputs.myo import MyoUdp
from mpl.unity import UnityUdp
# from TrainingUdp import TrainingUdp
from pattern_rec.feature_extract import feature_extract


def unity_trainer(args):
    """Run Unity/Python sample trainer program. Python records myo data/runs LDA classifier based on Unity UDP cues
    
    Keyword arguments:
    args -- command line arguments parsed by python argparse. see function parse() for list of arguments
    
    UDP codes (received from Unity):
    'b' -- "Begin training"
    'a' -- "Acknowledged"
    'r' -- "Start Recording"
    
    UDP codes (sent from Python)
    '<pose name>' -- the name of the current pose to be recorded. Unity uses this to construct the UI text
    '<next pose>' -- synonym of above. Used to denote next pose in the sequence of training poses
    'a' -- "Acknowledged"
    'd' -- "Done Recording Pose"
    'f' -- "Finished Recording All Poses"
    
    UDP Unity/Python communication protocol
    Handshake - run to sync Python operations with Unity operations at the start of the program
    --Python waits for data signal from Unity
    --Unity generates a random byte [A] and sends it to Python
    --Python receives random byte [A], generates a random byte [B] and sends [A+1,B] to python as an acknowledgement
    --Unity receives [A+1,B], checks that the first byte is in fact [A+1], and sends [B+1] in response to Python. Unity now enters its main program
    --Python receives [B+1], checks that it is in fact [B+1], and then enters its main program section. The handshale is complete. Now Unity and Python are "acquainted".
    
    General training sequence - Unity cues Python to record training data when Unity receives UI input
    --When the "Begin Training" button is clicked, Unity sends to Python ['b'] for "begin training"
    --When python receives ['b'] it starts the training cycle, and responds with the name of the current pose ['<pose name>']
    --Unity receives ['<pose name>'] and uses it to update the UI text. Unity then sends to Python ['a'] for "acknowledged"
    --When the "Record Pose: <pose name>" button is clicked, Unity sends to Python ['r'] for "start recording <pose>"
    --Python receives ['r'] it responds with ['a'] for "acknowledged" and begins saving feature extracted Myo data into a list of data
    --When Python finishes recording the specified number of samples (controlled by input arg -t or --TRAIN) Python sends to Unity ['d'] for "done training"
    --Unity receives the ['d'] and then enters the cooldown phase.
    --Python begins transmitting ['<next pose>'] to Unity to reset the cycle for the new pose
    --When the cooldown is complete, Unity receives ['<next pose>'] responds with ['a'] for "acknowledged"
    --This process repeats until all of the poses have been trained.
    --At the end of recording the last pose, Python sends ['f'] for "finished training cycle" instead of ['<next pose>']
    --Unity receives ['f'], and hides the UI, then sends to Python ['a'] for "acknowledged"
    --Python receives ['a'], and saves the training data, then fits the training data to the LDA model.
    --Python then enters the prediction phase where it outputs joint angles to the vMPL based on the predicted pose for current Myo data 
    
    To-Do
    --When Unity quits, send a UDP command to Python to quit if it is running, so that things close properly
    --Make general training sequence less sequential, and more controllable by UDP cues. E.g.:
        --ability to progress to next pose signaled by Unity UI input
        --ability to return to previous pose signaled by Unity UI input
        --ability to pause/resume training sequence signaled by Unity UI input
        --ability to save/delete training data signaled by Unity UI input
        --<see Bobby for other python control features controlled by UDP from Unity UI>
        --(General Note about UDP control) UDP cues should be able to be from any arbitrary source, not just the Unity UI. I.e. Any program that sends the proper sequence of UDP cues to python should be able to control the training process.
    --Discover bug where vMPL changes position during resting phase. vMPl should remain in the same spot except for the hand motions
    --Update Plant.py so that control model uses ROC tables with interpolation as opposed to basic Python dictionary implemented. Update internal control model to handle ROC style Plant model
    """

    # state machine variable. Same states are mirrored in Unity script.
    STATES = enum(waitingHandshake=0, waitingStart=1, setupRecord=2, waitingRecord=3, recording=4, cooldown=5,
                  inactive=6, off=7, none=8)
    # initial state is waiting for Handshake from Unity
    state = STATES.waitingHandshake

    # Machine learning Myo UDP trainer controller
    trainer = MyoUDPTrainer(args)

    # handshake between unity and python
    trainer.handshake()

    state = STATES.waitingStart

    # load saved data from disk if available
    trainer.load()

    # Ideal communication protocal between unity and python
    # e.g. Unity -> '<command code><data>' -> Python
    # Python -> '<Acknowledgement>' -> Unity
    # sometimes the acknowledgement is omitted

    # Set arm to demonstration JointPosition
    trainer.hPlant.JointPosition[0] = 1
    trainer.hPlant.JointPosition[3] = 1.3
    trainer.hSink.send_joint_angles(trainer.hPlant.JointPosition)

    print('Waiting for Unity to send "Begin Training" cue.')
    while state == STATES.waitingStart:
        # wait for signal to begin 'b'
        data, addr = trainer.receiveBlock()
        data = bytearray(data)
        if data[0] == ord('q'):  # quit training session
            trainer.close()
            quit()
        if data[0] == ord('b'):
            state = STATES.setupRecord
            print('Beginning training session.\n')



            # adjust in future to read in classes based on unity settings/take all from ROC file
            # if trainer.TrainingName == []:
            # trainer.TrainingName = ['No Movement', 'Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Adduction',
            # 'Wrist Abduction', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp']

    for trainCycle in list(range(trainer.tcycles)):  # repeat training process a specified number of times
        for pose in trainer.TrainingName:  # run training process for each pose
            # Set arm to demonstration JointPosition
            trainer.hPlant.JointPosition[0] = 1
            trainer.hPlant.JointPosition[3] = 1.3
            trainer.hSink.send_joint_angles(trainer.hPlant.JointPosition)

            # train each pose while communicating with unity UI
            # tell unity pose name to be trained
            state = STATES.setupRecord  # Unity will initially still be in cooldown, so python waits until Unity acknowledges the start of the setupRecord phase
            print('waiting for acknowledgement that unity received pose: ' + pose + '.')
            while data == None or data[0] != ord('a'):
                trainer.send(pose)
                data, addr = trainer.receiveBlock()
                print('received packet: ' + str(data))
                if data != None:
                    data = bytearray(data)

                if data[0] == ord('q'):  # quit training session
                    trainer.close()
                    quit()

            start = time.time()
            while time.time() - start < 1:
                trainer.output(pose)

            state = STATES.waitingRecord
            print('waiting for training signal.')
            # wait for unity to signal recording of pose
            while data == None or data[0] != ord('r'):
                # trainer.output(pose)
                data, addr = trainer.receiveBlock()
                print('received packet: ' + str(data))
                if data != None:
                    data = bytearray(data)
                if data[0] == ord('q'):  # quit training session
                    trainer.close()
                    quit()
            trainer.send('a')
            state = STATES.recording
            trainer.trainSingle(trainer.TrainingName.index(pose), pause=1)
            trainer.send('d')

            # zero out hand joints
            for i in list(range(len(trainer.hPlant.JointPosition))):
                trainer.hPlant.JointPosition[i] = 0
            trainer.hPlant.JointPosition[0] = 1
            trainer.hPlant.JointPosition[3] = 1.3
            trainer.hSink.send_joint_angles(trainer.hPlant.JointPosition)

            state = STATES.cooldown  # python will immediately enter the setupRecord state while Unity will remain in cooldown until the cooldown timer completes

    # wait for end of unity cooldown. Notify that training is done.
    while data == None or data[0] != ord('a'):
        trainer.send('f')
        data, addr = trainer.receiveNoBlock(timeout=1.0)
        print('received packet: ' + str(data))
        if data != None:
            data = bytearray(data)
    trainer.save()
    trainer.fit()

    print('')
    print(str(trainer))

    print('Running prediction model:')
    trainer.predictMult()

    trainer.close()
    print('\nEnding program in 5 seconds...')
    time.sleep(5)


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
    
    UDP Cues for Trainer Functions
    (~ for no cue)
    Cue:                Function:                   Meaning:            Details:    
    ~                   __init__()            
    cc                  create()                    "class create"
    ca<class>           addClass(class)             "class add"
    cr<class>           removeClass(class)          "class remove"
    dc                  clear()                     "data clear"        
    dd                  delete()                    "data delete"
    df                  fit()                       "data fit"
    dl                  load()                      "data load"
    ds                  save()                      "data save"
    op                  output()                    "output plant"
    os                  print(__str__)              "output string"
    pm<count>           predictMult(count)          "predict multiple"  (<count> is optional. 'infinite' for -1, else, 1 uint8 for <count> value.)
    ps                  predictsingle()             "predict single"
    ta<samples,cycles>  trainall(samples, cycles)   "train all"         (<samples> is optional; 1 uint8 for value at data[2]. <cycles> is optional (requires samples present); 1 uint8 at data[3].)
    tn                  (next pose)                 "train next"        ((not a function) increments a class counter by 1) (overflow causes a UDP reply 'o')
    tp                  (previous pose)             "train previous"    ((not a function) decrements a class counter by 1) (underflow causes a UDP reply 'o')
    ts<cycles>          trainsingle()               "train single"      (<cycles> is optional. 1 uint8 for <cycles> value)
    ~                   send()           
    ~                   receiveNoBlock()
    ~                   receiveBlock()
    ~                   handshake()

    Others UDP Codes:
    code:               Meaning:                    Details:
    {ACK} (0x06)        "Acknowledged"
    {NAK} (0x15)        "Negative Acknowledge"
    o                   "counter out of bounds"     (sent when 'tn' or 'tp' is received and counter would progress past -1, or len(classes)) (i.e. counter at start or end of class list)
    q                   "quit (current loop)"
    
    """

    print('Running UDP driven trainer. Progress will only continue if proper UDP cues are returned.\n')

    # state machine variable. Same states are mirrored in Unity script.
    # STATES = enum(waitingHandshake=0, waitingStart=1, setupRecord=2, waitingRecord=3, recording=4, cooldown=5, inactive=6, off=7, none=8)
    # initial state is waiting for Handshake from Unity
    # state = STATES.waitingHandshake

    # Machine learning Myo UDP trainer controller
    trainer = MyoUDPTrainer(args)

    # handshake between unity and python
    trainer.handshake()

    # state = STATES.waitingStart

    data, addr = None, None  # current UDP packet received from Unity
    curPose = 0  # index of the current pose being operated on

    # handle generic UDP cues
    print('Start of UDP flow control section.')
    while data is None or data[0] != ord('q'):  # 'q' cue for "quit"
        try:
            print('Waiting for UDP data packet...')
            data, addr = trainer.receiveBlock()
            data = bytearray(data)
            print('Received packet: ' + str(data)[12:-2])

            if data[0] == ord('d'):  # data
                if data[1] == ord('s'):  # save
                    trainer.save()

                elif data[1] == ord('l'):  # load
                    trainer.load()

                elif data[1] == ord('d'):  # delete
                    trainer.delete()

                elif data[1] == ord('c'):  # clear
                    trainer.clear()

                elif data[1] == ord('f'):  # fit to model
                    trainer.fit()

            elif data[0] == ord('c'):  # class (poses)
                if data[1] == ord('c'):  # create (defaults)
                    trainer.create()

                elif data[1] == ord('a'):  # add
                    className = data[2:].decode('utf-8')
                    trainer.addClass(className)

                elif data[1] == ord('r'):  # remove
                    className = data[2:].decode('utf-8')
                    trainer.removeClass(className)

            elif data[0] == ord('o'):  # output
                if data[1] == ord('s'):  # tostring
                    print(str(trainer))

                elif data[1] == ord('p'):  # plant
                    # output plant. not sure how this would be used...
                    pass

            elif data[0] == ord('p'):  # predict
                if data[1] == ord('m'):  # multiple
                    if len(data) == 3:
                        trainer.predictMult(data[2])
                    elif len(data) > 3 and data[2:].decode('utf-8').lower() == 'infinity':
                        trainer.predictMult(-1)
                    else:
                        trainer.predictMult()  # use settings in object

                elif data[1] == ord('s'):  # single
                    print(trainer.predictSingle())  # this isn't useful in generic UDP control mode
                    pass

            elif data[0] == ord(
                    't'):  # train (handles sequence for training poses, e.g. progressing to next pose, training current pose, etc.)
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

                elif data[1] == ord('n'):  # (goto) next pose
                    if curPose + 1 < len(trainer.TrainingName):
                        curPose += 1
                        print('Current pose set to "' + trainer.TrainingName[curPose] + '."\n')
                    else:
                        # curPose = 0  #may want to delete this line
                        print('Already at last pose "' + trainer.TrainingName[curPose] + '."\n')
                        trainer.send('o')  # pose overflow

                elif data[1] == ord('p'):  # (goto) previous pose

                    if curPose > 0:
                        curPose -= 1
                        print('Current pose set to "' + trainer.TrainingName[curPose] + '."\n')
                    else:
                        # curPose = len(trainer.TrainingName) - 1 #may want to delete this line.
                        print('Already at first pose "' + trainer.TrainingName[curPose] + '."\n')
                        trainer.send('o')

                elif data[1] == ord('f'):  # (goto) first pose
                    curPose = 0
                    print('Current pose set to "' + trainer.TrainingName[curPose] + '."\n')

                elif data[1] == ord('l'):  # (goto) last pose
                    curPose = len(trainer.TrainingName) - 1
                    print('Current pose set to "' + trainer.TrainingName[curPose] + '."\n')

            elif data[0] == '':
                pass

            elif data[0] == '':
                pass

            else:
                print('Unrecognized data packet. Restarting control loop.\n')

            pass  # do stuff

        # error handling
        except Exception as err:  # print the exception, and continue running UDP flow control loop
            try:
                exc_info = sys.exc_info()
            finally:
                print('\nError occured in execution loop.')
                traceback.print_exception(*exc_info)
                print('')
                del exc_info
            pass
        pass
    # End of UDP flow control loop

    print('Exiting UDP flow control section.\n')

    trainer.close()
    # print('\nEnding program in 5 seconds...')
    # time.sleep(5)


    pass


def demo(args):
    """console demo of training sequence."""

    trainer = MyoUDPTrainer(args)
    print('')

    if args.DELETE:
        trainer.delete()
    # trainer.create()

    testClasses = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open',
                   'Spherical Grasp', 'No Movement']
    # import poses example
    for pose in testClasses:
        try:
            trainer.addClass(pose)
        except:
            pass

    # trainer.addClass('randomClass')

    # trainer.removeClass('randomClass')
    # trainer.removeClass('No Movement')
    # trainer.addClass('No Movement')

    if args.DELETE == False:
        trainer.load()
    trainer.trainAll()
    trainer.save()
    trainer.fit()

    print('')
    print(str(trainer))

    print('Running prediction model:')
    trainer.predictMult()
    pass


def replay(args):
    """replay using saved training data"""

    trainer = MyoUDPTrainer(args)
    print('')
    trainer.load()
    trainer.fit()

    print('')
    print(str(trainer))

    print('Running prediction model:')
    trainer.predictMult()
    pass


def enum(**enums):
    """adding Enum support to Python."""
    return type('Enum', (), enums)


class MyoUDPTrainer:
    """Python Class for managing machine learning and Myo training operations."""

    def __init__(self, args, path=None):
        """
        Initialize the MyoUDPTrainer object.
        
        Keyword Arguments:
        self -- pointer to this object
        args -- preparsed command-line arguments. Comprise most of the instance data of this object
        path -- (Optional) If passed in, sets the path to load/save data from. Otherwise path is set to current location of this file
        """

        # Set MyoUDPTrainer object instance data
        self.TrainingData = []  # List of all feature extracted samples
        self.TrainingClass = []  # List of class indices that each sample belongs to
        self.TrainingName = []  # Name of each class

        if path == None:  # path to script location. Saved data will be saved/accessed from here.
            self.path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.path = path

        if args.DELETE:
            self.delete()

        self.quadratic = args.QUADRATIC  # set Quadratic Discriminant Analysis mode. False means LDA mode
        self.tsamples = args.TRAIN  # how many samples per training each class
        self.tcycles = args.TRAIN_LOOP  # hoe many cycles of training each pose to repeat
        self.dt = 1.0 / args.FREQUENCY  # how frequently do training and prediction loops run
        self.verb = args.VERBOSE  # how much information output to the console
        self.pcycles = args.PREDICT  # how many cycles to predict for. setting to -1 means infinite cycles
        self.hMyo = MyoUdp()  # Signal Source get external bio-signal data
        self.ROCFile = '../../WrRocDefaults.xml'  # ROC file for possible motion classes
        self.hPlant = Plant(self.dt,
                            self.ROCFile)  # Plant maintains current limb state (positions) during velocity control
        self.hSink = UnityUdp()  # ("192.168.1.24")   # Sink is output to ouside world (in this case to VIE)
        self.clf = None  # Fit training data model

        self.UDP_IP = args.UDP_IP  # IP address to communicate with unity through (directed to localhost).
        self.PYTHON_SEND_PORT = args.PYTHON_PORT  # from python send data to unity using this port
        self.UNITY_RECEIVE_PORT = args.UNITY_PORT  # from unity receive data in python using this port

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
        """

        if samples == None:
            samples = self.tsamples
        if cycles == None:
            samples = self.tcycles

        if samples > 0:
            print('\n\nBeginning training Regime in 5 seconds...')
            print('(Ready for first pose "' + self.TrainingName[0] + '"')
            time.sleep(5)

            print('')
            for cycle in list(range(cycles)):
                print('Training Cycle #' + str(cycle) + '\n')
                for classNum, className in enumerate(self.TrainingName):
                    self.trainSingle(classNum, samples)
        print('Finished training all poses.\n')

    def trainSingle(self, classNum, samples=None, pause=3):
        """
        Run training regime for single specified pose.
        
        Keyword Arguments:
        self -- pointer to this object
        samples -- (Optional) If passed in, overrides number of samples to collect for each pose. Otherwise uses number of samples specified in self.tsamples
        pause -- (Optional) If passed in, set how long to pause before recording the Myo data. Otherwise default pause is 3 seconds
        """

        if samples == None:
            samples = self.tsamples

        print('pose: ' + self.TrainingName[classNum])
        time.sleep(pause)

        if self.verb == 0:
            print('Collecting EMG samples...')

        for i in list(range(samples)):
            loopStart = time.time()
            emgData = self.hMyo.get_data() * 0.01
            f = (feature_extract(emgData)).tolist()[0]
            self.TrainingData.append(f)
            self.TrainingClass.append(classNum)

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

        if len(self.TrainingData) == 0 or len(self.TrainingClass) == 0:
            raise ValueError('Training Data or Class array(s) is empty. Did you forget to save training data?')
        if len(self.TrainingData) != len(self.TrainingClass):
            raise ValueError(
                'Training Data and Training class arrays are incompatable sizes. Try generating new training data from scratch.')

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
        while i != cycles and (data == None or data[0] != ord('q')):
            data, addr = self.receiveNoBlock()  # receive UDP data to allow for exiting infinite loop
            loopStart = time.time()
            prediction = self.predictSingle()
            if self.verb >= 1:
                print('prediction: ' + prediction)
            if self.verb >= 2:
                print(('QDA' if self.quadratic else 'LDA') + ' prediction execution time: ' + str(
                    time.time() - loopStart) + 's')

            self.output(prediction, True)

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
        prediction -- model class prediction of current class based on current Myo data
        """
        return self.TrainingName[self.clf.predict(feature_extract(self.hMyo.get_data() * 0.01))]

    def output(self, classDecision, upperAngles=False):
        """
        Update and output joint angles to vMPL based on class specified.
        
        Keyword Arguments:
        self -- pointer to this object
        classDecision -- string that names the pose to output
        upperAngles -- (Optional) If passed in, specifies whether or not to output upper arm angles based on Myo orientation data. Otherwise defaults to False
        """

        # Move joints using classifier
        # try:
        gain = 2.0

        classInfo = self.hPlant.class_map(classDecision)

        # Set joint velocities
        self.hPlant.new_step()
        # set the mapped class
        if classInfo['IsGrasp']:
            if classInfo['GraspId'] is not None:
                self.hPlant.GraspId = classInfo['GraspId']
            self.hPlant.set_grasp_velocity(classInfo['Direction'] * gain)
        else:
            self.hPlant.set_joint_velocity(classInfo['JointId'], classInfo['Direction'] * gain)

        self.hPlant.update()

        if upperAngles:
            # perform joint motion update
            vals = self.hMyo.get_angles()
            self.hPlant.JointPosition[3] = vals[1] + math.pi / 2

        # transmit output
        self.hSink.send_joint_angles(self.hPlant.JointPosition)

        # except:
        #    print('Class "' + classDecision + '" not available from ROC table.')
        #    #jointId, jointDir = [[],0]
        #    pass    

    def save(self, path=None):
        """
        Save the current data to the disk.
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides the path to save the data to. Otherwise save data to path at self.path
        """

        if path == None:
            path = self.path

        start = time.time()

        print('Saving emg feature data to test file.')
        trainFolder = os.path.join(path, 'training_data')

        if not os.path.exists(trainFolder):
            os.makedirs(trainFolder)

        joblib.dump(np.array(self.TrainingData), trainFolder + os.sep + 'X.pkl')
        joblib.dump(np.array(self.TrainingClass), trainFolder + os.sep + 'y.pkl')
        joblib.dump(self.TrainingName, trainFolder + os.sep + 'className.pkl')

        if self.verb >= 2:
            print('Save training data execution time: ' + str(time.time() - start) + 's')

        print('')

    def load(self, path=None):
        """
        Load training data from disk. Training data is stored into self.TrainingData, self.TrainingClass, and self.TrainingName.
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides path that training data is loaded from. Otherwise data is loaded from self.path
        """

        if path == None:
            path = self.path
        trainFolder = os.path.join(path, 'training_data')

        # Check if data already exists
        # Manipulate data as python arrays, then convert to numpy arrays when final size reached
        saved = isfile(trainFolder + os.sep + 'X.pkl') and isfile(trainFolder + os.sep + 'y.pkl') and isfile(
            trainFolder + os.sep + 'className.pkl')
        if saved:
            # load from files
            print('Found saved training data. Loading training data from files.')
            self.TrainingData = joblib.load(trainFolder + os.sep + 'X.pkl').tolist()
            self.TrainingClass = joblib.load(trainFolder + os.sep + 'y.pkl').tolist()
            self.TrainingName = joblib.load(trainFolder + os.sep + 'className.pkl')
        else:
            print('No training data found.')
            self.create()

        # perform error checks here:
        # if error: self.create()
        print('')

    def delete(self, path=None):
        """
        Delete training data from disk.
        
        Keyword Arguments:
        self -- pointer to this object
        path -- (Optional) If passed in, overrides path that training data is deleted from. Otherwise data is deleted from self.path
        """
        print('Deleting saved data.\n')

        if path == None:
            path = self.path
        trainFolder = os.path.join(path, 'training_data') + os.sep

        if isfile(trainFolder + 'X.pkl'):
            os.remove(trainFolder + 'X.pkl')
        if isfile(trainFolder + 'y.pkl'):
            os.remove(trainFolder + 'y.pkl')
        if isfile(trainFolder + 'className.pkl'):
            os.remove(trainFolder + 'className.pkl')

    def clear(self):
        """
        Clear training data. 
        Blank training data is stored into self.TrainingData, self.TrainingClass, and self.TrainingName.
        
        Keyword Arguments:
        self -- pointer to this object
        """

        # create new data from default
        print('Clearning set of training data.\n')
        self.TrainingData = []
        self.TrainingClass = []
        self.TrainingName = []

    def create(self):
        """
        Create initial training data from scratch. 
        Blank training data is stored into self.TrainingData and self.TrainingClass
        Default data is stored into self.TrainingName.
        
        Keyword Arguments:
        self -- pointer to this object
        """

        # create new data from default
        print('Creating new set of training data with default classes.\n')
        self.TrainingData = []
        self.TrainingClass = []
        # TrainingName should be loaded from the current ROC file, or start blank, and then addClass for each class
        # self.TrainingName = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp', 'No Movement']
        # self.TrainingName = ['No Movement', 'Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Adduction',
        #    'Wrist Abduction', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp']
        self.TrainingName = ['No Movement', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp']

        pass

    def close(self):
        """Cleanup currently opened UDP objects."""
        print('')
        print('Cleaning up...')
        print('')
        self.hSink.close()
        self.hMyo.close()

    def addClass(self, newClass):
        """
        Add a pose to the list of poses that are in the training set. New class is added to self.TrainingName (with no initial training data).
        
        Keyword Arguments:
        self -- pointer to this object
        newClass -- string that names the pose to add
        """
        if newClass not in self.TrainingName:
            print('Adding class "' + newClass + '" to pose list.\n')
            self.TrainingName.append(newClass)
        else:
            raise ValueError('Cannot add class "' + newClass + '" to training set. Class already exists in object.')

    def removeClass(self, toRemove):
        # bug, need to shift indexes so that class numbers are correctly sized
        """
        Delete a pose from the list of poses that are in the training set. New class is deleted from self.TrainingName along with all associated training data in self.TrainingData and self.TrainingClass.
        
        Keyword Arguments:
        self -- pointer to this object
        newClass -- string that names the pose to add
        """
        print('Attempting to remove class "' + toRemove + '."\n')

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
                    # classNum = self.TrainingClass[i]
                    # if classNum > remIndex:
                    # classNum -= 1

                    newClass.append(
                        self.TrainingClass[i] - (1 if i > remIndex else 0))  # Convert indexes above removed class
                    newData.append(self.TrainingData[i])

        self.TrainingData = newData
        self.TrainingClass = newClass
        self.TrainingName = newName
        if self.verb > 3:
            print(newData)
            print(newClass)
            print(newName)

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
        sizes = [0] * len(self.TrainingName)
        for i in range(len(self.TrainingClass)):
            sizes[self.TrainingClass[i]] += 1

        string = 'Myo Trainer Object\n'
        for i, name in enumerate(self.TrainingName):
            string += 'Class: ' + name + '\tSamples: ' + str(sizes[i]) + '\n'

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
