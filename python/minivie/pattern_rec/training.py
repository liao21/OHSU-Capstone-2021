# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 18:03:38 2016

This class is designed to receive training commands. Training commands can be found in scenarios/init

@author: R. Armiger
"""


class TrainingManagerSpacebrew(object):
    """
    This Training manager uses websockets provided through the spacebrew interface to manager training commands

    """

    def __init__(self):
        
        # handle to spacebrew websocket interface
        self.brew = None
        
        # store the last messages so we don't re-transmit a lot of repreated data
        self.last_msg = {'strStatus': '', 'strTrainingMotion': '', 'strOutputMotion': ''}
        
        # keep count of skipped messages so we can send at some nominal rate
        self.msg_skip_count = 0

    def setup(self, description="JHU/APL Embedded Controller", server="192.168.1.1", port=9000):
        from pySpacebrew.spacebrew import Spacebrew

        # setup web interface
        self.brew = Spacebrew("MPL Embedded", description, server, port)
        self.brew.addSubscriber("strCommand", "string")
        self.brew.addPublisher("strStatus", "string")
        self.brew.addPublisher("strTrainingMotion", "string")
        self.brew.addPublisher("strOutputMotion", "string")
        self.brew.start()

    def add_message_handler(self, func):
        # attach a function to received commands from websocket
        self.brew.subscribe("strCommand", func)

    def send_message(self, msg_id, msg):
        # send message but only when the string changes (or timeout occurs)

        if not self.last_msg[msg_id] == msg:
            self.last_msg[msg_id] = msg
            self.brew.publish(msg_id, msg)
            return
        else:
            self.msg_skip_count +=1
            
        # add a timeout so that we get 'some' messages as a nominal rate
        
        if self.msg_skip_count > 100:
            
            # re-send all messages
            for key,val in self.last_msg.items():
                self.brew.publish(key, val)
                
            # reset counter
            self.msg_skip_count = 0
            
        

    def close(self):
        self.brew.stop()


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

        self.sock = socket.socket(socket.AF_INET,       # Internet
                                  socket.SOCK_DGRAM)    # UDP
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
