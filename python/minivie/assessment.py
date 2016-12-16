# take in a vie object and perform a control assessment


class MotionTester(object):
    def __init__(self, vie, trainer):
        self.vie = vie
        self.trainer = trainer
        self.thread = None

    def command_string(self, value):
        """
        Commands are strings with the following format:

        [CMD_TYPE]:[CMD_VALUE]

        [CMD_TYPE] options are:
            Cmd - Indicates the cmd_value is a command word. Options are:
                StartAssessment
        """
        import threading
        import logging

        logging.info('Received new motion tester command:' + value)
        parsed = value.split(':')
        if not len(parsed) == 2:
            logging.warning('Invalid motion tester command: ' + value)
            return
        else:
            cmd_type = parsed[0]
            cmd_data = parsed[1]

        if cmd_type == 'Cmd':
            if cmd_data == 'StartMotionTester':
                self.thread = threading.Thread(target=self.start_assessment)
                self.thread.name = 'MotionTester'
                self.thread.start()
            else:
                logging.info('Unknown motion tester command: ' + cmd_data)

    def start_assessment(self):
        import math
        import time
        from mpl import JointEnum as MplId

        # Determine which classes should be trained
        motion_names = self.vie.TrainingData.motion_names
        totals = self.vie.TrainingData.get_totals()

        trained_classes = [motion_names[i] for i, e in enumerate(totals) if e != 0]
        print(trained_classes)

        # pause limb during test
        self.vie.pause('All', True)
        print('Holdout')

        # TODO: Don't test No movement
        for i_rep in range(3):
            print('New Trial')

            for i_class in trained_classes:
                is_complete = self.assess_class(i_class)
                if is_complete:
                    print('Motion Completed!')
                else:
                    print('Motion Incomplete')

        self.vie.pause('All', False)

    def assess_class(self, class_name):
        import time
        import logging

        self.send_status('Testing Class: ' + class_name)

        dt = 0.1  # 100ms RIC JAMA
        timeout = 5
        time_begin = time.time()
        max_correct = 10
        move_complete = False
        num_correct = 0
        num_wrong = 0
        time_elapsed = 0.0

        while not move_complete and (time_elapsed < timeout):

            # get the class
            current_class = self.vie.output['decision']

            if current_class == class_name:
                num_correct += 1
                # send status to mobile trainer
                self.send_status('Testing Class: ' + class_name + ': ' + str(num_correct) + '/' + str(max_correct) + ' Correct Classifications, ')
            else:
                num_wrong += 1

            if num_correct >= max_correct:
                move_complete = True

            time.sleep(dt)
            time_elapsed = time.time() - time_begin

        self.send_status('Class Assessment: ' + class_name + ': ' + str(num_correct) + '/' + str(max_correct) + ' Correct Classifications, ' + str(num_wrong) + ' Misclassifications')

        return move_complete

    def send_status(self, status):
        import logging

        print(status)
        logging.info(status)
        self.trainer.send_message("mplString", 'strStatus:' + status)




class TargetAchievementControl(object):
    def __init__(self, vie, trainer):
        self.vie = vie
        self.trainer = trainer

    def command_string(self, value):
        """
        Commands are strings with the following format:

        [CMD_TYPE]:[CMD_VALUE]

        [CMD_TYPE] options are:
            Cmd - Indicates the cmd_value is a command word. Options are:
                StartAssessment
        """
        import logging
        import threading

        logging.info('Received new  TAC command:' + value)
        parsed = value.split(':')
        if not len(parsed) == 2:
            logging.warning('Invalid TAC command: ' + value)
            return
        else:
            cmd_type = parsed[0]
            cmd_data = parsed[1]

        if cmd_type == 'Cmd':
            if cmd_data == 'StartAssessment':
                self.thread = threading.Thread(target=self.start_assessment)
                self.thread.name = 'Assessement'
                self.thread.start()

    def start_assessment(self):
        import math
        import time
        from mpl import JointEnum as MplId

        timeout = 6.0 #seconds
        dt = 0.05 # seconds
        time_end = 0
        # start timer

        time_begin = time.time()
        self.vie.pause('All',True)
        print('Holdout')
        time.sleep(timeout)
        self.vie.pause('All',False)

        time_begin = time.time()
        while (time_end - time_begin) < timeout:

            arm = self.vie.Plant.JointPosition[MplId.ELBOW] * 180 / math.pi
            hand = self.vie.Plant.GraspPosition
            decision = self.vie.output['decision']
            print('Elbow: {0:6.2f}  Grasp: {1:6.2f} Class:{2}'.format(arm, hand, decision))

            time_end = time.time()
            time.sleep(dt)

        print('Done')


