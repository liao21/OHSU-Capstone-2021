# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 18:03:38 2016

This class is designed to receive training commands via udp. Training commands
consist of a message length, a class id, and a class name. This can be used to 
set the cues for which training action is active so that currently recorded data
can be labeled correctly

@author: R. Armiger
"""

import threading
import socket
VERBOSE = 0


class TrainingUdp(object):
    """ Class for receiving Training Commands data via UDP"""
    def __init__(self, ip="127.0.0.1", port=3003):
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

        self.lock = threading.Lock()
        
        # Create a thread for processing new data
        # Create two threads as follows
        self.thread = threading.Thread(target=self.recv)
        self.thread.start()

    def recv(self):
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
