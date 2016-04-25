"""
MyoUdpDriver.py - ver 0.6

Created on Mar 25 08:50:20 2016 - proof simultaneous dual myo configuration at 300Hz:EMG 200Hz:IMU
Edited on Apr 24 2016 - improved driver options, enable console output, improved threading

Module to connect to Myo and stream data


@author: W. Haris
"""

##from __future__ import print_function
###from bluepy import btle
from cmdHCI import discoverBtleHCI, scanForBtleMAC, configHCI
from myo_btle import Connection, myo_struct, isThalmic
import sys
import btle
import time
import threading
from subprocess import Popen
import struct
import socket
import argparse
import binascii

__version__ = "0.6"


### Parameters:
#   NOTE FOR BOOLEAN ARGUMENTS:
#       example usage to disable threading and to un/subscribe from IMU Notifications:
#
#           "python MyoUdpDriver.py --bNoIMU True --bNoThrd True ..."
#
#       otherwise allow the argument to accept the default value by
#       not including the argument option at all
#       example usage to un/subscribe from IMU Notifications and allow Threading by default value:
#
#           "python MyoUdpDriver.py --bNoIMU True ..."
#
parser = argparse.ArgumentParser(description='Read myo and stream UDP. ' +
                                 ' Default options will stream ' +
                                 'Notifications (Raw EMG Data, IMU Data, Battery Data) and ' +
                                 'Indications (IMU.Events and Classifier.Events) ' +
                                 'to IP Address: 127.0.0.1 using ports 10001 and 10002.  ' +
                                 'Streaming frequency is displayed every 2 seconds.' +
                                 '  -------->   ' +
                                 'NOTE: command-line option --bVrbEMG *may* create a UDP delay if run concurrently with ' +
                                 'MyoUdp.py in a different console terminal ' +
                                 'on the same computer (Raspberry Pi 2 for example)'
                                 )
# BLUETOOTH DEVICE MAC ADDRESS
parser.add_argument('--strMAC1', default='DISCOVERY',
                    help='{str} <DISCOVERY> Myo MAC address')
parser.add_argument('--strMAC2', default='DISCOVERY',
                    help='{str} <DISCOVERY> Myo MAC address')
# NETWORK ADDRESS and PORTS & BLUETOOTH RADIO INTERFACE
parser.add_argument('--iIface1', default = -1, type=int,
                    help='{int} <-1> Discover/set hciX interface')
parser.add_argument('--iIface2', default = -1, type=int,
                    help='{int} <-1> Discover/set hciX interface')
parser.add_argument('--sDestIP', default='127.0.0.1',
                    help='{str} <''127.0.0.1''> Destination IP Address')
parser.add_argument('--iPrtEMG1', default=10001, type=int,
                    help='{int} <10001> Destination Port')
parser.add_argument('--iPrtEMG2', default=10002, type=int,
                    help='{int} <10002> Destination Port')
#NOTE: FUTURE PORT OPTIONS: (also in Configure Myo Armband(s) section /and/ MyoDelegate section)
##parser.add_argument('--iPrtTrn1', default=3003, type=int,
##                    help='{int} <3003> Destination Trainer Port')
##parser.add_argument('--iPrtTrn2', default=3004, type=int,
##                    help='{int} <3004> Destination Trainer Port')
##parser.add_argument('--iPrtIMU1', default=3005, type=int,
##                    help='{int} <3005> Destination IMU Port')
##parser.add_argument('--iPrtIMU2', default=3006, type=int,
##                    help='{int} <3006> Destination IMU Port')
##parser.add_argument('--iPrtBat1', default=3007, type=int,
##                    help='{int} <3007> Destination Batt Port')
##parser.add_argument('--iPrtBat2', default=3008, type=int,
##                    help='{int} <3008> Destination Batt Port')
# MYO SUBSCRIPTIONS
parser.add_argument('--bNoIMU', default = False, type=bool,
                    help='{bool} <False> Turn off Subscription to IMU Svc')
parser.add_argument('--bNoEMG', default = False, type=bool,
                    help='{bool} <False> Turn off Subscription to Raw EMG Svc')
parser.add_argument('--bNoBatt', default = False, type=bool,
                    help='{bool} <False> Turn off Subscription to Battery')
parser.add_argument('--bNoCls', default = False, type=bool,
                    help='{bool} <False> Turn off Subscription to Classifier Svc')
# VERBOSE SETTINGS
parser.add_argument('--bVrbEMG', default = False, type=bool,
                    help='{bool} <False> Print EMG Realtime Stream to terminal')
parser.add_argument('--bVrbNoti', default = False, type=bool,
                    help='{bool} <False> Print Notifications to terminal')
parser.add_argument('--bVrbHCI', default = False, type=bool,
                    help='{bool} <False> Print HCI information to terminal')
parser.add_argument('--bVrbDisc', default = False, type=bool,
                    help='{bool} <False> Print Discovery Information to terminal')
# THREADING
parser.add_argument('--bNoThrd', default = False, type=bool,
                    help='{bool} <False> Enable data stream threads for each Myo')

args = parser.parse_args()

# mac address of myo
#mac1 = 'D4:5F:B3:52:6C:25'
#mac2 = 'F0:1C:CD:A7:2C:85'



class MyoDelegate(btle.DefaultDelegate):
##    def __init__(self, myo, sock, addr, structMyo):
    def __init__(self, myo):
        self.myo = myo.pConn
        self.sock = myo.sockUdp
        self.addr = myo.addrUdp
##        self.addrTrainer = myo.addrUdpTrainer
##        self.addrIMU = myo.addrUdpIMU
##        self.addrBatt = myo.addrUdpBatt
        self.bVerboseNotif = myo.bVerboseNotif
        # Assign select Notification Handles from Myo Structure
        self.EMGdata_valHandle = myo.disc.EMGdata.hValue    # returns a list of one handle
        self.RawEMG_valHandle = myo.disc.RawEMG.hValue      # returns a list of four handles
        self.IMU_valHandle = myo.disc.IMU.hValue            # returns a list of one handle
        self.Batt_valHandle = myo.disc.Batt.hValue          # returns a list of one handle
        self.Classifier_valHandle = myo.disc.Classifier.hValue          # returns a list of one handle
        # Assign counter variables
        self.pCount = 0;
        self.imuCount = 0;
        self.battCount = 0;
        # Create the first data payload variable 'l' used for brevity
        # note one 'l' =8bytes; therefore 6l=48bytes

##        emptyIMUdata=list()
##        for i in range(10): emptyIMUdata.append(0)
##        emptyIMUdata[0]=1 # to make sure the Quaternion orientation matrix is valid
##        self.zerosIMUdata=bytearray(struct.pack('%dh' % len(emptyIMUdata),*emptyIMUdata))
        self.zerosIMUdata=bytearray(struct.pack('4h3h3h', 1,0,0,0 ,0,0,0 ,0,0,0))
        
##        emptyEMGdata=list()
##        for i in range(8): emptyEMGdata.append(127)
##        self.ceilEMGdata=bytearray(struct.pack('8b',*emptyEMGdata))
        self.ceilEMGdata=bytearray(struct.pack('8b',127, 127, 127, 127, 127, 127 ,127, 127))

##        self.full_sMask_8b = struct.pack('8b',127,127,127,127,127,127,127,127)
##        self.full_uMask_8b = struct.pack('8B',255,255,255,255,255,255,255,255)

        self.incomingEMGdata = [0,1,2,3, 4,5,6,7]
##        self.incomingEMGdata = bytearray(struct.pack('8b',2,-2,5,-5,10,-10,100,-100))


    def handleNotification(self, cHandle, data):
        # NOTE: The data payload will send either bogus EMG or bogus IMU data
        #        with each UDP packet.
        # The payload will carry ceiling EMG values ((8)*127) for each IMU notification, and
        #  the payload will carry zeros for IMU data with each EMG notification.
        # Filter for IMU data at the receiver by adding the first 8 bytes
        #  checking for a total of 1016 to confirm an IMU data transmit or
        #  else the payload contains new EMG data.

        if cHandle == self.RawEMG_valHandle[0]:      #0x2b: # EmgData0Characteristic
            self.packEMGandTransmit(data)
            self.pCount += 2
        elif cHandle == self.RawEMG_valHandle[1]:    #0x2e: # EmgData1Characteristic
            self.packEMGandTransmit(data)
            self.pCount += 2
        elif cHandle == self.RawEMG_valHandle[2]:    #0x31: # EmgData2Characteristic
            self.packEMGandTransmit(data)
            self.pCount += 2
        elif cHandle == self.RawEMG_valHandle[3]:    #0x34: # EmgData3Characteristic
            self.packEMGandTransmit(data)
            self.pCount += 2
        elif cHandle == self.IMU_valHandle[0]:       #0x1c: # IMUCharacteristic
            self.packIMUandTransmit(data)
            self.imuCount += 1
        elif cHandle == self.Batt_valHandle[0]:      #0x11: # BatteryCharacteristic
##            self.sock.sendto(data,self.addrBatt)
            self.battCount += 1
        elif cHandle == self.Classifier_valHandle[0]: #0x??: # ClassifierCharacteristic
            self.packIMUandTransmit(data)
##            self.sock.sendto(data,self.addrBatt)
        else:
            print('Got unfiltered Notification from BTLE Characteristic Handle: %d' % cHandle)
        
        return

    def packEMGandTransmit(self, dataEMG):
        # Handle first Raw EMG
        self.incomingEMGdata = struct.unpack('8b',dataEMG[:8])
        self.data_28bPayload = dataEMG[:8] + self.zerosIMUdata
        self.sock.sendto(self.data_28bPayload, self.addr)
        if self.bVerboseNotif:
            print binascii.hexlify(self.data_28bPayload)
        # Handle second Raw EMG
        self.incomingEMGdata = struct.unpack('8b',dataEMG[8:])
        self.data_28bPayload = dataEMG[8:] + self.zerosIMUdata
        self.sock.sendto(self.data_28bPayload, self.addr)
        if self.bVerboseNotif:
            print binascii.hexlify(self.data_28bPayload)

    def packIMUandTransmit(self, dataIMU):
        self.data_28bPayload = self.ceilEMGdata + dataIMU
        self.sock.sendto(self.data_28bPayload, self.addr)
        if self.bVerboseNotif:
            print binascii.hexlify(self.data_28bPayload)
            
    def packClsandTransmit(self, dataClassifier):
        self.data_28bPayload = self.ceilEMGdata + dataIMU
        self.sock.sendto(self.data_28bPayload, self.addr)
        if self.bVerboseNotif:
            print binascii.hexlify(self.data_28bPayload)
            

def setParameters(myo):
    "function parameters"
    #Notifications are unacknowledged, while indications are acknowledged. Notifications are therefore faster, but less reliable.
    # Indication = 0x02; Notification = 0x01

    #TODO: Enumerate myo commands in struct.pack arguments

    # Setup main streaming:
    myo.pConn.writeCharacteristic(myo.disc.Batt.hConfig[0],         struct.pack('<bb', myo.subscriptionBat, 0), 1) # Un/subscribe from battery_level notifications
    myo.pConn.writeCharacteristic(myo.disc.Classifier.hConfig[0],   struct.pack('<bb', myo.subscriptionCls, 0), 1) # Un/subscribe from classifier indications
    myo.pConn.writeCharacteristic(myo.disc.IMU.hConfig[0],          struct.pack('<bb', myo.subscriptionIMU, 0), 1) # Subscribe from imu notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[0],       struct.pack('<bb', myo.subscriptionEMG, 0), 1) # Subscribe to emg data0 notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[1],       struct.pack('<bb', myo.subscriptionEMG, 0), 1) # Subscribe to emg data1 notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[2],       struct.pack('<bb', myo.subscriptionEMG, 0), 1) # Subscribe to emg data2 notifications
    myo.pConn.writeCharacteristic(myo.disc.RawEMG.hConfig[3],       struct.pack('<bb', myo.subscriptionEMG, 0), 1) # Subscribe to emg data3 notifications

    #TODO: Enumerate additional command options per Thalmic
    myo.pConn.writeCharacteristic(myo.disc.hCmd, struct.pack('<bbbbbhbbhb',2,0xa,3,1,0,0x12c,0,0,0xaf,0x62), 1) # Tell the myo we want EMG 300=300, IMU 175=200

    # turn off sleep
    myo.pConn.writeCharacteristic(myo.disc.hCmd, struct.pack('<bbb',9,1,1), 1)

    return


def threadMyo(myo, bVrbEMG):
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
                        if listMyo[0].intHCI and not bVrbEMG:
                                print("Myo1:EMG %4.1f Hz        |IMU %4.1f Hz " % (rate_EMG, rate_IMU ))
                        elif not bVrbEMG:
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
if args.iIface1 < 0 or args.iIface2 < 0:
    listHCI=list(discoverBtleHCI(args.bVrbHCI))
    listHCI.sort() # This sort is redundent but is important for peripheral binding order.
    if not listHCI:
        print 'Could not find BTLE radio.'
        sys.exit("No Bluetooth LE radio found. [TERMINATING DRIVER]")
else:
    listHCI=list()
if args.iIface1 >= 0:
    configHCI("hci"+str(args.iIface1),"UP", True)
    listHCI.insert(0, "hci"+str(args.iIface1))
if args.iIface2 >= 0:
    configHCI("hci"+str(args.iIface2),"UP", True)
    listHCI.insert(0, "hci"+str(args.iIface2))
print '\n>> Get HCI Done. (%d found)' % len(listHCI)





#%%
# Get MAC Addresses
print '\n>> Get MAC'
if args.strMAC1=="DISCOVERY" or args.strMAC2=="DISCOVERY":
    print 'Initial BTLE radio scan...'
    listMAC=list(scanForBtleMAC(listHCI[0], args.bVrbHCI))
    if not listMAC:
        print "Could not find any BTLE Devices. [Three more Attempts]"
        listMAC=list(scanForBtleMAC(listHCI[0], args.bVrbHCI))
        if not listMAC:
            print "Could not find any BTLE Devices. [Two more Attempts]"
            listMAC=list(scanForBtleMAC(listHCI[0], args.bVrbHCI))
            if not listMAC:
                print "Could not find any BTLE Devices. [Last Attempt]"
                listMAC=list(scanForBtleMAC(listHCI[0], args.bVrbHCI))
                if not listMAC:
                    sys.exit("BTLE radio scan for Devices turned up empty. [TERMINATING DRIVER]")
else:
    listMAC=list()
if args.strMAC1 != "DISCOVERY":
    listMAC.insert(0,strMAC1)
if args.strMAC2 != "DISCOVERY":
    listMAC.insert(1,strMAC2)
print '\n>> Get_MAC Done. (%d found)' % len(listMAC)





#%%
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






#%%
# Discover Select Services & Characteristics
##    listMyo[i].discover(listMyo[i].pConn,["Raw EMG","IMU Data","Generic Access", "Myo Attribute"])

# TODO: Need to pickle discovery based on FW version

print '\n>> Discover Myo(s)'
for i in range(len(listMyo)):
    listMyo[i].discover(listMyo[i].pConn,["All"])

    listMyo[i].bVerboseNotif = args.bVrbNoti
    if args.bVrbDisc:
        print '\n>> Dump info'
        listMyo[i].dumpStruct()
        print '=========================================='
        print 'Name: ', listMyo[i].Name
        print 'Appearance: ', listMyo[i].Appear
        print 'PPCP: ', listMyo[i].PPCP
        print 'MAC: ', listMyo[i].MAC
        print 'FW: ', listMyo[i].FW
        print 'hCmd: ', listMyo[i].disc.hCmd





    
#%%
# Configure Myo Armband(s)

listMyo[0].addrUdp=(args.sDestIP, args.iPrtEMG1)
##listMyo[0].addrUdpTrainer=(args.sDestIP, args.iPrtTrn1)
##listMyo[0].addrUdpIMU=(args.sDestIP, args.iPrtIMU1)
##listMyo[0].addrUdpBatt=(args.sDestIP, args.iPrtBat1)
listMyo[0].subscriptionIMU = not args.bNoIMU
listMyo[0].subscriptionEMG = not args.bNoEMG
listMyo[0].subscriptionBat = not args.bNoBatt
if args.bNoCls:
    listMyo[0].subscriptionCls=False
else:
    listMyo[0].subscriptionCls=0x02
if len(listMyo)>1:
    listMyo[1].addrUdp=(args.sDestIP, args.iPrtEMG2)
##    listMyo[1].addrUdpTrainer=(args.sDestIP, args.iPrtTrn2)
##    listMyo[1].addrUdpIMU=(args.sDestIP, args.iPrtIMU2)
##    listMyo[1].addrUdpBatt=(args.sDestIP, args.iPrtBat2)
    listMyo[1].subscriptionIMU = not args.bNoIMU
    listMyo[1].subscriptionEMG = not args.bNoEMG
    listMyo[1].subscriptionBat = not args.bNoBatt
    if args.bNoCls:
        listMyo[1].subscriptionCls=False
    else:
        listMyo[1].subscriptionCls=0x02


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




#%%
rate_EMG1 = 0
rate_EMG2 = 0
if args.bVrbEMG:
    if len(listMyo)>1:
        print '\n---- ---- ---- ---- ---- ---- ---- ---- | ---- ---- ---- ---- ---- ---- ---- ---- | ------ ------ --'
    else:
        print '\n---- ---- ---- ---- ---- ---- ---- ---- | ____ Hz '
    try:
        pauseResponse = input('Make sure the above line fits the console window <Press Enter> to continue... ')
    except SyntaxError:
        pass

print '\n  Press <Ctrl-C> to terminate; <Ctrl-Z> to suspend (''fg'' to resume suspend)\n'

try:
    tStart = time.time()
    if args.bNoThrd:
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
            if args.bVrbEMG:
                a = listMyo[0].Delegate.incomingEMGdata
                if len(listMyo)>1:
                    b = listMyo[1].Delegate.incomingEMGdata
                    sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %4d %4d %4d %4d %4d %4d %4d %4d | %4.1f %4.1f Hz' %
                                     (a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],
                                      b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],
                                      rate_EMG1, rate_EMG2))
            ##                          ,*myoReceiver1.dataEMG[:1,:], *myoReceiver2.dataEMG[:1,:]))
                else:
                    sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %4.1f Hz' %
                                     (a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],rate_EMG1))
                sys.stdout.flush()
            if (tElapsed > 2.0):
                rate_EMG1 = (listMyo[0].Delegate.pCount - pLast1) / tElapsed
                rate_IMU1 = (listMyo[0].Delegate.imuCount - imuLast1) / tElapsed
                if len(listMyo)>1:
                    rate_EMG2 = (listMyo[1].Delegate.pCount - pLast2) / tElapsed
                    rate_IMU2 = (listMyo[1].Delegate.imuCount - imuLast2) / tElapsed
                else:
                    rate_EMG2 = 0
                    rate_IMU2 = 0
                if not args.bVrbEMG:
                    print("EMG:%4.1f Hz %4.1f Hz    IMU:%4.1f Hz %4.1f Hz    after 2sec period" %
                          (rate_EMG1, rate_EMG2, rate_IMU1, rate_IMU2))
                tStart = tNow
                pLast1 = listMyo[0].Delegate.pCount
                imuLast1 = listMyo[0].Delegate.imuCount
                if len(listMyo)>1:
                    pLast2 = listMyo[1].Delegate.pCount
                    imuLast2 = listMyo[1].Delegate.imuCount

    else:
        t1 = threading.Thread(target=threadMyo,args=[listMyo[0], args.bVrbEMG])
        if len(listMyo)>1:
            t2 = threading.Thread(target=threadMyo,args=[listMyo[1], args.bVrbEMG])

        t1.start()
        if len(listMyo)>1:
            t2.start()

        if args.bVrbEMG:
            while(1):
                a = listMyo[0].Delegate.incomingEMGdata
                if len(listMyo)>1:
                    b = listMyo[1].Delegate.incomingEMGdata
                else:
                    b = [0,0,0,0,0,0,0,0]
                if len(listMyo)>1:
                    sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d | %4d %4d %4d %4d %4d %4d %4d %4d | %4.1f %4.1f Hz' %
                                     (a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],
                                      b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],
                                      rate_EMG1, rate_EMG2))
            ##                          ,*myoReceiver1.dataEMG[:1,:], *myoReceiver2.dataEMG[:1,:]))
                else:
                    sys.stdout.write('\r%4d %4d %4d %4d %4d %4d %4d %4d ' %
                                     (a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7]))
                sys.stdout.flush()

        print '\n join Threads'
        t1.join()
        if len(listMyo)>1:
            t2.join()
        print '\n post join'


except KeyboardInterrupt:
##    break
    pass

for m in listMyo:
    m.pConn.disconnect()
