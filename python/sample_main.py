# Initial pass and simulating MiniVIE processing using python so that this runs on an embedded device
#
# Created 1/23/2016 Armiger



import pygame
import math
import socket
import time
import binascii
import struct
   
VERBOSE = 1;
   
class Plant(object):

    def __init__(self):
        NUM_JOINTS = 27;
        self.position = [0.0]*NUM_JOINTS
        self.velocity = [0.0]*NUM_JOINTS
        self.limit = [45.0 * math.pi / 180.0]*NUM_JOINTS

        self.velocity[2] = 30.0 * math.pi / 180.0

    def update(self,dt):
        
        for i,item in enumerate(self.position):  
            self.position[i] = self.position[i] + self.velocity[i]*dt/1000;
        
            if abs(self.position[i]) > self.limit[i] :
                self.velocity[i] = -self.velocity[i]
                self.position[i] = math.copysign(self.limit[i],self.position[i])

class UnityUdp(object):
    def __init__(self, UDP_IP = "127.0.0.1", UDP_PORT = 25000):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        
        print("UnityUdp target IP:", self.UDP_IP)
        print("UnityUdp target port:", self.UDP_PORT)

        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
                             
    def sendJointAngles(self,values):
        
        # Send data
        packer = struct.Struct('27f')
        packed_data = packer.pack(*values)
        if VERBOSE > 1:
            print('Sending "%s"' % binascii.hexlify(packed_data), values)
        self.sock.sendto(packed_data, (self.UDP_IP, self.UDP_PORT))
    
    def close(self):
        self.sock.close()
        print("Closing Socket")


import numpy

# from http://www.lfd.uci.edu/~gohlke/code/transformations.py.html

def euler_from_matrix(matrix, axes='sxyz'):
    """Return Euler angles from rotation matrix for specified axis sequence.

    axes : One of 24 axis sequences as string or encoded tuple

    Note that many Euler angle triplets can describe one matrix.

    >>> R0 = euler_matrix(1, 2, 3, 'syxz')
    >>> al, be, ga = euler_from_matrix(R0, 'syxz')
    >>> R1 = euler_matrix(al, be, ga, 'syxz')
    >>> numpy.allclose(R0, R1)
    True
    >>> angles = (4*math.pi) * (numpy.random.random(3) - 0.5)
    >>> for axes in _AXES2TUPLE.keys():
    ...    R0 = euler_matrix(axes=axes, *angles)
    ...    R1 = euler_matrix(axes=axes, *euler_from_matrix(R0, axes))
    ...    if not numpy.allclose(R0, R1): print(axes, "failed")

    """
    try:
        firstaxis, parity, repetition, frame = _AXES2TUPLE[axes.lower()]
    except (AttributeError, KeyError):
        _TUPLE2AXES[axes]  # validation
        firstaxis, parity, repetition, frame = axes

    i = firstaxis
    j = _NEXT_AXIS[i+parity]
    k = _NEXT_AXIS[i-parity+1]

    M = numpy.array(matrix, dtype=numpy.float64, copy=False)[:3, :3]
    if repetition:
        sy = math.sqrt(M[i, j]*M[i, j] + M[i, k]*M[i, k])
        if sy > _EPS:
            ax = math.atan2( M[i, j],  M[i, k])
            ay = math.atan2( sy,       M[i, i])
            az = math.atan2( M[j, i], -M[k, i])
        else:
            ax = math.atan2(-M[j, k],  M[j, j])
            ay = math.atan2( sy,       M[i, i])
            az = 0.0
    else:
        cy = math.sqrt(M[i, i]*M[i, i] + M[j, i]*M[j, i])
        if cy > _EPS:
            ax = math.atan2( M[k, j],  M[k, k])
            ay = math.atan2(-M[k, i],  cy)
            az = math.atan2( M[j, i],  M[i, i])
        else:
            ax = math.atan2(-M[j, k],  M[j, j])
            ay = math.atan2(-M[k, i],  cy)
            az = 0.0

    if parity:
        ax, ay, az = -ax, -ay, -az
    if frame:
        ax, az = az, ax
    return ax, ay, az


def quaternion_matrix(quaternion):
    """Return homogeneous rotation matrix from quaternion.

    >>> M = quaternion_matrix([0.99810947, 0.06146124, 0, 0])
    >>> numpy.allclose(M, rotation_matrix(0.123, [1, 0, 0]))
    True
    >>> M = quaternion_matrix([1, 0, 0, 0])
    >>> numpy.allclose(M, numpy.identity(4))
    True
    >>> M = quaternion_matrix([0, 1, 0, 0])
    >>> numpy.allclose(M, numpy.diag([1, -1, -1, 1]))
    True

    """
    q = numpy.array(quaternion, dtype=numpy.float64, copy=True)
    n = numpy.dot(q, q)
    if n < _EPS:
        return numpy.identity(4)
    q *= math.sqrt(2.0 / n)
    q = numpy.outer(q, q)
    return numpy.array([
        [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
        [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
        [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
        [                0.0,                 0.0,                 0.0, 1.0]])

# epsilon for testing whether a number is close to zero
_EPS = numpy.finfo(float).eps * 4.0

# axis sequences for Euler angles
_NEXT_AXIS = [1, 2, 0, 1]

# map axes strings to/from tuples of inner axis, parity, repetition, frame
_AXES2TUPLE = {
    'sxyz': (0, 0, 0, 0), 'sxyx': (0, 0, 1, 0), 'sxzy': (0, 1, 0, 0),
    'sxzx': (0, 1, 1, 0), 'syzx': (1, 0, 0, 0), 'syzy': (1, 0, 1, 0),
    'syxz': (1, 1, 0, 0), 'syxy': (1, 1, 1, 0), 'szxy': (2, 0, 0, 0),
    'szxz': (2, 0, 1, 0), 'szyx': (2, 1, 0, 0), 'szyz': (2, 1, 1, 0),
    'rzyx': (0, 0, 0, 1), 'rxyx': (0, 0, 1, 1), 'ryzx': (0, 1, 0, 1),
    'rxzx': (0, 1, 1, 1), 'rxzy': (1, 0, 0, 1), 'ryzy': (1, 0, 1, 1),
    'rzxy': (1, 1, 0, 1), 'ryxy': (1, 1, 1, 1), 'ryxz': (2, 0, 0, 1),
    'rzxz': (2, 0, 1, 1), 'rxyz': (2, 1, 0, 1), 'rzyz': (2, 1, 1, 1)}

_TUPLE2AXES = dict((v, k) for k, v in _AXES2TUPLE.items())

class MyoUdp(object):
    def __init__(self, UDP_IP = "127.0.0.1", UDP_PORT = 10001):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        
        print("MyoUdp target IP:", self.UDP_IP)
        print("MyoUdp target port:", self.UDP_PORT)
        
        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP

        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)

        self.emg_buffer = numpy.zeros((100,8))
    def getData(self):
        data =''
        address = ''
        try:
            data,address = self.sock.recvfrom(1024)
            output = struct.unpack("8b4f3f3f",data);
            self.emg_buffer[:1,:] = output[0:8]
            self.emg_buffer = numpy.roll(self.emg_buffer,1, axis=0)
            self.quat = output[8:12]
            print(euler_from_matrix(quaternion_matrix(self.quat)))            
            
            
            self.accel = output[12:14]
            self.gyro = output[15:17]
        except socket.error:
            pass
        

    def close(self):
        self.sock.close()
        print("Closing Socket")


# Create data objects    
myPlant = Plant()
hSink = UnityUdp()
hMyo = MyoUdp()

try: 
    # setup main loop control
    time_elapsed_since_last_action = 0
    clock = pygame.time.Clock()
    while True: # main loop
    
        # the following method returns the time since its last call in milliseconds
        # it is good practice to store it in a variable called 'dt'
        dt = clock.tick() 
    
        data = hMyo.getData()
        myPlant.update(dt)
        
        # Simulate a slow process
        if 0:        
            time.sleep(0.001)
        
        time_elapsed_since_last_action += dt
        # dt is measured in milliseconds, therefore 20 ms = 0.02 seconds = 50Hz
        if time_elapsed_since_last_action >= 20:
            print(myPlant.position[2])
            vals = euler_from_matrix(quaternion_matrix(hMyo.quat))
            myPlant.position[3] = vals[1] + math.pi/2
            time_elapsed_since_last_action = 0 # reset it to 0 so you can count again
            hSink.sendJointAngles(myPlant.position)
            
finally:
    print(hMyo.emg_buffer)
    hSink.close()
    hMyo.close()
