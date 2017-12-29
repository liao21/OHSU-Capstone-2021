import time
import logging
import utilities
from utilities.user_config import read_user_config, get_user_config_var
import mpl
from collections import Counter, deque


class Scenario(object):
    """
    Define the building blocks of the MiniVIE

        SignalSource - source of EMG data
        SignalClassifier - algorithm to classify emg into 'intent'
        Plant - Perform forward integration and apply joint limits
        DataSink - output destination of command signals (e.g. real or virtual arm)
    """

    def __init__(self):
        # import socket
        self.SignalSource = None
        self.SignalClassifier = None
        self.FeatureExtract = None
        self.TrainingData = None
        self.TrainingInterface = None
        self.Plant = None
        self.DataSink = None

        # Debug socket for streaming Features
        # self.DebugSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Training parameters
        self.add_data = False
        self.add_data_last = False  # Track whether data added on previous update, necessary to know when to autosave
        self.auto_save = True  # Boolean, if true, will save out training data every time new data finished being added
        self.training_motion = 'No Movement'
        self.training_id = 0

        self.num_channels = 0

        self.decision_buffer = deque([], get_user_config_var('NumMajorityVotes', 25))

        self.output = None  # Will contain latest status message

        # User should access values through the is_paused method
        self.__pause = {'All': False, 'Arm': False, 'Hand': False}

        # Control gains and speeds for precision control mode
        self.precision_mode = False
        self.gain_value = 1.4
        self.gain_value_last = self.gain_value
        self.gain_value_precision = 0.2
        self.hand_gain_value = 1.2
        self.hand_gain_value_last = self.hand_gain_value
        self.hand_gain_value_precision = 0.15

    def set_precision_mode(self, value):
        # Select between precision mode or default mode.
        # When switching, gain values for alternate mode will be preserved.
        #
        # Input argument can be True/False or 1/0

        self.precision_mode = value
        if value:
            logging.info('Switching to precision gain mode')
            # Arm gain
            self.gain_value_last = self.gain_value  # preserve this for later
            self.gain_value = self.gain_value_precision
            # Hand gain
            self.hand_gain_value_last = self.hand_gain_value  # preserve this for later
            self.hand_gain_value = self.hand_gain_value_precision

        else:
            logging.info('Switching to default gain mode')
            # Arm gain
            self.gain_value_precision = self.gain_value  # preserve this for later
            self.gain_value = self.gain_value_last
            # Hand gain
            self.hand_gain_value_precision = self.hand_gain_value  # preserve this for later
            self.hand_gain_value = self.hand_gain_value_last

    def is_paused(self, scope='All'):
        # return the pause value for the given context ['All' 'Arm' 'Hand']
        return self.__pause[scope]

    def pause(self, scope='All', state=None):
        # Toggles pause state which suspends motion of arm
        #
        # State can be forced with optional value argument
        #
        # pause('All') Toggle
        # pause('All', True) Force PAUSE
        # pause('All', False) Force RESUME

        # check if 2 args given (set versus toggle)
        if state is not None: 
            # need to toggle only if state not already set
            if state is not self.__pause[scope]:
                # this should only happen once when state is changed
                self.__pause[scope] = state

            # return either way
            return

        if self.__pause[scope]:
            self.__pause[scope] = False
        else:
            self.__pause[scope] = True

    def gain(self, factor):
        # Increase the speed of the arm and apply max / min constraints
        self.gain_value *= factor
        if self.gain_value < 0.1:
            self.gain_value = 0.1
        if self.gain_value > 5:
            self.gain_value = 5

    def hand_gain(self, factor):
        # Increase the speed of the hand and apply max / min constraints
        self.hand_gain_value *= factor
        if self.hand_gain_value < 0.1:
            self.hand_gain_value = 0.1
        if self.hand_gain_value > 5:
            self.hand_gain_value = 5

    def command_string(self, value):
        """
        This function accepts training commands

        Commands are strings with the following format:

        [CMD_TYPE]:[CMD_VALUE]

        [CMD_TYPE] options are:
            Cls - Indicates the cmd_value is the name of a motion class to be selected
            Cmd - Indicates the cmd_value is a command word. Options are:
                Shutdown - Send shutdown command to the OpenNFU
                Add - Begin adding data to the currently selected class
                Stop - Stop adding data to the currently selected class
                ClearClass - Clear the data for the currently selected class
                ClearAll - Clear all the labeled training data
                Train - Recompute the classifier based on the current data
                Save - Save all labeled training data to TRAINING_DATA.hdf5 file (note this also issues a backup)
                Backup - Copy the data in TRAINING_DATA.hdf5 to a timestamped backup file
                Pause - Temporarily Suspend Motion of the limb system
                SpeedUp - Increase speed of all arm joints
                SpeedDown - Decrease speed of all arm joints
                HandSpeedUp - Increase speed of hand motions
                HandSpeedDown - Decrease speed of hand motions
                PrecisionModeOff - Reset hand and arm speed to default values
                PrecisionModeOn - Set hand and arm speed to precision values
                AutoSaveOn - Automatically save training data when new data added
                AutoSaveOff - Turn off autosave feature

        TODO: add classifier options to train and switch between LDA, QDA, SVM, etc
        TODO: add reset to hand/arm speed
        """

        # Commands should come in with colon operator
        # e.g. Cmd:Add or Cls:Elbow Flexion
        logging.info('Received new scenario command:' + value)

        parsed = value.split(':', 1)
        if not len(parsed) == 2:
            logging.warning('Invalid scenario command: ' + value)
            return
        else:
            cmd_type = parsed[0]
            cmd_data = parsed[1]

        if cmd_type == 'Cls':
            # Parse a Class Message
            try:
                self.training_id = self.TrainingData.motion_names.index(cmd_data)
                self.training_motion = cmd_data
            except ValueError:
                logging.error('Unmatched training class name: {}'.format(cmd_data))
            self.add_data = False

        elif cmd_type == 'Log':
            # Parse a log message
            print("User inserted log message: " + cmd_data)
            logging.critical("User inserted log message: " + cmd_data)

        elif cmd_type == 'Cmd':

            ###################
            # Training Options
            ###################
            if cmd_data == 'Add':
                self.add_data = True
            elif cmd_data == 'Stop':
                self.add_data = False
                self.SignalClassifier.fit()
            elif cmd_data == 'ClearClass':
                self.TrainingData.clear(self.training_id)
                self.SignalClassifier.fit()
            elif cmd_data == 'ClearAll':
                self.TrainingData.reset()
                self.SignalClassifier.fit()
            elif cmd_data == 'Train':
                self.SignalClassifier.fit()
            elif cmd_data == 'Save':
                self.TrainingData.copy()
                self.TrainingData.save()
            elif cmd_data == 'Backup':
                self.TrainingData.copy()

            elif cmd_data == 'AutoSaveOn':
                self.auto_save = True
            elif cmd_data == 'AutoSaveOff':
                self.auto_save = False

            ######################
            # MPL Control Options
            ######################
            elif cmd_data == 'ResetTorqueOn':
                self.DataSink.reset_impedance = True
            elif cmd_data == 'ResetTorqueOff':
                self.DataSink.reset_impedance = False

            elif cmd_data == 'ImpedanceOn':
                self.DataSink.enable_impedance = 1
            elif cmd_data == 'ImpedanceOff':
                self.DataSink.enable_impedance = 0

            elif cmd_data == 'ImpedanceLow':
                self.DataSink.impedance_level = 'low'
            elif cmd_data == 'ImpedanceHigh':
                self.DataSink.impedance_level = 'high'

            elif cmd_data == 'ReloadRoc':
                # Reload xml parameters and ROC Table
                # RSA: Update reload both ROC and xml config parameters
                read_user_config(reload=True)
                self.Plant.load_roc()
                self.Plant.load_config_parameters()
                self.DataSink.load_config_parameters()

            elif cmd_data == 'GotoHome':
                self.pause('All', True)
                angles = [0.0] * mpl.JointEnum.NUM_JOINTS
                self.DataSink.goto_smooth(angles)
                time.sleep(0.1)
                # synch percept position and plant position
                self.Plant.joint_position = self.DataSink.position['last_percept'][:]
                time.sleep(0.1)
                self.pause('All', False)

            elif cmd_data == 'GotoPark':
                self.pause('All', True)
                angles = self.DataSink.position['park']
                self.DataSink.goto_smooth(angles)
                time.sleep(0.1)
                # synch percept position and plant position
                self.Plant.joint_position = self.DataSink.position['last_percept'][:]
                time.sleep(0.1)
                self.pause('All', False)

            ######################
            # Myo Control Options
            ######################
            elif cmd_data == 'RestartMyo1':
                utilities.restart_myo(1)
            elif cmd_data == 'RestartMyo2':
                utilities.restart_myo(2)
            elif cmd_data == 'ChangeMyoSet1':
                utilities.change_myo(1)
            elif cmd_data == 'ChangeMyoSet2':
                utilities.change_myo(2)

            #################
            # System Options
            #################
            elif cmd_data == 'Reboot':
                # utilities.reboot()
                # Try to set the limb state to soft reset
                try:
                    self.DataSink.set_limb_soft_reset()
                except AttributeError:
                    logging.warning('set_limb_soft_reset mode not defined')
            elif cmd_data == 'Shutdown':
                # utilities.shutdown()
                pass

            ################
            # Speed Options
            ################
            elif cmd_data == 'PrecisionModeOff':
                self.set_precision_mode(False)
            elif cmd_data == 'PrecisionModeOn':
                self.set_precision_mode(True)

            elif cmd_data == 'SpeedUp':
                self.gain(1.2)
            elif cmd_data == 'SpeedDown':
                self.gain(0.8)

            elif cmd_data == 'HandSpeedUp':
                self.hand_gain(1.2)
            elif cmd_data == 'HandSpeedDown':
                self.hand_gain(0.8)

            elif cmd_data == 'PauseHand':
                self.pause('Hand')

            elif cmd_data == 'PauseAllOn':
                self.pause('All', True)
                # Try to set the limb state to soft reset
                try:
                    self.DataSink.set_limb_soft_reset()
                except AttributeError:
                    logging.warning('set_limb_soft_reset mode not defined')
            elif cmd_data == 'PauseAllOff':
                # Synchronize current position
                # Wait for a new percept
                # Then set plant position to percept position

                self.DataSink.position['last_percept'] = None
                time.sleep(0.1)
                self.DataSink.wait_for_connection()
                # synchronize percept position and plant position
                self.Plant.joint_position = self.DataSink.position['last_percept'][:]
                time.sleep(0.1)

                self.pause('All', False)
            elif cmd_data == 'PauseHandOn':
                self.pause('Hand', True)
            elif cmd_data == 'PauseHandOff':
                self.pause('Hand', False)

            else:
                # It's ok to have commands that don't match here.  another callback might use them
                # logging.info('Unknown scenario command: ' + cmd_data)
                pass

    def attach_source(self, input_source):
        # Pass in a list of signal sources and they will be added to the scenario

        self.SignalSource = input_source

        for s in input_source:
            s.connect()
            self.num_channels += s.num_channels

    def update(self):
        """
        Perform forward classification and return a dictionary with status information

        This is the main step for the vie consisting of the following steps:

            Get data from signal sources
                - If the data is to be used for training purposes, label it
            Filter data / extract features
            Classify signals
            Use class decision to determine limb motion
            Move limb
            Send output

        :return:
            output = {'status': 'RUNNING', 'features': None, 'decision': 'None'}

        """
        from controls.plant import class_map
        # import struct

        # initialize output
        self.output = {'status': 'RUNNING', 'features': None, 'decision': 'None', 'vote': None}

        # get data / features
        self.output['features'], f, imu = self.FeatureExtract.get_features(self.SignalSource)

        # Debug stream:
        # values = self.output['features']
        # print(values)
        # packer = struct.Struct('64f')
        # packed_data = packer.pack(*values)
        # self.DebugSock.sendto(packed_data, ('192.168.7.1', 23456))

        # if simultaneously training the system, add the current results to the data buffer
        if self.add_data and f.any():
            self.TrainingData.add_data(self.output['features'], self.training_id, self.training_motion, imu)

        # save out training data if auto_save is on, data just finished being added
        if self.auto_save and self.add_data_last and not self.add_data:
            self.TrainingData.delete()  # Lets delete so we have a clean file to write to
            self.TrainingData.save()
        # track previous add_data state
        self.add_data_last = self.add_data

        # classify
        decision_id, self.output['status'] = self.SignalClassifier.predict(f)
        if decision_id is None:
            return self.output

        # perform majority vote
        # Note Counter used here instead of statitstics.mode since that will raise error if equal frequency of values,
        # which can happen even if the buffer length is odd
        self.decision_buffer.append(decision_id)
        counter = Counter(self.decision_buffer)

        if self.TrainingData.motion_names[decision_id] != 'No Movement':
            # Immediately stop if class is no movement, otherwise use majority vote
            decision_id = counter.most_common(1)[0][0]

        # get decision name
        class_decision = self.TrainingData.motion_names[decision_id]
        self.output['decision'] = class_decision

        # parse decision type as arm, grasp, etc
        class_info = class_map(class_decision)

        # Set joint velocities
        self.Plant.new_step()

        # pause if applicable
        if self.is_paused('All'):
            self.output['status'] = 'PAUSED'
            return self.output
        elif self.is_paused('Hand'):
            self.output['status'] = 'HAND PAUSED'

        # set the mapped class into either a hand or arm motion
        pause_hand = self.is_paused('Hand') or self.is_paused('All')
        if class_info['IsGrasp'] and not pause_hand:
            # the motion class is either a grasp type or hand open
            if class_info['GraspId'] is not None and self.Plant.grasp_position < 0.2:
                # change the grasp state if still early in the grasp motion
                self.Plant.grasp_id = class_info['GraspId']
            self.Plant.set_grasp_velocity(class_info['Direction'] * self.hand_gain_value)

        pause_arm = self.is_paused('Arm') or self.is_paused('All')
        if not class_info['IsGrasp'] and not pause_arm:
            # the motion class is an arm movement
            self.Plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * self.gain_value)

        self.Plant.update()

        # transmit output
        if self.DataSink is not None:
            self.DataSink.send_joint_angles(self.Plant.joint_position,self.Plant.joint_velocity)

        return self.output

    def close(self):
        # Close input and output objects
        for s in self.SignalSource:
            s.close()
        if self.DataSink is not None:
            self.DataSink.close()


class MplScenario(Scenario):
    """
    Created on Tue Jan 23 10:17:58 2016

    Initial pass at simulating MiniVIE processing using python so that this runs on an embedded device

    @author: R. Armiger
    """

    from scenarios import Scenario

    def setup(self):
        """
        Create the building blocks of the MiniVIE

            SignalSource - source of EMG data
            SignalClassifier - algorithm to classify emg into 'intent'
            Plant - Perform forward integration and apply joint limits
            DataSink - output destination of command signals (e.g. real or virtual arm)
        """
        from inputs import myo
        import pattern_rec as pr
        from mpl.unity import UnityUdp
        from mpl.open_nfu import NfuUdp
        from controls.plant import Plant
        from scenarios import Scenario

        # attach inputs
        self.attach_source([myo.MyoUdp(source='//0.0.0.0:15001'), myo.MyoUdp(source='//0.0.0.0:15002')])
        # self.attach_source([myo.MyoUdp(source='//0.0.0.0:15001')])

        # Training Data holds data labels
        # training data manager
        self.TrainingData = pr.TrainingData()
        self.TrainingData.load()
        self.TrainingData.num_channels = self.num_channels

        # Setup feature extract and properties
        self.FeatureExtract = pr.FeatureExtract()
        self.FeatureExtract.zc_thresh = get_user_config_var('FeatureExtract.zcThreshold', 0.05)
        self.FeatureExtract.ssc_thresh = get_user_config_var('FeatureExtract.sscThreshold', 0.05)
        self.FeatureExtract.sample_rate = 200

        # Classifier parameters
        self.SignalClassifier = pr.Classifier(self.TrainingData)
        self.SignalClassifier.fit()

        # Plant maintains current limb state (positions) during velocity control
        filename = get_user_config_var('rocTable', '../../WrRocDefaults.xml')
        dt = get_user_config_var('timestep', 0.02)
        self.Plant = Plant(dt, filename)

        # Sink is output to outside world (in this case to VIE)
        # For MPL, this might be: real MPL/NFU, Virtual Arm, etc.
        data_sink = get_user_config_var('DataSink', 'Unity')
        if data_sink == 'Unity':
            sink = UnityUdp()
            sink.udp['RemoteHostname'] = "127.0.0.1"
            sink.udp['RemotePort'] = 25000
            sink.udp['LocalHostname'] = "0.0.0.0"
            sink.udp['LocalPort'] = 25001
            sink.connect()
        elif data_sink == 'NfuUdp':
            sink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
            sink.connect()
        else:
            import sys
            # unrecoverable
            logging.critical('Unmatched Data Sink from user_config: {}. Program Halted.'.format(data_sink))
            self.close()
            sys.exit(1)

        # synchronize the data sink with the plant model
        if get_user_config_var('mpl_connection_check', 1):
            sink.wait_for_connection()
        # Synchronize joint positions
        if sink.position['last_percept'] is not None:
            for i in range(0, len(self.Plant.joint_position)):
                self.Plant.joint_position[i] = sink.position['last_percept'][i]
        self.DataSink = sink

    def run(self):
        """
            Main function that involves setting up devices,
            looping at a fixed time interval, and performing cleanup
        """
        import sys
        import time

        # setup main loop control
        print("")
        print("Running...")
        print("")
        sys.stdout.flush()

        # ##########################
        # Run the control loop
        # ##########################
        time_elapsed = 0.0
        dt = self.Plant.dt
        print(dt)
        while True:
            try:
                # Fixed rate loop.  get start time, run model, get end time; delay for duration
                time_begin = time.time()

                # Run the actual model
                output = self.update()

                # send gui updates
                if self.TrainingInterface is not None:
                    msg = '<br>' + self.DataSink.get_status_msg()  # Limb Status
                    msg += ' ' + output['status']  # Classifier Status
                    for src in self.SignalSource:
                        msg += '<br>MYO:' + src.get_status_msg()
                    msg += '<br>' + time.strftime("%c")

                    # Forward status message (voltage, temp, etc) to mobile app
                    self.TrainingInterface.send_message("strStatus", msg)
                    # Send classifier output to mobile app (e.g. Elbow Flexion)
                    self.TrainingInterface.send_message("strOutputMotion", output['decision'])
                    # Send motion training status to mobile app (e.g. No Movement [70]
                    msg = '{} [{:.0f}]'.format(self.training_motion,
                                               round(self.TrainingData.get_totals(self.training_id), -1))
                    self.TrainingInterface.send_message("strTrainingMotion", msg)

                time_end = time.time()
                time_elapsed = time_end - time_begin
                if dt > time_elapsed:
                    time.sleep(dt - time_elapsed)
                else:
                    # print("Timing Overload: {}".format(time_elapsed))
                    pass

                # print('{0} dt={1:6.3f}'.format(output['decision'],time_elapsed))

            except KeyboardInterrupt:
                break

        print("")
        print("Last time_elapsed was: ", time_elapsed)
        print("")
        print("Cleaning up...")
        print("")

        self.close()


def test_scenarios():
    print('Testing Scenario File')
    import os

    if os.path.split(os.getcwd())[1] == 'scenarios':
        import sys
        sys.path.insert(0, os.path.abspath('..'))
        os.chdir('..')  # change directory so xml files can be found as expected

    print('Working Directory is {}'.format(os.getcwd()))
    a = MplScenario()
    a.setup()
    # Expected to be valid:
    a.command_string('Cls:Index Grasp')
    # Expected to log an error:
    a.command_string('Cls:Error Grasp')
    a.close()

    pass


if __name__ == '__main__':
    test_scenarios()
