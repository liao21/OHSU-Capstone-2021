#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple Oscilloscope-style plotting function for EMG Device

This module previews a data source using matplotlib.  The asyncio module is used to simultaneously get data from
the websocket source as well as update the plot

Example
-------
To run from command line:

    $ python3 -m gui.test_emg_device_plot.py

Under windows this function should be able to be 'double-clicked' using the path check below

Revisions
-------
2019JAN31 Armiger: Created

"""

import asyncio
import matplotlib.pyplot as plt
from matplotlib import style

# Check path to ensure that the module can be found on path relative to the 'minivie' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs import emg_device_client


a = emg_device_client.EmgSocket(source='ws://localhost:5678', num_samples=2000)

# setup plot area
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
