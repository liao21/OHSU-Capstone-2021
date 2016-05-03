"""
cmdHCI.py - revision 3.a

0.0 Created on Mar 23 22:02:12 2016
0.3.a - edited on May 01 2016 - Python 3 compatible


Module to discover Bluetooth interfaces and Bluetooth devices
--Functions:
----discoverBtleHCI   :discover BTLE HCI
----configHCI         : (called by 'discoverBtleHCI') bring HCI up or down
----scanForBtleMAC    :discover MAC Addresses


@author: W. Haris
"""

##from sys import argv
##from string import split, rfind
import sys
import string
from subprocess import Popen, PIPE
import re

__version__ = "0.3.a"
print(sys.argv[0] + " Version: " + __version__)

bDEBUG = False

def configHCI(hciX, strDesiredState, bVerbose=False):
    if bVerbose: print('HCI to bring %s: %s' %(strDesiredState,hciX))
    cmdHCIstate = Popen(["sudo","hciconfig",hciX,strDesiredState]).wait()#, shell=True).wait()
    return

def discoverBtleHCI(bVerbose=False):
    #=============================================
    #~~~ Bluetooth Host Controller Interfaces
    #
    foundHCI=list()
    if bVerbose: print('find, open and initialize all linux-configured BT Radios')

    # Alternate command-line process
    ##cmd1 = Popen(["hcitool", "dev"], stdout=PIPE)#, shell=True).wait() 
    ##cmd2 = Popen(["grep", "hci"], stdin=cmd1.stdout, stdout=PIPE)#, shell=True).wait() 
    ##lis=list
    ##lis=iter(cmd2.stdout.readline,b'')
    ##for line in lis:
    ##    print(line.split()[0])

    #~~~ Find Bluetooth Host Controller Interfaces
    # open process with input & output pipes and return results for analysis
    cmdHCIconfig = Popen(["hciconfig"], stdout=PIPE)#, shell=True).wait() 
    cmdGrepHCI = Popen(["grep", "-o", "-e", "hci."], stdin=cmdHCIconfig.stdout, stdout=PIPE)#, shell=True).wait()
    listHCI=list(iter(cmdGrepHCI.stdout.readline,b''))      #populate list with filtered output
    if bDEBUG: print(listHCI)
    #
    # Look for the HCI status ("UP" or "DOWN")
    cmdHCIconfig = Popen(["hciconfig"], stdout=PIPE)#, shell=True).wait() 
    cmdGrepHCIstate = Popen(["grep", "-o", "-e", "UP", "-e", "DOWN"], stdin=cmdHCIconfig.stdout, stdout=PIPE)#, shell=True).wait()
    bytesListHCIstate=list(iter(cmdGrepHCIstate.stdout.readline,b''))      #populate list with filtered output
    if bDEBUG: print(bytesListHCIstate)
    #~~~ Loop through found Bluetooth Host Controller Interfaces
    if len(listHCI)>0:
        i=0
        j=0
        for bytesLineHCI in listHCI:
            # Python 3 requires decode to utf-8
            lineHCI = bytesLineHCI.decode('utf-8')
##            foundHCI.append(lineHCI.split()[0].split(':')[0])
            foundHCI.append(lineHCI.split()[0].split(':')[0])
            if bDEBUG: print(foundHCI)
            #~~~ Open and initialize found HCI devices
            listHCIstate = bytesListHCIstate[i].decode('utf-8')
##            if listHCIstate[i].split()[0]=='DOWN':
            if listHCIstate.split()[0]=='DOWN':
                if bVerbose: print('bringing UP ', foundHCI[j])
                configHCI(foundHCI[j],'up', bVerbose)
            #~~~ Find Bluetooth version for found HCI devices
            cmdHCIver = Popen(["hciconfig",foundHCI[j],"version"], stdout=PIPE)
            listVer=iter(cmdHCIver.stdout.readline,b'')
            if bDEBUG: print(listVer)
            for bytesLineVer in listVer:
                lineVer = bytesLineVer.decode('utf-8')
                if re.search("HCI Version", lineVer):
                    intVer= [int(s) for s in lineVer.split()[2].split('.') if s.isdigit()][0]
                    #~~~ Check for Bluetooth version 4 "a.k.a. Bluetooth LE"
                    if intVer==4:
                        if bVerbose: print('BT Radio using %s is LE' % foundHCI[j])
                        j += 1
                    else:
                        #~~~ Un-find Host Controller Interfaces that are not Bluetooth LE
                        hciXbad=foundHCI.pop(j)
                        print('BT Radio using %s is version %s; BTLE version needed!' %(hciXbad, str(intVer)))
            i += 1
    else:
        print('No BT Radios Found.')
        return

    #~~~ List Bluetooth LE devices (sorted in ascending order)
    #NOTE: HCI interfaces must be listed in ascending order for btle.py to establish dedicated bindings.
    # If btle.py connects a peripheral to interface hci1 before hci0, it will bind a second peripheral
    # to hci1 as well even if the command uses proper syntax for binding the second peripheral to hci0.
    foundHCI.sort()         
    if bVerbose:
        print('Bluetooth LE Radios available:')
        if len(foundHCI)>0:
            pass
        else:
            print('None.')
    print(foundHCI)

    print('HCI discovery done.\n')
    return foundHCI

#%%
def scanForBtleMAC(hciX=None, bVerbose=False):
    listBtleMAC=list()
    if hciX==None:
        listHCI=list(discoverBtleHCI(bVerbose))
        if len(listHCI)>0:
            hciX=listHCI[0]
        else:
            print('No BT Radios Found')
            return
    print('Scaning for BTLE devices on: %s ...' % hciX)
    cmdLEscan = Popen(["sudo","timeout","-s","SIGINT","-k","0","3","sudo","hcitool","-i",hciX,"lescan"], stdout=PIPE)#.wait()
    lstMACscan=iter(cmdLEscan.stdout.readline,b'')      #populate list with filtered output
    if bDEBUG: print(lstMACscan)
    for bytesLine in lstMACscan:
        line = bytesLine.decode('utf-8')
        if bDEBUG: print(line)
        #~~~ Find Bluetooth Perhipheral device MAC Addresses
        sp = line.split(' ')
        if len(sp[0].split(':')) == 6 and sp[0] not in listBtleMAC: # and len(sp) >= 2 and sp[0] not in blacklist:
            listBtleMAC.append(sp[0])
    if bVerbose: print('Found the following BTLE MAC Addresses:')
    print(listBtleMAC)
    print('BTLE MAC scan done.')
    return listBtleMAC


if __name__=='__main__':
    print(sys.argv[0] + " Version: " + __version__)
##    bVerbose=True
    bVerbose=False
    listHCI=list(discoverBtleHCI(bVerbose))
    if len(listHCI)>0:
        hciX=listHCI[0]
    listMAC=list(scanForBtleMAC(hciX, bVerbose))
    
