import struct
import numpy as np
import socket
from inputs import myo
import time
import binascii

m1 = myo.MyoUdp(source='//127.0.0.1:15001')
m1.connect()

m2 = myo.MyoUdp(source='//127.0.0.1:15002')
m2.connect()


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.bind(('127.0.0.1', 5005))



while True:
    try:
        time.sleep(0.02)
        
        ang1 = m1.get_angles() 
        c1 = ang1[1] * 180.0 / 3.14159

        ang2 = m2.get_angles() 
        c2 = ang2[1] * 180.0 / 3.14159

        #print(c1)


        # get difference between two channels
        mav = np.mean(np.abs(m1.get_data()), axis=0)
        #print(mav)
        cmd1 = mav[6] - mav[3]


        mav = np.mean(np.abs(m2.get_data()), axis=0)
        #print(mav)
        cmd2 = mav[5] - mav[1]
        #print(cmd2)
        

        # set lower threshold
        if abs(cmd1) < 10: cmd1 = 0
        if abs(cmd2) < 10: cmd2 = 0
        
        # limit range
        cmd1 = np.clip(round(c1*500), -32768, 32767)
        cmd2 = np.clip(round(c2*500), -32768, 32767)
        
        print((cmd1, cmd2))
        
        # format output packet
        payload = np.append(cmd1,cmd2)        
        packer = struct.Struct('2h')
        msg = bytearray([1,0,2])
        msg.extend(packer.pack(*payload))
        
        #print(binascii.hexlify(msg))
        sock.sendto(msg, ('127.0.0.1',5005))
        
    except KeyboardInterrupt:
        break

m1.close()
m2.close()
sock.close()


