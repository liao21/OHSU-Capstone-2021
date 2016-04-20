"""
MyoUdpDriver.py - revision 0

Created on Mar 25 08:50:20 2016

Module to connect to Myo and stream data


@author: W. Haris
"""

##from __future__ import print_function
###from bluepy import btle
from cmdHCI import discoverBtleHCI, scanForBtleMAC
from myo_btle import Connection, myo_struct, isThalmic
import sys
import btle
import time
import threading
from subprocess import Popen
import struct
import socket
##import argparse

bVerbose=False
bTest=True

# TODO: Establish Input Arguments

### Parameters:
##parser = argparse.ArgumentParser(description='Read myo and stream UDP.')
##parser.add_argument('--MAC1', default='D4:5F:B3:52:6C:25',
##                   help='Myo MAC address')
##parser.add_argument('--MAC2', default='F0:1C:CD:A7:2C:85',
##                   help='Myo MAC address')
##parser.add_argument('--IP', default='192.168.56.1',
##                   help='Destination IP Address')
##parser.add_argument('--Port1', default=15001, type=int,
##                   help='Destination Port')
##parser.add_argument('--Port2', default=15002, type=int,
##                   help='Destination Port')
##parser.add_argument('--Iface1', default=0, type=int,
##                   help='hciX interface')
##parser.add_argument('--Iface2', default=1, type=int,
##                   help='hciX interface')
##
##args = parser.parse_args()
##
##mac1 = args.MAC1
##addr1=(args.IP, args.Port1)
##
##mac2 = args.MAC2
##addr2=(args.IP, args.Port2)
##
##iface1 = args.Iface1
##iface2 = args.Iface2
##
### mac address of myo
### (Get from linux command prompt > sudo hcitool lescan)
###mac1 = 'D4:5F:B3:52:6C:25'
###mac2 = 'F0:1C:CD:A7:2C:85'
### destination for UDP
###addr1=('192.168.56.1',15001)
##


class MyoDelegate(btle.DefaultDelegate):
##    def __init__(self, myo, sock, addr, structMyo):
    def __init__(self, myo):
        self.myo = myo.pConn
        self.sock = myo.sockUdp
        self.addr = myo.addrUdp
        # Assign select Notification Handles from Myo Structure
        self.EMGdata_valHandle = myo.disc.EMGdata.hValue    # returns a list of one handle
        self.RawEMG_valHandle = myo.disc.RawEMG.hValue      # returns a list of four handles
        self.IMU_valHandle = myo.disc.IMU.hValue            # returns a list of one handle
        self.Batt_valHandle = myo.disc.Batt.hValue          # returns a list of one handle
        # Assign counter variables
        self.pCount = 0;
        self.imuCount = 0;
        self.battCount = 0;

    def handleNotification(self, cHandle, data):
        if cHandle == self.RawEMG_valHandle[0]:      #0x2b: # EmgData0Characteristic
            self.sock.sendto(data,self.addr)
            self.pCount += 2
        elif cHandle == self.RawEMG_valHandle[1]:    #0x2e: # EmgData1Characteristic
            self.sock.sendto(data,self.addr)
            self.pCount += 2
        elif cHandle == self.RawEMG_valHandle[2]:    #0x31: # EmgData2Characteristic
            self.sock.sendto(data,self.addr)
            self.pCount += 2
        elif cHandle == self.RawEMG_valHandle[3]:    #0x34: # EmgData3Characteristic
            self.sock.sendto(data,self.addr)
            self.pCount += 2
        elif cHandle == self.IMU_valHandle[0]:       #0x1c: # IMUCharacteristic
            self.sock.sendto(data,self.addr)
            self.imuCount += 1
        elif cHandle == self.Batt_valHandle[0]:      #0x11: # BatteryCharacteristic
            self.sock.sendto(data,self.addr)
            self.battCount += 1
        else:
            print('Got Notification: %d' % cHandle)
        return

def setParameters(myo):
    "function parameters"
    #Notifications are unacknowledged, while indications are acknowledged. Notifications are therefore faster, but less reliable.
    # Indication = 0x02; Notification = 0x01

    #TODO: Enumerate myo commands in struct.pack arguments
    
    # Setup main streaming:
    myo.pConn.writeCharacteristic(myo.disc.Batt.hConfig[0],         struct.pack('<bb', 0, 0), 1) # Un/subscribe from battery_level notifications
    myo.pConn.writeCharacteristic(myo.disc.Classifier.hConfig[0],   struct.pack('<bb', 0, 0), 1) # Un/subscribe from classifier indications
    myo.pConn.writeCharacteristic(myo.disc.IMU.hConfig[0],          struct.pack('<bb', 1, 0), 1) # Subscribe from imu notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[0],       struct.pack('<bb', 1, 0), 1) # Subscribe to emg data0 notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[1],       struct.pack('<bb', 1, 0), 1) # Subscribe to emg data1 notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[2],       struct.pack('<bb', 1, 0), 1) # Subscribe to emg data2 notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[3],       struct.pack('<bb', 1, 0), 1) # Subscribe to emg data3 notifications

    #TODO: Enumerate additional command options per Thalmic
    myo.pConn.writeCharacteristic(myo.disc.hCmd, struct.pack('<bbbbbhbbhb',2,0xa,3,1,0,0x12c,0,0,0xaf,0x62), 1) # Tell the myo we want EMG 300=300, IMU 175=200

    # turn off sleep
    myo.pConn.writeCharacteristic(myo.disc.hCmd, struct.pack('<bbb',9,1,1), 1)

    return


def threadMyo(myo):
        tStart = time.time()
        pLastX=0
        imuLastX=0
        while(1):
                tNow = time.time()
                tElapsed = tNow - tStart
                myo.pConn.waitForNotifications(1.0)
                if (tElapsed > 2.0):
                        rate_EMG = (myo.Delegate.pCount - pLastX) / tElapsed
                        rate_IMU = (myo.Delegate.imuCount - imuLastX) / tElapsed
                        if listMyo[0].intHCI:
                                print("Myo1:EMG %4.1f Hz        |IMU %4.1f Hz " % (rate_EMG, rate_IMU ))
                        else:
                                print("Myo2:EMG        %4.1f Hz  |IMU          %4.1f Hz" % (rate_EMG, rate_IMU ))
                        tStart = tNow
                        pLastX = myo.Delegate.pCount
                        imuLastX = myo.Delegate.imuCount

#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

                        
# Get HCI interface(s)
# NOTE:
#   listHCI is needed for syntax of command line arguments
print '\n>> Get HCI'
listHCI=list(discoverBtleHCI(bVerbose))
listHCI.sort() # This sort is redundent but is important for peripheral binding order.
if not listHCI:
    print 'Could not find BTLE radio.'
    sys.exit("No Bluetooth LE radio found. [TERMINATING DRIVER]")
print '\n>> Get HCI Done. (%d found)' % len(listHCI)





# Get MAC Addresses
print '\n>> Get MAC'
print 'Initial BTLE radio scan...'
listMAC=list(scanForBtleMAC(listHCI[0], bVerbose))
if not listMAC:
    print "Could not find any BTLE Devices. [Three more Attempts]"
    listMAC=list(scanForBtleMAC(listHCI[0], bVerbose))
    if not listMAC:
        print "Could not find any BTLE Devices. [Two more Attempts]"
        listMAC=list(scanForBtleMAC(listHCI[0], bVerbose))
        if not listMAC:
            print "Could not find any BTLE Devices. [Last Attempt]"
            listMAC=list(scanForBtleMAC(listHCI[0], bVerbose))
            if not listMAC:
                sys.exit("BTLE radio scan for Devices turned up empty. [TERMINATING DRIVER]")
print '\n>> Get_MAC Done. (%d found)' % len(listMAC)





# Connect found Myo(s)
print '\n>> Connect Myo(s)'
iMyo=0 #Myo counter
listMyo=list()
for iMAC in range(len(listMAC)):
    print '\n>> Start loop for Myo(s) (iter:%d)' % iMyo
    if not iMyo:
        pConn1=Connection(listMAC[iMAC], int(listHCI[0].strip()[len(listHCI[0].strip())-1]))
        if isThalmic(pConn1):
            listMyo.append( myo_struct())
            setattr(listMyo[iMyo],'strMAC', listMAC[iMAC])
            setattr(listMyo[iMyo],'strHCI', listHCI[0])
            setattr(listMyo[iMyo],'intHCI', int(listHCI[0].strip()[len(listHCI[0].strip())-1]))
            setattr(listMyo[iMyo],'pConn', pConn1)
            print 'The BTLE Device with MAC:[%s] is a Thalmic Device on %s' % (listMAC[iMAC], listMyo[iMyo].strHCI)
            iMyo += 1
        else:
            #TODO: need to blacklist the MAC Address
            print 'The BTLE Device with MAC:[%s] is NOT a Thalmic Device!' % listMAC[iMAC]
            pConn1.disconnect()
    elif iMyo:
        if len(listHCI) > 1:
            print 'Second Myo Armbands connected to second BTLE Radio'
            pConn2=Connection(listMAC[iMAC], int(listHCI[1].strip()[len(listHCI[1].strip())-1]))
        else:
            print 'NOTE: using 2 Myo Armbands on one BTLE Radio'
            pConn2=Connection(listMAC[iMAC], listMyo[0].intHCI)
        if isThalmic(pConn2):
            listMyo.append(myo_struct())
            setattr(listMyo[iMyo],'strMAC', listMAC[iMAC])
            if len(listHCI) > 1:
                setattr(listMyo[iMyo],'strHCI', listHCI[1])
                setattr(listMyo[iMyo],'intHCI', int(listHCI[1].strip()[len(listHCI[1].strip())-1]))
                setattr(listMyo[iMyo],'pConn', pConn2)
            else:
                setattr(listMyo[iMyo],'strHCI', listHCI[0])
                setattr(listMyo[iMyo],'intHCI', int(listHCI[0].strip()[len(listHCI[0].strip())-1]))
                setattr(listMyo[iMyo],'pConn', pConn1)
            print 'The BTLE Device with MAC:[%s] is a Thalmic Device on %s' % (listMAC[iMAC], listMyo[iMyo].strHCI)
            iMyo += 1
            break
        else:
            #TODO: need to blacklist the MAC Address
            print 'The BTLE Device with MAC:[%s] is NOT a Thalmic Device!' % listMAC[iMAC]
            pConn2.disconnect()
    print '\n>> Finished one loop for Myo(s)'






# Discover Select Services & Characteristics
##    listMyo[i].discover(listMyo[i].pConn,["Raw EMG","IMU Data","Generic Access", "Myo Attribute"])

# TODO: Need to pickle discovery based on FW version

print '\n>> Discover Myo(s)'
for i in range(len(listMyo)):
    listMyo[i].discover(listMyo[i].pConn,["All"])

    if bTest:
        print '\n>> Dump info'
        listMyo[i].dumpStruct()
        print '=========================================='
        print 'Name: ', listMyo[i].Name
        print 'Appearance: ', listMyo[i].Appear
        print 'PPCP: ', listMyo[i].PPCP
        print 'MAC: ', listMyo[i].MAC
        print 'FW: ', listMyo[i].FW
        print 'hCmd: ', listMyo[i].disc.hCmd





    
# Configure Myo Armband(s)

listMyo[0].addrUdp=('127.0.0.1',15001)
if len(listMyo)>1:
    listMyo[1].addrUdp=('127.0.0.1',15002)

for m in listMyo:
    strBytesPPCP = ''
    for a in m.PPCP:
        b="%0.4X" % a                                           #convert interger to hex
        strBytesPPCP = strBytesPPCP +  "%s %s " % (b[2:],b[:2]) #build hex string in network order
    cmd1 = "sudo hcitool -i %s cmd 0x08 0x0013 40 00 %s 00 00 07 00" % (m.strHCI, strBytesPPCP)
##    COMMAND TRANSLATES TO:   cmd 0x08 0x0013 40 00 06 00 06 00 00 00 90 01 00 00 07 00"
    Popen(cmd1, shell=True).wait()                              #send command to shell
    setParameters(m)                                            #config myo parameters
    m.sockUdp=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #create UDP socket
    m.Delegate = MyoDelegate(m)                                 #build Delegate object
    m.pConn.withDelegate( m.Delegate )                          #assign event handler
    print("\n\nMyo_Config done.")



                        
try:
    useThreading = False
    tStart = time.time()
    if useThreading:
        t1 = threading.Thread(target=threadMyo,args=[listMyo[0]])
        if len(listMyo)>1:
            t2 = threading.Thread(target=threadMyo,args=[listMyo[1]])
        t1.start()
        if len(listMyo)>1:
            t2.start()

        t1.join()
        if len(listMyo)>1:
            t2.join()
    else:
        tStart = time.time()
        pLast1=0
        imuLast1=0
        pLast2=0
        imuLast2=0
        while(1):
            tNow = time.time()
            tElapsed = tNow - tStart
            listMyo[0].pConn.waitForNotifications(1.0)
            if len(listMyo)>1:
                listMyo[1].pConn.waitForNotifications(1.0)
            if (tElapsed > 2.0):
                rate_EMG1 = (listMyo[0].Delegate.pCount - pLast1) / tElapsed
                rate_IMU1 = (listMyo[0].Delegate.imuCount - imuLast1) / tElapsed
                rate_EMG2 = 0 #placeholder
                rate_IMU2 = 0 #placeholder
                if len(listMyo)>1:
                    rate_EMG2 = (listMyo[1].Delegate.pCount - pLast2) / tElapsed
                    rate_IMU2 = (listMyo[1].Delegate.imuCount - imuLast2) / tElapsed
                print("EMG:%4.1f Hz %4.1f Hz    IMU:%4.1f Hz %4.1f Hz    after 2sec period" %
                      (rate_EMG1, rate_EMG2, rate_IMU1, rate_IMU2))
                tStart = tNow
                pLast1 = listMyo[0].Delegate.pCount
                imuLast1 = listMyo[0].Delegate.imuCount
                if len(listMyo)>1:
                    pLast2 = listMyo[1].Delegate.pCount
                    imuLast2 = listMyo[1].Delegate.imuCount

except KeyboardInterrupt:
##    break
    pass

for m in listMyo:
    m.pConn.disconnect()
