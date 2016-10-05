#!/usr/bin/python
# test script for MPL interface
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
from builtins import input

def ping(host):
    """
    Returns True if host responds to a ping request
    """
    import os, platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if  platform.system().lower()=="windows" else "-c 1"

    # Ping
    return os.system("ping " + ping_str + " " + host) == 0

## Show menu ##
print (30 * '-')
print ("   M A I N - M E N U")
print (30 * '-')
print ("1. Ping: Limb system and router using OS")
print ("2. User management")
print ("3. Reboot the server")
print (30 * '-')
 
## Get input ###
#choice = raw_input('Enter your choice [1-3] : ')
choice = input('Enter selection : ')
assert isinstance(choice, str)    # native str on Py2 and Py3
 
### Convert string to int type ##
choice = int(choice)
 
### Take action as per selected menu-option ###
if choice == 1:
        print ("Starting ping...")
        result = ping('192.0.0.10')
        print(result)
elif choice == 2:
        print ("Starting user management...")
elif choice == 3:
        print ("Rebooting the server...")
else:    ## default ##
        print ("Invalid number. Try again...")

        
        
        
