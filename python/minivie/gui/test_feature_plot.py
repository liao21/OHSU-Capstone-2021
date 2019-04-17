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
import numpy as np

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs import myo
import pattern_rec
from pattern_rec import features_selected
from pattern_rec import features

# Setup Data Source
m = myo.MyoUdp(source='//127.0.0.1:15001', num_samples=50)
m.connect()

# data_buffer = [(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.0)] * 100
data_buffer = np.ones((100, 8))
iVal = 0

style.use('dark_background')
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
fig.canvas.set_window_title('EMG Preview')

FeatureExtract = pattern_rec.FeatureExtract()
select_features = features_selected.FeaturesSelected(FeatureExtract)
# select_features.create_instance_list()

# FeatureExtract.attach_feature(features.Mav())
FeatureExtract.attach_feature(features.CurveLen())
# FeatureExtract.attach_feature(features.Zc(zc_thresh=0.02))
# FeatureExtract.attach_feature(features.Ssc())
# FeatureExtract.attach_feature(features.Wamp())
# FeatureExtract.attach_feature(features.Var())
# FeatureExtract.attach_feature(features.Vorder())
# FeatureExtract.attach_feature(features.LogDetect())
# FeatureExtract.attach_feature(features.EmgHist())
# FeatureExtract.attach_feature(features.AR())
# FeatureExtract.attach_feature(features.Ceps())


def animate(i):
    f2, f, imu, rot_mat = FeatureExtract.get_features([m])

    for iChannel in range(0, m.num_channels):
        feature = f2[iChannel] * 0.01
        data_buffer[i % 100, iChannel] = (feature + (1 * (iChannel + 1)))

    ax1.clear()
    ax1.plot(data_buffer)
    plt.ylim((0, m.num_channels+1))
    plt.xlabel('Samples')
    plt.ylabel('Channel')
    plt.title('EMG Stream')
    # print('{:0.2f}'.format(m.get_data_rate_emg()))


ani = animation.FuncAnimation(fig, animate, interval=1)
plt.show()
