import nidaqmx
import time
import socket
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5432))
sock.settimeout(3.0)

start_time = time.time()
with nidaqmx.Task() as task:
     task.ai_channels.add_ai_voltage_chan("Dev1/ai0", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai1", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai2", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai3", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai4", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai5", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai6", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     task.ai_channels.add_ai_voltage_chan("Dev1/ai7", terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
     for i in range(0, 20000):
        a = task.read(number_of_samples_per_channel=1)

        packed_data = bytes()
        floatList = a
        packed_data = packed_data.join((struct.pack('f', val[0]) for val in floatList))

        #packer = struct.Struct('8f')
        #packed_data = packer.pack(*a)

        sock.sendto( packed_data , ('localhost', 15001) )
        #print(a)
        time.sleep(0.001)
sock.close()

elapsed_time = time.time() - start_time
print('Time: {0:0.2f} s'.format(elapsed_time))

print('Press any key to continue...')
input()

