"""
Created on Tue Jan 23 10:17:58 2016

Initial pass at simulating MiniVIE processing using python so that this runs on an embedded device

@author: R. Armiger
"""

import os
import sys
import math
import time
import numpy as np

from inputs.myo import MyoUdp
from controls.plant import Plant, class_map
from mpl.unity import UnityUdp
from pattern_rec import training, feature_extract

VERBOSE = 0
dt = 0.02  # seconds per loop.  50Hz update


def setup():
    """ 
    Create the building blocks of the MiniVIE
    
        SignalSource - source of EMG data
        SignalClassifier - algorithm to classify emg into 'intent'
        Plant - Perform forward integration and apply joint limits
        DataSink - output destination of command signals (e.g. real or virtual arm)
    """
        
    filename = "../../WrRocDefaults.xml"
    # Create data objects

    # Signal Source get external bio-signal data
    # For MPL, this might be CPC Headstage, External Signal Acquisition, MyoBand, etc.
    # data_src = MyoUdp()#("192.168.1.3")
    data_src = MyoUdp(source='//127.0.0.1:15001', num_samples=20)  # ("192.168.1.3")
    data_src.connect()

    # Training Data holds data labels 
    trainer = training.TrainingUdp()

    # Plant maintains current limb state (positions) during velocity control
    # TODO[Lydia2] This can fail if file does not exist, then the UDP objects aren't cleaned up properly
    plant = Plant(dt, filename)

    # Sink is output to outside world (in this case to VIE)
    # For MPL, this might be: real MPL/NFU, Virtual Arm, etc.
    data_sink = UnityUdp()  # ("192.168.1.24")

    # Classifier parameters
    train_folder = os.path.join(os.getcwd(), 'scenarios/training_data')
    # TODO: generate defaults if these files don't exist, or are corrupt
    # TODO: Perform error checking to ensure number of Classes match matrix sizes
    w = np.genfromtxt(os.path.join(train_folder, "weights.txt"), dtype=None)
    c = np.genfromtxt(os.path.join(train_folder, "centers.txt"), dtype=None)
    # Classifier class names 
    with open(os.path.join(train_folder, "classes.txt")) as f:
        class_names = f.read().splitlines()

    classifier = (w, c, class_names)

    # create file for dumping training data
    # TODO[Lydia2]: store training data more efficiently and explicitly
    file = open(os.path.join(train_folder, 'training_dump.dat'), 'w')
    
    return {'SignalSource': data_src, 'SignalClassifier': classifier, 'DataSink': data_sink,
            'Plant': plant, 'Trainer': trainer, 'TmpFile': file}


def model(signal_source, signal_classifier, plant, data_sink, trainer, file):

    # Get data and extract features
    emg_data = signal_source.get_data() * 0.01
    # feature vector should be [1,nChan*nFeat]
    # data ordering is as follows
    # [ch1f1, ch1f2, ch1f3, ch1f4, ch2f1, ch2f2, ch2f3, ch2f4, ... chNf4]
    f = feature_extract(emg_data)
    print('%8.4f %8.4f %8.4f %8.4f' % (f[0, 0], f[0, 0], f[0, 0], f[0, 0]))
    # Classify
    w = signal_classifier[0]
    c = signal_classifier[1]
    class_names = signal_classifier[2]
    
    # features[1,nChan*nFeat] * Wg[nChan*numFeat,nClasses] + Cg[1,nClasses]
    v = np.dot(f, w) + c
    class_num = v.argmax()

    class_decision = class_names[class_num]
    
    # Move joints using classifier
    gain = 2.0
    
    class_info = class_map(class_decision)

    # Set joint velocities
    plant.new_step()
    # set the mapped class
    if class_info['IsGrasp']:
        if class_info['GraspId'] is not None:
            plant.grasp_id = class_info['GraspId']
        plant.set_grasp_velocity(class_info['Direction'] * gain)
    else:
        plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * gain)
    
    plant.update()

    # Non-EMG Motion based inputs [Optional]
    # perform joint motion update
    vals = signal_source.get_angles()
    # Temp: Overwrite Elbow angle based on Myo orientation
    plant.joint_position[3] = vals[1] + math.pi / 2

    # transmit output
    data_sink.send_joint_angles(plant.joint_position)

    # TODO[Lydia2]: Update training 
    # Training Process begin logging
    # [Lydia2] Efficient way to organize incoming messages, store labeled data on disk
    # [Lydia3] Implement LDA in python to regen training parameters
    class_name = str(trainer.class_name)  # Do I have an external command?
    if class_name:
        # If external command, write the data and label to disk
        print(class_name)
        # txt = ','.join(map(str, f.tolist()))
        f.tofile(file)
        # file.write(' %d %s\n'%(Trainer.class_id, class_name))
    
    # Training Process end

    # DEBUG output display
    if VERBOSE:
        # print(f[:1,:])
        print(("%8.4f" % plant.joint_position[3], "%8.4f" % plant.joint_position[4]), 'Class: %s' % class_names[class_num])


def main():
    """ Main function that involves setting up devices,
        looping at a fixed time interval, and performing cleanup
    """

    h = setup()

    # Iteration counter
    cycle_max = 140  # Max iterations (0 for infinite)
    cycle_cnt = 0  # Internal Counter
    time_elapsed = -1

    try:
    
        # setup main loop control
        print("")
        print("Running...")
        print("")
        sys.stdout.flush()

        while (cycle_max > 0) and (cycle_cnt < cycle_max):  # main loop
            # Fixed rate loop.  get start time, run model, get end time; delay for duration 
            time_begin = time.time()
            
            # Increment loop counter
            cycle_cnt += 1
 
            # Run the actual model
            model(h['SignalSource'], h['SignalClassifier'], h['Plant'], h['DataSink'], h['Trainer'], h['TmpFile'])

            time_end = time.time()
            time_elapsed = time_end - time_begin
            if dt > time_elapsed:
                time.sleep(dt-time_elapsed)
            else:
                print("Timing Overload")

    finally:        
        print("")
        # print("EMG Buffer:")
        # print(hMyo.getData())
        print("Last time_elapsed was: ", time_elapsed)
        print("")
        print("Cleaning up...")
        print("")

        h['SignalSource'].close()
        h['DataSink'].close()
        h['Trainer'].close()
        h['TmpFile'].close()    # close file
        # Add short delay to view any final messages
        time.sleep(2.0)

        
if __name__ == "__main__":
    main()
