import nidaqmx
import time
import socket
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5432))
sock.settimeout(3.0)

start_time = time.time()
with nidaqmx.Task() as task:
     task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
     for i in range(0,200):
        a = task.read(number_of_samples_per_channel=100)
        packer = struct.Struct('100f')
        packed_data = packer.pack(*a)
        sock.sendto( packed_data , ('localhost', 5454) )
        #print(a)
        time.sleep(0.1)
sock.close()

elapsed_time = time.time() - start_time
print('Time: {0:0.2f} s'.format(elapsed_time))

print('Press any key to continue...')
input()

