from inputs import myo
from gui import signal_viewer
import threading
import cProfile
import pstats


def start_test():
    # Start myo udp stream
    #thread = threading.Thread(target=myo.emulate_myo_udp_exe(destination='//127.0.0.1:10001'))
    #thread.start()

    # Read myo udp stream
    source = myo.MyoUdp(source='//127.0.0.1:15001')
    source.connect()

    # Start signal viewer
    signal_viewer.SignalViewer(signal_source=source)

# Run profiler
f_name = 'signal_viewer_profile'
#sort_mode = 'cumulative'
sort_mode = 'time'

cProfile.run('start_test()', f_name)
p = pstats.Stats(f_name)
p.strip_dirs().sort_stats(sort_mode).print_stats(20)

# Can also run "snakeviz signal_viewer_profile" from terminal
