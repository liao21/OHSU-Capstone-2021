For complete installation:
First, need to install bluetooth drivers for compatibility with noble bluetooth. 
Instructions can be found here: https://www.youtube.com/watch?v=mL9B8wuEdms

Install latest Visual Studio Community: https://www.visualstudio.com/

	1. Download Visual Studio Community Installer
	2. Install all Windows components

Install Python 2.7: http://python.org/

	1. Under Downloads, Python 2.7.13
	2. Accept all default settings
	
Install NodeJs: http://nodejs.org

	1. Install latest LTS version
	2. Use default options

Need to bypass Windows Bluetooth Stack. Make sure to use bluetooth with Broadcomm Chipset, or as compatible with noble.
Logitech adaptors come with compatible chipset. In order to bypass and install drivers:

Install Zadig: http://zadig.akeo.ie/

	1. Download the tool and launch.
	2. Options ==> List all devices.
	3. Scroll down and choose bluetooth adapter. (BCM20702A0 or similar)
	4. Click replace device
	
Screenshots for all above steps can be found on the youtube link mentioned above. 

Then, download javascript from this library, and in this location:

To compile, first run:
npm install myonodebluetoothapl

This command must be run any time changes happen to any file other than myo_udp.js

To run:

	node myo_udp --n(optional) numBands --option1 value1 value2 ... --option2 value1 value2 ...

OPTIONS:
--n 	number of armbands. 

	Default 1 armband. Takes one value determining number of armbands. If used, must be first option.

--ADD 	MAAC address. 
	 
	Default for 1 armband can be set above. Value is armband maac address without ':' characters. Can include as many as necessary.

--PORT	Destination port to send to. 
		
	Default is 15001. Include values as necessary in same order as maac address.
		
--IP 	Destination IP.
		
	Default is localhost. Include values as necessary in same order as maac address.
	
--DEBUG  Verbosity settings

	Default is 0. No additional text will be printed
	Debug level 0: No additional text other than startup
	Debug level 1: Some additional text, including IP addresses, Ports, and MAAC addresses for debugging
	Debug Level 2: For critical debugging, also prints raw data. 
		
Example: node myo_udp --n 4 --ADD address1 address2 address3 address4 --PORT 15001 15002 15003 15004 --IP localhost localhost localhost localhost --DEBUG debuglevel


4 Myo Armbands.
MAAC addresses: address1 address2 address3 address4
PORTS for each respective address: 15001 15002 15003 15004
IP Addresses: localhost localhost localhost localhost

After running, data from the Myo armbands will be streaming over bluetooth to the IP addresses and ports set from the command line. 

IMPORTANT NOTE: Since noble cannot create multiple connections at once, although it search and connect to various devices simultaneously, only one instance of this program can be running from a device. 
Either list all devices in the single command, or end the program, and write a new command when adding new devices. 