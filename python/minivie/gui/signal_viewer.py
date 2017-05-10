#!/usr/bin/env python

import sys
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
# Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)


class SignalViewer(QtCore.QObject):
    """

    Class for viewing, filtering, and recording signals

    """

    def __init__(self, signal_source=None):
        # Constructor. If called with no arguments, user must assign signal source and initialize.

        # Initialize as QObject
        QtCore.QObject.__init__(self)

        # Properties controlling signal source viewed
        self._signal_source = None
        self._selected_channels = [True] * 16
        self._show_filtered_data = True
        self._mode_select = 'Time Domain'

        # Timer
        self._timer = None

        # GUI components
        self._qt_app = QtGui.QApplication(sys.argv)
        self._qt_main_widget = QTWindow(self)

        # Set signal source
        self.set_signal_source(signal_source)

        # Initialize
        self.initialize()

    def set_signal_source(self, signal_source):
        # Set method for signal source. Returns false if empty input.

        if signal_source:
            self._signal_source = signal_source
            return True
        else:
            return False

    def initialize(self):
        # Starts gui, assuming signal source has been set

        if not self._signal_source:
            print('No Signal Source Assigned. Use signal_viewer.set_signal_source().\n')
            return

        print('Initializing Signal Viewer.\n')

        # TODO: Update mode select property

        # TODO: Make channel select method

        # Timer
        self._timer = QtCore.QTimer(self)
        self.connect(self._timer, QtCore.SIGNAL("timeout()"), self._update)

        # TODO: Make _update_figure() method which syncs properties with UI objects
        #self._update_figure()

        self._update()

        # Start timer
        self._timer.start(100)

        # Execute App (no code after this wil run)
        self.run()

    def _update(self):
        # Called by timer object to update GUI
        if self._mode_select == 'Time Domain':
            # Need to update based on signal emit, once gui has started
            self._qt_main_widget.custom_signal.connect(self._update_time_domain)
            self._qt_main_widget.custom_signal.emit()

    def _update_time_domain(self):

        # Get Data
        # TODO: Add getFilteredData method to signal source
        channel_data = self._signal_source.get_data()

        # Plot data
        for i_channel in range(16):
            if self._selected_channels[i_channel]:  # update curves if selected
                signal = channel_data[:, i_channel]
                sample_num = [x+1 for x in range(len(signal))]
                self._qt_main_widget.curves[i_channel].setData(sample_num, signal)
            else:  # otherwise make invisible
                self._qt_main_widget.curves[i_channel].setData([0], [0])

    # Callbacks
    def signal_select_callback(self, sig_idx):
        # Method to change which signals are displayed based on checkboxes

        for i,checkBox in enumerate(self._qt_main_widget.signalCheckboxes):
            # Check state of this signal checkbox
            state = checkBox.isChecked()
            # Update active channels
            self._selected_channels[i] = state

    def run(self):
        self._qt_main_widget.show()
        self._qt_app.exec_()


class QTWindow(QtGui.QWidget):
    """

    Class for the main qt display

    """

    # This signal can be used on the fly, just needs to be instantiated up front
    custom_signal = QtCore.Signal()

    def __init__(self, signal_viewer):
        # Initialize as QWidget
        QtGui.QWidget.__init__(self)

        # Reference to signal_viewer
        self.signal_viewer = signal_viewer

        # Initialize the QWidget and
        # set its title and minimum width
        self.setWindowTitle('Signal Viewer')
        self.setMinimumWidth(400)
        # TODO: Set minimum height
        # TODO: Set position

        # Create the QVBoxLayout that lays out the whole window
        self.layout = QtGui.QVBoxLayout()

        # Set up PyQtGraph figure
        self.plot_widget = pg.PlotWidget()
        plot_item = self.plot_widget.getPlotItem()
        plot_item.setLabel('bottom', text='Sample Number')
        plot_item.setLabel('left', text='Signal', units='Volts')
        plot_item.setTitle(title='Signal Viewer')
        plot_item.showButtons() # Enables autoscale button
        plot_item.showGrid(x=True,y=True,alpha=0.6)
        #plot_item.addLegend()

        # These are the "Tableau 20" colors as RGB.
        tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
                           (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                           (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                           (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                           (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

        # Set up each curve
        self.curves = []
        for i_channel in range(16):
            self.curves.append(self.plot_widget.plot(pen=pg.mkPen(tableau20[i_channel]), name=str(i_channel)))

        # Add widgets to layout
        self.layout.addWidget(self.plot_widget)
        # Create the QHBoxLayout that will lay out the lower portion of the window
        self.lowerHBoxLayout = QtGui.QHBoxLayout()
        #
        # # Placeholder items for now
        # self.lowerHBoxLayout.addWidget(QLabel('Plot Domain', self))
        # self.lowerHBoxLayout.addWidget(QLabel('Plot Properties', self))

        # Add signal select checkboxes
        self.lowerHBoxLayout.addWidget(QtGui.QLabel('Channel Select: ', self))
        self.signalCheckboxes = []
        for i in range(16):
            self.signalCheckboxes.append(QtGui.QCheckBox(str(i + 1), self))
            self.signalCheckboxes[-1].isTriState = False
            self.signalCheckboxes[-1].setCheckState(QtCore.Qt.Checked)
            self.signalCheckboxes[-1].stateChanged.connect(self.signal_viewer.signal_select_callback)
            self.lowerHBoxLayout.addWidget(self.signalCheckboxes[-1])

        self.layout.addLayout(self.lowerHBoxLayout)

        self.setLayout(self.layout)

if __name__ == "__main__":
    s = SignalViewer()
