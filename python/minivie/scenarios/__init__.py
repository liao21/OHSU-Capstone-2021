class Scenario(object):
    """
    Define the building blocks of the MiniVIE

        SignalSource - source of EMG data
        SignalClassifier - algorithm to classify emg into 'intent'
        Plant - Perform forward integration and apply joint limits
        DataSink - output destination of command signals (e.g. real or virtual arm)
    """
    def __init__(self):
        self.SignalSource = None
        self.SignalClassifier = None
        self.FeatureExtract = None
        self.TrainingData = None
        self.TrainingInterface = None
        self.Plant = None
        self.DataSink = None

        self.add_data = False
        self.training_motion = 'No Movement'
        self.training_id = 0

        self.num_channels = 0

        self.output = None  # Will contain latest status message

        self.__pause = {'All': False, 'Arm': False, 'Hand': False}
        self.__gain_value = 1.0
        self.__hand_gain_value = 1.0

    def is_paused(self, scope='All'):
        # return the pause value for the given context ['All' 'Arm' 'Hand']
        return self.__pause[scope]

    def get_gain_value(self):
        return self.__gain_value

    def get_hand_gain_value(self):
        return self.__hand_gain_value

    def pause(self, scope='All', state=None):
        # Toggles pause state which suspends motion of arm
        #
        # State can be forced with optional value argument
        #
        # pause('All') Toggle
        # pause('All', True) Force PAUSE
        # pause('All', False) Force RESUME

        if state is not None:
            self.__pause[scope] = state
            return

        if self.__pause[scope]:
            self.__pause[scope] = False
        else:
            self.__pause[scope] = True

    def gain(self, factor):
        self.__gain_value *= factor
        if self.__gain_value < 0.1:
            self.__gain_value = 0.1

    def hand_gain(self, factor):
        self.__hand_gain_value *= factor
        if self.__hand_gain_value < 0.1:
            self.__hand_gain_value = 0.1

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

        TODO: add classifier options to train and switch between LDA, QDA, SVM, etc
        TODO: add majority voting
        TODO: add reset to hand/arm speed
        """

        import logging
        from utilities import shutdown, reboot, restart_myo

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
            self.training_motion = cmd_data
            self.training_id = self.TrainingData.motion_names.index(cmd_data)
            self.add_data = False

        elif cmd_type == 'Cmd':
            print(cmd_data)
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
            elif cmd_data == 'Pause':
                self.pause('All')
            elif cmd_data == 'PauseHand':
                self.pause('Hand')
            elif cmd_data == 'PauseAllOn':
                self.pause('All', True)
            elif cmd_data == 'PauseAllOff':
                self.pause('All', False)
            elif cmd_data == 'PauseHandOn':
                self.pause('Hand', True)
            elif cmd_data == 'PauseHandOff':
                self.pause('Hand', False)
            elif cmd_data == 'RestartMyo1':
                restart_myo(1)
            elif cmd_data == 'RestartMyo2':
                restart_myo(2)
            elif cmd_data == 'Reboot':
                reboot()
            elif cmd_data == 'Shutdown':
                shutdown()
            elif cmd_data == 'SpeedUp':
                self.gain(1.2)
            elif cmd_data == 'SpeedDown':
                self.gain(0.8)
            elif cmd_data == 'HandSpeedUp':
                self.hand_gain(1.2)
            elif cmd_data == 'HandSpeedDown':
                self.hand_gain(0.8)
            else:
                logging.info('Unknown scenario command: ' + cmd_data)

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

        # initialize output
        self.output = {'status': 'RUNNING', 'features': None, 'decision': 'None', 'vote': None}

        # get data / features
        self.output['features'], f = self.FeatureExtract.get_features(self.SignalSource)

        # if simultaneously training the system, add the current results to the data buffer
        if self.add_data:
            self.TrainingData.add_data(self.output['features'], self.training_id, self.training_motion)

        # classify
        decision_id, self.output['status'] = self.SignalClassifier.predict(f)
        if decision_id is None:
            return self.output

        # TODO: add majority vote

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
            if class_info['GraspId'] is not None and self.Plant.GraspPosition < 0.2:
                # change the grasp state if still early in the grasp motion
                self.Plant.GraspId = class_info['GraspId']
            self.Plant.set_grasp_velocity(class_info['Direction'] * self.__hand_gain_value)

        pause_arm = self.is_paused('Arm') or self.is_paused('All')
        if not class_info['IsGrasp'] and not pause_arm:
            # the motion class is an arm movement
            self.Plant.set_joint_velocity(class_info['JointId'], class_info['Direction'] * self.__gain_value)

        self.Plant.update()

        # transmit output
        if self.DataSink is not None:
            self.DataSink.send_joint_angles(self.Plant.JointPosition)

        return self.output

    def close(self):
        # Close input and output objects
        for s in self.SignalSource:
            s.close()
        if self.DataSink is not None:
            self.DataSink.close()
