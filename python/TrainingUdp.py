# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 18:03:38 2016

@author: R. Armiger
"""

import threading
import socket
VERBOSE = 0

class TrainingUdp(object):
    """ Class for receiving Training Commands data via UDP"""
    def __init__(self, UDP_IP="127.0.0.1", UDP_PORT=3003):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        print("TrainingUdp target IP:", self.UDP_IP)
        print("TrainingUdp target port:", self.UDP_PORT)

        # Default kinematic values
        self.class_id = -1
        self.class_name = ""

        self.sock = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM)   # UDP
        self.sock.bind((UDP_IP, UDP_PORT))

        # Create a thread for processing new data
        # Create two threads as follows
        self.thread = threading.Thread(target=self.recv)
        self.thread.start()

    def recv(self):
        """ Receive Incoming Commands """

        # Loop forever to recv data
        while True:
            # Blocking call until data received
            data, address = self.sock.recvfrom(1024)
            
            msg_id = data[0]
            if msg_id == 10:
                msg_len = data[1]
                self.class_id = data[2]
                self.class_name = data[3:msg_len].decode("utf-8") 
            else:
                print("Unknown Msg ID")
                
    def close(self):
        """ Cleanup socket """
        self.sock.close()
        print("Closing Socket")
