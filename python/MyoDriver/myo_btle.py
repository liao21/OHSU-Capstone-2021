# -*- coding: utf-8 -*-
"""
myo_btle.py - [see __version__ below]

Created on Mar 22 20:22:37 2016
edited on Apr 24 2016 - comments and verbose improvements
edited on Apr 30 2016 - added try-except handler for non-Myo devices
                        Python 3 compatible

Module to discover Bluetooth Services for a Myo through -btle-
--Object Classes:
----c_struct_construct  :c-structure constructor to store BTLE Svcs & Chars
----myo_struct          :MyoArmband object store BTLE Svcs & Chars
------discover          :BTLE Service Discovery
------appendInfo2       : (called  by 'discover') further Service discovery
------appendInfo        : (called by 'appendInfo2') discover Svc Characteristics
------dumpStruct        :print structure to terminal
------showAttrib        : (called by 'dumpStruct') loop through attributes
------resetStruct       :clear all root attributes
--Functions:
----isThalmic           :confirm that a MAC Address is for a Thalmic device
----addCharData         :used to build the structure object attributes
----Connect             :establish a BTLE Peripheral connection with a MAC address

--discover Services
--discover Characteristics in any discovered Service


@author: W. Haris
"""

from __future__ import with_statement # 2.5 only
import btle
import cmdHCI
from struct import unpack
import time
from subprocess import Popen
import sys
import string

__version__ = "0.5.g"
print (sys.argv[0]  + " Version: " + __version__)

bDEBUG = False

class c_struct_construct:
    pass


#%%
# ADD BLUETOOTH CHARACTERISTIC DATA TO OBJECT_ATTRIBUTE
#  The following will save data by either 1) creating
#  a list or 2) append a list.
def addCharData(obj,attr,data):
    if hasattr(obj,attr):
        (getattr(obj,attr)).append(data)
    else:
        setattr(obj,attr,list([data]))
        


#%%
# CLASS CONSTRUCTOR
class myo_struct:

    # METHOD: Instanciate Class Attributes
    def __init__(self, bVerbose=False):

        # NOTE - The following data to be obtained by discovery from anoter module (ex: cmdHCI.py)
        self.intHCI                 = 0
        self.strHCI                 = 'hci0'
        self.strMAC                 = '00:00:00:00:00:00'

        #note: the following prefix/suffix information is used to create long UUIDs.
        self.myoUUIDprefix  = 'd506'
        self.myoUUIDsuffix  = '-a904-deb9-4748-2c7f4a124842'
        self.SIGUUIDprefix  = '0000'
        self.SIGUUIDsuffix  = '-0000-1000-8000-00805f9b34fb'
        self.count          = 0

        self.disc               = c_struct_construct() # 0x1800 Generic Access
        self.disc.GenAccess     = c_struct_construct() # 0x1800 Generic Access
        self.disc.GenAttrib     = c_struct_construct() # 0x1801 Generic Attribute
        self.disc.DevInfo       = c_struct_construct() # 0x180A Device Information
        self.disc.Batt          = c_struct_construct() # 0x180F Battery Service
        self.disc.MyoAttrib     = c_struct_construct() # 0x0001 Myo Attribute
        self.disc.IMU           = c_struct_construct() # 0x0002 IMU Data Service
        self.disc.Classifier    = c_struct_construct() # 0x0003 Classifier Data Service
        self.disc.EMGdata       = c_struct_construct() # 0x0004 EMG Data Service
        self.disc.RawEMG        = c_struct_construct() # 0x0005 EMG Raw Service
        self.disc.Unknown       = c_struct_construct() # 0x0006 Unknown Service
        # The following dictionary associates a Name to a short UUID for desired Characteristic
        self.ChrNames={"Name"       : '2a00',
                       "Appearance" : '2a01',
                       "PPCP"       : '2a04',
                       "MAC"        : '0101',
                       "FW"         : '0201',
                       "command"    : '0401'
                       }
        # The following dictionary enumerates SIG and Thalmic defined short UUID services
        self.shrtUUID2longSvcName={
            '1800': 'Generic Access',
            '1801': 'Generic Attribute',
            '180a': 'Device Information',
            '180f': "Battery Service",
            '0001': "Myo Attribute",
            '0002': "IMU Data",
            '0003': "Classifier Data",
            '0004': "EMG Data",
            '0005': "Raw EMG",
            '0006': "Unknown"}
        # The following dictionary associates a list object to a known service
        #    enumUUIDlongName[0] == short UUID
        #    enumUUIDlongName[1] == attribute name for a myo_struct object eg: "myo1.disc.GenAccess"
        self.enumUUIDlongName={
            'Generic Access'    : ["1800", "disc.GenAccess"],
            'Generic Attribute' : ["1801", "disc.GenAttrib"],
            'Device Information': ["180a", "disc.DevInfo"],
            "Battery Service"   : ["180f", "disc.Batt"],
            "Myo Attribute"     : ["0001", "disc.MyoAttrib"],
            "IMU Data"          : ["0002", "disc.IMU"],
            "Classifier Data"   : ["0003", "disc.Classifier"],
            "EMG Data"          : ["0004", "disc.EMGdata"],
            "Raw EMG"           : ["0005", "disc.RawEMG"],
            "Unknown"           : ["0006", "disc.Unknown"]
            }

    # METHOD: DISCOVER/STORE BLUETOOTH Descriptors and Characteristics (using BTLE getDescriptors and getCharacteristics methods)
    #           Input: BTLE.Peripheral.Connection, BTLE Service, local object
    # called by 'appendInfo2' method
    def appendInfo(self, perif_conn, srvc, structBase):
        # Discover descriptors
        for d in perif_conn.getDescriptors(srvc.hndStart, srvc.hndEnd):
            # Filter characteristic Attribute 2803
            if str(d.uuid)[4:8]=='2803':
                # Discover characteristic information
                c = perif_conn.getCharacteristics(d.handle, d.handle)
                # Store Data
                addCharData(structBase,'hChar',d.handle)                # Store Characteristic handle (used for ...)
                addCharData(structBase,'hValue',c[0].valHandle)         # Store Characteristic Value handle (streaming data)
                addCharData(structBase,'prop',c[0].properties)          # Store characteristic properties
                addCharData(structBase,'sUUID',str(c[0].uuid)[4:8])     # Store short UUID
                if str(c[0].uuid)[4:8]==self.ChrNames["Name"]:          # Filter for 2a00 (see dictionary above)
                    self.Name=perif_conn.readCharacteristic(c[0].valHandle).decode('utf-8')
                elif str(c[0].uuid)[4:8]==self.ChrNames["Appearance"]:  # Filter for 2a01 (see dictionary above)
                    self.Appear=list(unpack('h',perif_conn.readCharacteristic(c[0].valHandle)))
                elif str(c[0].uuid)[4:8]==self.ChrNames["PPCP"]:        # Filter for 2a04 (see dictionary above)
                    self.PPCP=list(unpack('hhhh',perif_conn.readCharacteristic(c[0].valHandle)))
                elif str(c[0].uuid)[4:8]==self.ChrNames["FW"]:          # Filter for 0201 (see dictionary above)
                    self.FW=list(unpack('hhhh',perif_conn.readCharacteristic(c[0].valHandle)))
                elif str(c[0].uuid)[4:8]==self.ChrNames["MAC"]:         # Filter for 0101 (see dictionary above)
                    a=list(unpack('<BBBBBBhhhhhhh',perif_conn.readCharacteristic(c[0].valHandle)))
                    self.MAC='%x:%x:%x:%x:%x:%x' % (a[5],a[4],a[3],a[2],a[1],a[0])
                elif str(c[0].uuid)[4:8]==self.ChrNames["command"]:     # Filter for 0204 (see dictionary above)
                    self.disc.hCmd=c[0].valHandle
            # Filter Client Characteristic Configuration Attribute 2902
            elif str(d.uuid)[4:8]=='2902':
                addCharData(structBase,'hConfig',d.handle)  # Used to subscribe to service
        return

    # METHOD: DISCOVER/STORE BLUETOOTH Characteristics (using BTLE getServiceByUUID method)
    #     USING: getAppend information

# TODO: This method may not be necessary or can be combined in METHOD:'appendInfo'
    
    def appendInfo2(self, conn, strUUIDname):
##        for svc in conn.services:
##            lsEnumUUID=self.enumUUIDlongName[strUUIDname]
##            if lsEnumUUID[0]==str(svc)[4:8]:
##                if int('0x%s' % lsEnumUUID[0], 16)<7:
##                    longUUID=self.myoUUIDprefix + lsEnumUUID[0] + self.myoUUIDsuffix
##                else:
##                    longUUID=self.SIGUUIDprefix + lsEnumUUID[0] + self.SIGUUIDsuffix
##                self.appendInfo(conn,
##                                conn.getServiceByUUID(longUUID),
##                                getattr(self,lsEnumUUID[1]))
        # obtain List object based on UUID name (see dictionary above)
        lsEnumUUID=self.enumUUIDlongName[strUUIDname]
        
        next(svc for svc in conn.services if lsEnumUUID[0]==str(svc)[4:8])
        # convert short UUID to an integer and determine if it is a SIG assigned UUID Service
        #  or if it is a Thalmic Myo Service (Thalmic services are 0001 through 0006)
        if int('0x%s' % lsEnumUUID[0], 16)<7:
            longUUID=self.myoUUIDprefix + lsEnumUUID[0] + self.myoUUIDsuffix
        else:
            longUUID=self.SIGUUIDprefix + lsEnumUUID[0] + self.SIGUUIDsuffix
        self.appendInfo(conn,
                        conn.getServiceByUUID(longUUID),
                        getattr(self.disc,lsEnumUUID[1].split('.')[1]))
        


    # METHOD: DISCOVER SERVICES (using BTLE getServices)
    #   Input: BTLE.Peripheral.Connection, list of Services desired
    def discover(self, conn, discSvcName = list('All')):
        print('\n\nDiscover BT Handle Descriptors')
        allSvcNames=list(['Generic Access', 'Generic Attribute',
                         'Device Information', 'Battery Service',
                         'Myo Attribute', 'Classifier Data',
                         'IMU Data', 'EMG Data', 'Raw EMG'])

        if len(discSvcName)==1 and discSvcName[0]=="All":
            del discSvcName[:] # to get rid of the 'All'
            discSvcName=list(allSvcNames[:])
        conn.getServices()
        for svcName in discSvcName:
            print('.'),
            self.appendInfo2(conn, svcName)
        print('BTLE Discovery Done.')

        return

    # METHOD: DISPLAY DISCOVERED CONTENT
    #   Input: storage object
    def showAttrib(self, structBase):
        if hasattr(structBase,'hChar'):
            print('Characteristic Handle(s):                      %s' % getattr(structBase,'hChar'))
        if hasattr(structBase,'hValue'):
            print('Characteristic Value Handle(s):                %s' % getattr(structBase,'hValue'))
        if hasattr(structBase,'hConfig'):
            print('Client Characteristic Configuration Handle(s): %s' % getattr(structBase,'hConfig'))
        if hasattr(structBase,'sUUID'):
            print('Characteristic Short UUID(s):                  %s' % getattr(structBase,'sUUID'))
        if hasattr(structBase,'prop'):
            print('Characteristic Properties:                     %s' % getattr(structBase,'prop'))
        
    # METHOD: DISPLAY FORMAT
    def dumpStruct(self):
        if bDEBUG: print('start dumpStruct')
##        Python 3 uses items() not iteritems()
##        for key, value in self.enumUUIDlongName.iteritems():
        for key, value in self.enumUUIDlongName.items():
            print('\n- %s --------------------------' % key)
            if hasattr(self.disc,value[1].split('.')[1]):
                self.showAttrib(getattr(self.disc,value[1].split('.')[1]))
                (getattr(self.disc,value[1].split('.')[1]))
##        print('\n- Generic Access --------------------------')
##        if hasattr(self.disc,'GenAccess'): self.showAttrib(self.disc.GenAccess)

    def resetStruct(self):
        ## TODO: Should loop through object attributes in order to delete them
##        Python 3 uses items() not iteritems()
##        for key, value in self.enumUUIDlongName.iteritems():
        for key, value in self.enumUUIDlongName.items():
            if hasattr(self.disc,value[1].split('.')[1]):
                delattr(self.disc,value[1].split('.')[1])
        self.__init__()

class Connection(btle.Peripheral):
##    def __init__(self, mac, ifc=0, ty='public'):
    def __init__(self, mac, ifc, ty='public'):
        try:
            btle.Peripheral.__init__(self, mac, ty, ifc)
        except btle.BTLEException:
            p=None
##            blacklist.append(mac
def isThalmic(conn):
    checkMyo=myo_struct()
    checkMyo.discover(conn,["Device Information"])
    if hasattr(checkMyo.disc,"DevInfo"):
        if hasattr(checkMyo.disc.DevInfo,"hValue"):
            try:
                strMfg=conn.readCharacteristic(checkMyo.disc.DevInfo.hValue[0]).decode('utf-8')
                
                if strMfg=='Thalmic Labs':
                    return True
                else:
                    return False
            except:
                return False
        else:
            print('Object_construct Missing Characteristic Value Handle attribute')
            return False
    else:
        print('Object_construct Missing Device Info Service attribute')
        return False

    if bDEBUG: print('isThalmic done.')
#%%
## The following code (when this module is run as a stand-alone script)
##    will demonstrate this module's discovery capabilities and evaluate
##    how long the discover takes.  It is assumed that the BTLE radio is
##    on interface 'hci0' and a known MAC address for the Myo (only one)
##    is required.
    
if __name__=='__main__':
    print (sys.argv[0]  + " Version: " + __version__)
    bVerbose=False

    tStart1=time.time()

    # Get HCI interface(s)
    hciX='hci0'

    # Get MAC Addresses
    knownMAC =  'D0:8A:F1:84:B5:CB'
    knownMAC =  'DE:61:5F:43:2C:63'
    print('You must have a known MAC address to run this as a stand-alone module')
    print('Using: ' + knownMAC)

    # Configure HCI
    strDesiredState="up"
    cmdHCIstate = Popen(["sudo","hciconfig",hciX,strDesiredState]).wait()#, shell=True).wait()
    listMAC=list()
    listMAC.append(knownMAC)


    #Confirm MAC is for Thalmic
    for mac in listMAC:
        conn=Connection(mac, hciX)
        tEnd1=time.time()
        tStart2=tEnd1
        if isThalmic(conn):
            myo1=myo_struct()
            myo1.strMAC = mac
            myo1.strHCI = hciX
            print('The BTLE Device with MAC:[%s] is a Thalmic Device' % myo1.strMAC)
        else:
            print('The BTLE Device with MAC:[%s] is NOT a Thalmic Device!' % myo1.strMAC)
            #need to blacklist the MAC Address
        tEnd2=time.time()
        tStart3=tEnd2


    # Discover Select Services & Characteristics
##    myo1.discover(conn,"All")
    myo1.discover(conn,["Raw EMG","IMU Data","Generic Access", "Myo Attribute"])
    myo1.dumpStruct()
    print('==========================================')
    print('Name: ', myo1.Name)
    print('Appearance: ', myo1.Appear)
    print('PPCP: ', myo1.PPCP)
    print('MAC: ', myo1.MAC)
    print('FW: ', myo1.FW)
    print('hCmd: ', myo1.disc.hCmd)

    tEnd3=time.time()
    print('==========================================')
    print('==========================================')
    print('==========================================')

    myo1.resetStruct()
    tStart4=time.time()
    # Discover All Services & Characteristics
    myo1.discover(conn,['All'])
    myo1.dumpStruct()
    print('==========================================')
    print('Name: ', myo1.Name)
    print('Appearance: ', myo1.Appear)
    print('PPCP: ', myo1.PPCP)
    print('MAC: ', myo1.MAC)
    print('FW: ', myo1.FW)
    print('hCmd: ', myo1.disc.hCmd)
    tEnd4=time.time()
    conn.disconnect()
    print('\ndTime1 Connect = %f' % (tEnd1-tStart1))
    print('\ndTime2 Is Thalmic = %f' % (tEnd2-tStart2))
    print('\ndTime3 Discover Subset = %f' % (tEnd3-tStart3))
    print('\ndTime4 Discover All = %f' % (tEnd4-tStart4))

