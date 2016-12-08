# take in a vie object and perform a control assessment
class TargetAchievementControl(object):
    def __init__(self, vie):
        self.vie = vie

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

        logging.info('Received new command:' + value)
        parsed = value.split(':')
        if not len(parsed) == 2:
            logging.warning('Invalid Command: ' + value)
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


