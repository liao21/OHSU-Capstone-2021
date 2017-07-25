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
		
Example: node myo_udp --n 4 --ADD address1 address2 address3 address4 --PORT 15001 15002 15003 15004 --IP localhost localhost localhost localhost


4 Myo Armbands.
MAAC addresses: address1 address2 address3 address4
PORTS for each respective address: 15001 15002 15003 15004
IP Addresses: localhost localhost localhost localhost