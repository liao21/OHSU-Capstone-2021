# Simple plot function for showing the EMG stream
# Requires matplotlib
#
# To run from command line:
# > python -m gui.test_live_plot.py
#
# Test function can also be 'double-clicked' to start

import asyncio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs import emg_device_client


print('Running')
a = emg_device_client.CtrlSocket(source='ws://localhost:5678', num_samples=125)

style.use('dark_background')
fig, ax = plt.subplots()
lines = ax.plot(a.get_data())

fig.canvas.set_window_title('EMG Preview')
plt.pause(0.1)
plt.ylim((-10, 100))
plt.xlabel('Samples')
plt.ylabel('Channel')
plt.title('EMG Stream')

offset = 5

# try https://bastibe.de/2013-05-30-speeding-up-matplotlib.html
async def animate():
    while True:
        d = a.get_data()
        for i in range(0, a.num_channels):
            f = (d[:, i] - 2047) * 0.01 + offset*i
            lines[i].set_ydata(f)
        fig.canvas.draw()
        fig.canvas.flush_events()

        await asyncio.sleep(0.01)


loop = asyncio.get_event_loop()
loop.create_task(animate())
loop.run_until_complete(a.connect())
loop.run_forever()
