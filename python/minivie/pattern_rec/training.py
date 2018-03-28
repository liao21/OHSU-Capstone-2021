# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 18:03:38 2016

This class is designed to receive training commands. Training commands can be found in scenarios/init

@author: R. Armiger
"""

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
from pattern_rec.training_interface import TrainingInterface
import logging
from utilities.user_config import get_user_config_var


class TrainingUdp(object):
    VERBOSE = 0
    """ Class for receiving Training Commands data via UDP"""

    def __init__(self, ip="127.0.0.1", port=3003):
        import threading
        import socket

        self.UDP_IP = ip
        self.UDP_PORT = port
        print("TrainingUdp target IP:", self.UDP_IP)
        print("TrainingUdp target port:", self.UDP_PORT)

        # Default training values
        self.class_id = -1
        self.class_name = ""

        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP
        self.sock.bind((ip, port))
        self.sock.settimeout(3.0)

        self.lock = threading.Lock()

        # Create a thread for processing new data
        # Create two threads as follows
        self.thread = threading.Thread(target=self.recv)
        self.thread.start()

    def recv(self):
        import socket
        """ Receive Incoming Commands """

        # Loop forever to recv data
        while True:
            # Blocking call until data received
            try:
                # recv call will error if socket closed on exit
                data, address = self.sock.recvfrom(1024)
            except socket.error as e:
                print("Socket read error. Socket Closed?")
                print(e)
                return

            msg_id = data[0]
            if msg_id == 10:
                # Make thread safe
                with self.lock:
                    msg_len = data[1]
                    self.class_id = data[2]
                    self.class_name = data[3:msg_len].decode("utf-8")
            else:
                print("Unknown Msg ID")

    def close(self):
        """ Cleanup socket """
        print("Closing TrainingUdp Socket IP={} Port={}".format(self.UDP_IP, self.UDP_PORT))
        self.sock.close()
        self.thread.join()


#https://stackoverflow.com/questions/12479054/how-to-run-functions-outside-websocket-loop-in-python-tornado
wss = []  # list of websockets send commands
func_handle = []  # list of callbacks for message recv

# store the last messages so we don't re-transmit a lot of repeated data
message_history = {'strStatus': '', 'strOutputMotion': '', 'strTrainingMotion': '', 'strMotionTester': '',
                 'strTAC': '', 'strMotionTesterProgress': '', 'strMotionTesterImage': '',
                 'strTACJoint1Bar': '', 'strTACJoint1Target': '', 'strTACJoint1Error': '',
                 'strTACJoint1Name': '',
                 'strTACJoint2Bar': '', 'strTACJoint2Target': '', 'strTACJoint2Error': '',
                 'strTACJoint2Name': '',
                 'strTACJoint3Bar': '', 'strTACJoint3Target': '', 'strTACJoint3Error': '',
                 'strTACJoint3Name': '',
                 'jointCmd': '', 'jointPos': '', 'jointTorque': '', 'jointTemp': '',
                 }


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        logging.debug('Connection opened...')
        if self not in wss:
            wss.append(self)

    def on_message(self, message):
        logging.debug('Received:', message)
        for func in func_handle:
            func(message)

    def on_close(self):
        logging.debug('Connection closed...')
        if self in wss:
            wss.remove(self)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        homepage = get_user_config_var('mobile_app_homepage', "../www/mplHome/index.html")
        loader = tornado.template.Loader(".")
        self.write(loader.load(homepage).generate())


class TrainingManagerWebsocket(TrainingInterface):
    """
    This Training manager uses websockets provided through tornado

    """

    def __init__(self):
        import threading

        # Initialize superclass
        super(TrainingInterface, self).__init__()

        homepath = get_user_config_var('mobile_app_path',"../www/mplHome")

        # handle to websocket interface
        self.application = tornado.web.Application([
            (r'/ws', WSHandler),
            (r'/', MainHandler),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": homepath}),
        ])

        # store the last messages so we don't re-transmit a lot of repeated data
        self.last_msg = message_history

        # keep count of skipped messages so we can send at some nominal rate
        self.msg_skip_count = 0

        self.thread = threading.Thread(target=tornado.ioloop.IOLoop.instance().start, name='WebThread')

    def setup(self, port=9090):

        self.application.listen(port)
        self.thread.start()

    def add_message_handler(self, func):
        # attach a function to receive commands from websocket

        if func not in func_handle:
            func_handle.append(func)

    def send_message(self, msg_id, msg):
        # send message but only when the string changes (or timeout occurs)

        if not self.last_msg[msg_id] == msg:
            self.last_msg[msg_id] = msg
            try:
                logging.debug(msg_id + ':' + msg)
                for ws in wss:
                    ws.write_message(msg_id + ':' + msg)

            except Exception as e:
                logging.error(e)

            return
        else:
            self.msg_skip_count += 1

        # add a timeout so that we get 'some' messages as a nominal rate
        if self.msg_skip_count > 500:

            # re-send all messages
            for key, val in self.last_msg.items():
                try:
                    logging.debug(key + ':' + val)
                    for ws in wss:
                        ws.write_message(key + ':' + val)
                except Exception as e:
                    logging.error(e)

            # reset counter
            self.msg_skip_count = 0

    def close(self):
        pass


class TrainingManagerSpacebrew(TrainingInterface):
    """
    This Training manager uses websockets provided through the spacebrew interface to manager training commands

    """

    def __init__(self):

        # Initialize superclass
        super(TrainingInterface, self).__init__()

        # handle to spacebrew websocket interface
        self.brew = None

        # store the last messages so we don't re-transmit a lot of repeated data
        self.last_msg = message_history

        # keep count of skipped messages so we can send at some nominal rate
        self.msg_skip_count = 0

    def setup(self, description="JHU/APL Embedded Controller", server="192.168.1.1", port=9000):
        from pySpacebrew.spacebrew import Spacebrew

        # setup web interface
        self.brew = Spacebrew("MPL Embedded", description, server, port)
        self.brew.addSubscriber("cmdString", "string")
        self.brew.addPublisher("statusString", "string")
        self.brew.start()

    def add_message_handler(self, func):
        # attach a function to receive commands from websocket
        self.brew.subscribe("cmdString", func)

    def send_message(self, msg_id, msg):
        # send message but only when the string changes (or timeout occurs)

        if not self.last_msg[msg_id] == msg:
            self.last_msg[msg_id] = msg
            try:
                self.brew.publish('statusString', msg_id + ':' + msg)
            except Exception as e:
                print(e)

            return
        else:
            self.msg_skip_count += 1

        # add a timeout so that we get 'some' messages as a nominal rate

        if self.msg_skip_count > 300:

            # re-send all messages
            for key, val in self.last_msg.items():
                try:
                    self.brew.publish('statusString', key + ':' + val)
                except Exception as e:
                    print(e)

            # reset counter
            self.msg_skip_count = 0

    def close(self):
        self.brew.stop()
