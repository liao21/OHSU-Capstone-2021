How to use UDP controller:
1. run UPD_Controller_Reciever.py
2. ensure that controller is plugged in
3. run UDP_Controller_Emitter in MATLAB
controller should be streaming data

When run with zero input arguements, UDP_Controller_Reciever.py will default to a SNES style controller interface. An case sensitive command line argument can be used to specify the type of controller to use.

Supported Controller types. 
-Default
-NES
-SNES
-N64*
-Gamecube*
-Genesis
-Playstation
-Xbox*
-Unknown*

*these controlles currently exibit buggy/unstable behavior when test input is sent to them.

SNES and Default are identical. If an unrecognized argument is used, the program will default to Default. The Unknown controller type can be used for any controller not currently implemented. Unknown supports up to 64 axes and 255 buttons (in actuallity, only 254 buttons are available as a leading byte of 255 is reserved for the interrupt signal). Unknown does not guarantee a correct button layout and assumes the user will remap the buttons and axes in whatever application the controller is being used.

The controller type can also be set via UDP with an interrupt command from MATLAB (or any other source). At the moment, the MATLAB code automatically sends this command, setting the controller type to Default (which will overwrite any command-line inputs in the python UDP Receiver). The type MATLAB sets can be changed by changing the MATLAB line:

    "joystickType = 'Default';"
    to
    "joystickType = '<controller_type>';"

in order to prevent MATLAB from sending the interrupt signal to change controller types, comment out the line a.putData([255 uint8('T') uint8(joystickType)])" underneath the "joystickType = " line. In the future, this functionality should be moved to a more unified location so that the user can easily select which controller type they want. Ideally it would be controlled in a drop down menu of a GUI controlling the process.



Interrupt codes
send data with first byte 255 to use interrupt code
-'Q' quit UDP receiver
-'T' set controller type. include string of new controller after code
-'E' check if there is a mismatch between the endianness of the host and reciever

Note that the MATLAB script will automatically end the python UDP Reciever when it completes if the last line is uncommented. This line sends the quit interrupt code. The UDP Receiver can continue to receiver data, and the MATLAB script can be re-run seamlessly if this line is commented out.



Data format for receiver:
The UDP Reciever expects the following format for controller data

    # of buttons, button values, # of axes, axes values

"# of buttons": is a single byte containing the number of buttons the controller has.

"button values": one or more bytes containing the controller button data as corrisponding binary bits. the first button is the least significant bit, and the last is the most significant bit. the number of bytes expected by the reciever is ceiling(#number of buttons % 8). The receiver can handle a number of buttons that is not a multiple of 8, and any buttons that do not fit in a full byte should be send as if the rest of the buttons in that byte are zero.

    e.g. A controller with 12 buttons could send a byte like this: 01001101 00001101
    This reprisents the following button presses: 1st, 3rd, 4th, 7th, 9th, 11th, 12th.

"# of axes": is a byte of the number of axes that the controller has. Generally each stick has two axes.

"axes values": linux uinput recognizes axis inputs in the range of [-32767, 32767] inclusive (2^15-1 = 32767). Hence each axis value should be stored as two consecutive bytes reprisenting a 16-bit axis value. All byte values read in the data must be unsigned, so negative axis values must be packed as unsigned integers (i.e. the two's compliment), and then the reciever will unpack them into back into signed integers. The number of bytes expected by the receiver is (# of axes * 2).


A first byte value of 255, \b11111111, or \xff is reserved as the interrupt signal. Packets beginning with this number, followed by an interupt code letter (as a byte in ascii format) will cause the reciever to perform one of the various interrupt operations listed above.

    e.g. the packet '\xffTPlaystation' would cause the receiver to reset the controller type settings to those of a Playstation controller.
    e.g. the packet '\xffQ' would cause the reciever to quit operations
    e.g. the packet '\xffElittle' would tell the reciever that the axis data bytes are in little endian mode and would cause the receiver to check for an endian mismatch
    e.g. the packet '\x0c\b01001101\b00001101\x06\x7f\xff\x80\x01\x00\x00\xff\xff\xab\xcd' is a valid input state for a controller with 12 buttons and 6 axes.
