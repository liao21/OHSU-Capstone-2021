In order to enable Intan UDP interface to the MiniVIE, please see the modificaitons required below for the 
Intan Recording System Software

Contact: Robert Amriger









Modification and Usage Summary:



source code here has been modified from the original v1.11 version


Open .pro file --> QT Creator

updates include:

0) added qtincludes.h to almost all .cpp files just to get to compile
There's a note about this in the readme file


1) add to .pro file:

	QT            += network

--> re-run qmake

2) In mainwindow.cpp, mainwindow.h

added udp to constructor
added QUdpSocket object


%%%%%%%%
mainwindow.h
Line 28:

// RSA Added for UDP Support
#include <QUdpSocket>


Line 271:

    QUdpSocket *udpSocket;    // RSA Added for UDP Support



%%%%%%%%
mainwindow.cpp line 49 (after includes):

#include "qtincludes.h"            // RSA Added for UDP Support
#include <QtCore/QDataStream>      // RSA Added for UDP Support
#include <QtCore/QByteArray>       // RSA Added for UDP Support

%%%%%%%%
mainwindow.cpp line 115 (in constructor):

stopButton->setEnabled(false);

    // RSA Added for UDP Support
    udpSocket = new QUdpSocket(this);
    udpSocket->bind(QHostAddress::LocalHost, 7755);
    connect(udpSocket, SIGNAL(readyRead()),
            this, SLOT(readPendingDatagrams()));


openInterfaceBoard();


%%%%%%%%
mainwindow.cpp 
MainWindow::runInterfaceBoard()
Line 2055

// Apply notch filter to amplifier data.
signalProcessor->filterData(numUsbBlocksToRead, channelVisible);

            // ///////////////////////////////
            // RSA Added for UDP Support
            // ///////////////////////////////

            QByteArray byteArray;
            QDataStream dataStream(&byteArray, QIODevice::WriteOnly);
            for (uint stream = 0; stream < 1; ++stream) {
            //for (int stream = 0; stream < signalProcessor->numDataStreams; ++stream) {
                for (uint channel = 0; channel < 16; ++channel) {
                    for (uint i = 0; i < SAMPLES_PER_DATA_BLOCK * numUsbBlocksToRead; i++) {
                        //stream << signalProcessor->amplifierPostFilter.at(stream).at(channel).at(i);
                        dataStream << signalProcessor->amplifierPostFilter.at(stream).at(channel).at(i);
                    }
                }
            }

            //qDebug() << "Buffer's size:" << byteArray.size() << "byte" << numUsbBlocksToRead;

            //Write data to UDP
            //udpSocket->writeDatagram(myDatagram.data(), myDatagram.size(),QHostAddress::LocalHost,5678);
            udpSocket->writeDatagram(byteArray,QHostAddress::LocalHost,5678);

// Trigger WavePlot widget to display new waveform data.
wavePlot->passFilteredData();





%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



Running:

Follow Opal Kely and FTDI setup instructions on Intan downloads site

Running the release version of the executable can be done either in Qt Creator (Run)

To use the windows executable, ensure that the Qt libraries are on the system path:
C:\Qt\5.3\mingw482_32\bin;C:\Qt\Tools\mingw482_32\bin;
