# Simple plot function for showing the EMG stream
# Requires matplotlib
#
# To run from command line:
# > python -m gui.test_live_plot.py
#
# Test function can also be 'double-clicked' to start

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs import myo


# Setup Data Source
m = myo.MyoUdp(source='//0.0.0.0:15001', num_samples=600)
m.connect()

style.use('dark_background')
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
fig.canvas.set_window_title('EMG Preview')


def animate(_):
    d = m.get_data() * 0.01  # *1 for a shallow copy

    for iChannel in range(0, 8):
        d[:, iChannel] = d[::-1, iChannel] + (1 * (iChannel + 1))

    ax1.clear()
    ax1.plot(d)
    plt.ylim((0, 9))
    plt.xlabel('Samples')
    plt.ylabel('Channel')
    plt.title('EMG Stream')
    # print('{:0.2f}'.format(m.get_data_rate_emg()))


ani = animation.FuncAnimation(fig, animate, interval=150)
plt.show()
