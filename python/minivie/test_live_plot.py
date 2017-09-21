import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from inputs import myo

# Simple plot function for showing the EMG stream

# Setup Data Source
m = myo.MyoUdp(source='//127.0.0.1:10001', num_samples=600)
m.connect()

style.use('dark_background')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
fig.canvas.set_window_title('EMG Preview')

def animate(i):
    d = m.get_data() / 128  # *1 for a shallow copy

    for iChannel in range(0, 8):
        d[:, iChannel] = d[::-1, iChannel] + (1 * (iChannel + 1) )

    ax1.clear()
    ax1.plot(d)
    plt.ylim((0, 9))
    plt.xlabel('Samples')
    plt.ylabel('Channel')
    plt.title('EMG Stream')
    # print('{:0.2f}'.format(m.get_data_rate_emg()))


ani = animation.FuncAnimation(fig, animate, interval=50)
plt.show()
