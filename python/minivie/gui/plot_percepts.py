# Simple plot function for showing the Percept stream
# Requires matplotlib
#
# To run from command line:
# > python -m gui.plot_percepts.py
#
# Test function can also be 'double-clicked' to start

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from mpl import open_nfu
from mpl import JointEnum as MplId


num_samples = 50


class DataBuffer(object):
    def __init__(self):
        self.data_buffer = np.zeros((num_samples, 27))
    def add_data(self, d):
        self.data_buffer = np.roll(self.data_buffer, 1, axis=0)
        self.data_buffer[:1][:] = d


# Setup Data Source
m = open_nfu.NfuUdp()
m.connect()
m.wait_for_connection()

buff = DataBuffer()

style.use('dark_background')
fig, ax = plt.subplots(figsize=(15, 8))
ax.set_title('Percept Preview')
# lines = ax.plot(buff.data_buffer)
lines = [None] * MplId.NUM_JOINTS
for i in range(0, MplId.NUM_JOINTS):
    lines[i] = ax.plot([0.0]*num_samples, lw=2, label=MplId(i).name)[0]
leg = ax.legend(loc='upper left', fancybox=True, shadow=True)
leg.get_frame().set_alpha(0.4)

lined = dict()
for legline, origline in zip(leg.get_lines(), lines):
    legline.set_picker(5)  # 5 pts tolerance
    lined[legline] = origline
    vis = 0
    origline.set_visible(vis)
    # Change the alpha on the line in the legend so we can see what lines
    # have been toggled
    if vis:
        legline.set_alpha(1.0)
    else:
        legline.set_alpha(0.2)

def onpick(event):
    print('got event')
    # on the pick event, find the orig line corresponding to the
    # legend proxy line, and toggle the visibility
    legline = event.artist
    origline = lined[legline]
    vis = not origline.get_visible()
    origline.set_visible(vis)
    # Change the alpha on the line in the legend so we can see what lines
    # have been toggled
    if vis:
        legline.set_alpha(1.0)
    else:
        legline.set_alpha(0.2)
    # fig.canvas.draw()


def animate(i):
    p = m.get_percepts()
    buff.add_data(p['jointPercepts']['torque'])
    d = buff.data_buffer * 1
    for iChannel in range(0, 27):
        offset = (1 * (iChannel + 1) )
        offset = 0
        d[:, iChannel] = d[::-1, iChannel] + offset
        lines[iChannel].set_data(range(0, num_samples), d[:, iChannel])


plt.ylim((-7, 7))
plt.xlabel('Samples')
plt.ylabel('Channel')
plt.title('Percepts - Click Legend to Enable')

fig.canvas.mpl_connect('pick_event', onpick)
ani = animation.FuncAnimation(fig, animate, interval=20)
plt.show()
