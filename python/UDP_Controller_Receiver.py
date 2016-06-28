## UDP controller receiver for python
## By David Samson
## 
## June 28, 2016


import uinput
import socket
import sys
import struct
import math
import random
import time

def main():
    """Run UDP controller receiver. Controller data received as bytearrays will be emitted to the system.

    Command-line arguments:
    controller_type -- type of controller to listen for. Currently supports SNES, Playstation, Unknown
    -- if no argument or an incorrect argument is used, system defaults to Default (SNES equivalent)

    UDP interrupt codes:
    The following codes will cause the receiver to interrupt control data processing
    '\xffQ' -- quit running server
    '\xffE<source_endianness>' -- check if host and source have matching endian types.
    -- <source_endianness> can be 'little' or 'big' specify the endianness of the source
    '\xffT<controller_type>' -- set current controller type to <controller_type>.
    -- <controller_type> is a case sensitive string with the name of a valid controller type.
    -- if no arguement or an incorrect argument is used, system defaults to Default (SNES equivalent)
    """

    #set debug = True to run debug mode tests
    debug = False
    if debug:
        print('Running debug tests.')
        #run tests before running
        passed = True
        passed = passed and test_pack_unpack()

        test_control_input('')
        test_control_input('Default')
        test_control_input('NES')
        test_control_input('SNES')
        test_control_input('N64')
        test_control_input('Gamecube')
        test_control_input('Genesis')
        test_control_input('Playstation')
        test_control_input('Xbox')
        #test_control_input('Unknown') #slow and takes control of mouse/system.

        if not passed:
            print('Errors encountered in debug testing. Quitting program.')
            quit()
        else:
            print('No errors encountered. Proceeding to main program.\n')
            

            
    endianness = sys.byteorder
    same_endian = True  # is the python byte order the same as the matlab byte order?
                        # will be checked with interrupt code at matlab initialization
    
    controller_type = sys.argv[1] if len(sys.argv) > 1 else 'Default' 
    btn_events, axis_events, controller_type = setup_controller(controller_type)

    # Setup UDP Receiver
    #UDP_IP = "127.0.0.1"
    UDP_IP = "192.168.56.101"
    UDP_PORT = 5005
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print('UDP Controller Reciever has started.')
    print('IP Address: ' + str(UDP_IP))
    print('Port: ' + str(UDP_PORT) + '\n')

    # UDP reciever and control input emission section
    
    while True: #outer while loop allows for resetting controller type
        with uinput.Device(btn_events + axis_events) as device:
            while True:
                #inner while loop receives UDP data
                #control inputs may be made in here
                
                data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
                #print("received message: ",  data)

                data = bytearray(data)

                if data[0] != 255 : # if non-interrupt data is recieved
                    [btns,axes] = unpack(data)
                    #print(str(btns)+str(axes))
                    emit_controller(device, btn_events,axis_events,btns,axes)

                    
                #handle interrupt data
                else:
                    print('recieved interrupt code: ', data)
                    if len(data) > 1:
                        
                        if data[1] == ord('Q'): #quit
                            print('Quitting UDP Controller Reciever.\n')
                            quit()

                        elif data[1] == ord('T'): #set controller type
                            if ''.join([chr(i) for i in data[2:]]) != controller_type:
                                btn_events, axis_events, controller_type = setup_controller(
                                    ''.join([chr(i) for i in data[2:]]) #get controller type from data
                                )
                                print('Set controller type to: ' + controller_type)
                                print('Resetting reciever with new controller settings\n')
                                break #end inner loop to resetup controller
                            
                        elif data[1] == ord('E'): #check endianness. WIP (no fixes performed if mismatch)
                            if ''.join([chr(i) for i in data[2:]]) != endianness:
                                print('Mismatching endian types. Modifying unpack sequence to compensate.\n')
                                same_endian = False
                            else:
                                same_endian = True

                        else:
                            print('unrecognized interrupt code: "' + chr(data[1]) + '"')
                    else:
                        print('error reading interrupt code')
                        
    return





def emit_controller(device, btn_events, axis_events, btn_inputs, axis_inputs):
    """Emits inputted button presses/axis positions to the system
    
    Keyword arguments:
    device -- the virtual controller constructed by the UDP receiver. 
    btn_events -- list of all buttons that belong to device
    axis_events -- list of all axes that belong to device
    btn_inputs -- list of buttons' states. 0 reprisents unpressed, 1 represents pressed
    axis_inputs -- list of axes' positions. valid values are integers ranging from -32767 to 32767

    System input:
    button events and axis positions are emitted to the system as the device passed in.
    --If there is a mismatch in the number of elements of the device events and input array,
      then the number of inputs will be set to the shorter of the two.
      This is to attempt to handle non-standard input cases with preset controller setups.
    
    """
    num_btns = min(len(btn_events),len(btn_inputs))
    num_axes = min(len(axis_events),len(axis_inputs))
    
    for i in list(range(num_btns)):
        device.emit(btn_events[i], btn_inputs[i])
        
    for i in list(range(num_axes)):
        device.emit(axis_events[i], axis_inputs[i])
            
    return




def setup_controller(type):
    """Create the skeleton for the virtual controller interface based on specific controller types. 
    
    Keyword arguments:
    type -- a string containing the type of controller to setup
    -- if an incorrect or empty string is specified, the system default setup is Default (SNES equivalent)
    
    Return arguments:
    A list containing the items listed below is returned from this function
    uinput_btns list -- uinput reprisentation of all buttons contained by particular controller type
    uinput_axes list -- uinput reprisentation of all axes contained by particular controller type
    controller_type -- string specifying the controller type setup
    -- normally this is the same as input 'type' except in cases where setup of type specified fails

    Notes:
    To add a new controller type, make a set of tuples containing the uinput buttons and axes wanted,
    --then add the new controller to the dictionary that returns the controller selected by type
    A list of available buttons, keystrokes and axes is available at:
    --https://github.com/tuomasjjrasanen/python-uinput/blob/master/src/ev.py
    button or axes lists can also be generated with their numeric values, as in how Unknown is setup
    --WARNING, this is not recommended, and may produce unexpected behavior
    Some controllers are buggy when they have test input sent to them
    --this might be fixed by swapping the particular button or axis events with different ones.
    """

    
    #default button event codes (equivalent to SNES)
    default_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_X,
        uinput.BTN_Y,
        uinput.BTN_TL,
        uinput.BTN_TR,
        uinput.BTN_SELECT,
        uinput.BTN_START
    )
    
    #default axis event codes
    default_axes = (
        uinput.ABS_X,
        uinput.ABS_Y    
    )


    #NES button event codes
    NES_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_SELECT,
        uinput.BTN_START,
        uinput.BTN_DPAD_UP,
        uinput.BTN_DPAD_DOWN,
        uinput.BTN_DPAD_LEFT,
        uinput.BTN_DPAD_RIGHT,
    )

    #NES axes event codes
    NES_axes = () # NES controller d-pad are 4 separate buttons, not 2 axes

    
    #SNES buttons
    SNES_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_X,
        uinput.BTN_Y,
        uinput.BTN_TL,
        uinput.BTN_TR,
        uinput.BTN_SELECT,
        uinput.BTN_START
    )

    #SNES axes
    SNES_axes = (
        uinput.ABS_X,
        uinput.ABS_Y        
    )

    #BUGGY
    #Nintendo 64 buttons
    N64_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_X,
        uinput.BTN_Y,
        uinput.BTN_TL,
        uinput.BTN_TR,
        uinput.BTN_Z,
        uinput.BTN_START,
        uinput.BTN_DPAD_UP,
        uinput.BTN_DPAD_DOWN,
        uinput.BTN_DPAD_LEFT,
        uinput.BTN_DPAD_RIGHT,
        uinput.BTN_SOUTH,   #yellow c buttons
        uinput.BTN_EAST,
        uinput.BTN_NORTH,
        uinput.BTN_WEST,
    )

    #Nintendo 64 axes
    N64_axes = (
        uinput.ABS_X,
        uinput.ABS_Y
    )


    #BUGGY
    #Gamecube buttons
    GC_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_X,
        uinput.BTN_Y,
        uinput.BTN_Z,
        uinput.BTN_START,
        uinput.BTN_DPAD_UP,
        uinput.BTN_DPAD_DOWN,
        uinput.BTN_DPAD_LEFT,
        uinput.BTN_DPAD_RIGHT
    )

    #Gamecube axes
    GC_axes = (
        uinput.ABS_X,
        uinput.ABS_Y,
        uinput.ABS_RX,
        uinput.ABS_RY,
        uinput.ABS_Z,    #left trigger
        uinput.ABS_RZ,   #right trigger
    )


    #Sega Genesis buttons
    Genesis_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_C,
        uinput.BTN_TL,
        uinput.BTN_TR,
        uinput.BTN_SELECT,
        uinput.BTN_START,
    )

    #Sega Genesis axes
    Genesis_axes = (
        uinput.ABS_X,
        uinput.ABS_Y
    )

    
    #Sony Playstation buttons (equivalent to Logitech)
    PS_btns = (
        uinput.BTN_TRIGGER,  #square   (0)           
        uinput.BTN_THUMB,    #X        (1)           
        uinput.BTN_THUMB2,   #circle   (2)           
        uinput.BTN_TOP,      #triangle (3)           
        uinput.BTN_TOP2,     #         (4)           
        uinput.BTN_PINKIE,   #         (5)           
        uinput.BTN_BASE,     #         (6)           
        uinput.BTN_BASE2,    #         (7)           
        uinput.BTN_BASE3,    #         (8)           
        uinput.BTN_BASE4,    #         (9)           
        uinput.BTN_BASE5,    #left stick button  (10)
        uinput.BTN_BASE6     #right stick button (11)
    )

    #Sony Playstation axes
    PS_axes = (
        uinput.ABS_X,        #left stick X
        uinput.ABS_Y,        #left stick Y
        uinput.ABS_Z,        #right stick X
        uinput.ABS_RZ,       #right stick Y
        uinput.ABS_HAT0X,    #left D-pad X
        uinput.ABS_HAT0Y     #left D-pad Y
    )


    #BUGGY
    #Xbox 360 buttons
    Xbox_btns = (
        uinput.BTN_A,
        uinput.BTN_B,
        uinput.BTN_X,
        uinput.BTN_Y,
        uinput.BTN_Z,
        uinput.BTN_START,
        uinput.BTN_SELECT,
        uinput.BTN_TL,    #left bumper
        uinput.BTN_TR,    #right bumper
        uinput.BTN_DPAD_UP,
        uinput.BTN_DPAD_DOWN,
        uinput.BTN_DPAD_LEFT,
        uinput.BTN_DPAD_RIGHT
    )

    #Xbox 360 axes
    Xbox_axes = (
        uinput.ABS_X,        #left stick X
        uinput.ABS_Y,        #left stick Y
        uinput.ABS_Z,        #right stick X
        uinput.ABS_RZ,       #right stick Y
        uinput.ABS_HAT0X,    #left trigger
        uinput.ABS_HAT0Y     #right trigger
    )


    #REALLY BUGGY
    #generate 64 axes and 255 buttons for catch all input case
    uknwn_btns_list = list(range(256,256+64)) + list(range(321,321+9)) + list(range(331,331+182))
    Unknown_btns = tuple(tuple([1,i]) for i in uknwn_btns_list)
    Unknown_axes = tuple(tuple([3,i]) for i in list(range(0,64)))
    #may want to modify in the future to contain less buttons/axes. axes 0 and 1 interfere with mouse.

    

    return {
        'NES' : [NES_btns, NES_axes, 'NES'],
        'SNES' : [SNES_btns, SNES_axes, 'SNES'],
        'N64' : [N64_btns, N64_axes, 'N64'],
        'Gamecube' : [GC_btns, GC_axes, 'Gamecube'],
        'Genesis' : [Genesis_btns, Genesis_axes, 'Genesis'],
        'Playstation' : [PS_btns, PS_axes, 'Playstation'],
        'Xbox' : [Xbox_btns, Xbox_axes, 'Xbox'],
        'Unknown' : [Unknown_btns, Unknown_axes, 'Unknown'],
    }.get(type,[default_btns, default_axes, 'Default'])





def unpack(string):
    """Unpack bytearray for use by UDP controller receiver

    Keyword arguments:
    string -- a bytearray containing data to be unpacked

    expected bytearray format of string: b'num_buttons btn_presses num_axes axes_vals'
    num_buttons -- single byte containing the number of buttons the controller has
    btn_presses -- packed byte(s) containing button presses in binary. 1 for pressed, 0 for unpressed
    -- buttons are stored with the first button as the LSB, and the last button as the MSB
    num_axes -- single byte containing the number of axes the controller has
    axes-vals -- bytes containing axis values. Axis values are 16-bit unsigned ints split into two bytes
    -- negative axis values are the two's complement of the signed 16-bit integer

    Return arguments:
    btns -- an integer array representing button presses. 1 for pressed, 0 for unpressed
    axes -- an integer array representing axis positions. values range from -32767 to 32767

    """
    # print bytes for debug
    #print([str(i) for i in string])
    
    l = string[0]
    btns = []
    nb = l//8
    
    string = string[1:len(string)]
    
    for i in list(range(nb)):
        lst = [int(x) for x in format(string[i], '#010b')[2:]]
        lst.reverse()
        btns += lst
        
    if l%8 !=0:
        fmt = '#0' + str(l%8 + 2) + 'b'
        lst = [int(x) for x in format(string[nb], fmt)[2:]]
        lst.reverse()
        btns += lst

    # get axis data from string
    string = string[nb+(l%8!=0):len(string)]
    l = string[0]
    string = string[1:len(string)]

    fmt = '' + str(l) + 'h'
    axes = struct.unpack(fmt,string)

    return (btns, axes)




def pack(btns, axes):
    """Pack buttons and axes into bytearray that can be recieved by UDP controller receiver

    Keyword arguments:
    btns -- an integer array representing button presses. 1 for pressed, 0 for unpressed
    axes -- a signed 16-bit integer array representing axis positions. values range from -32767 to 32767

    Return arguments:
    string -- a bytearray containing packed button and axis data for sending via UDP

    """
    
    #ensure button data is only 1's and 0's
    for i in list(range(len(btns))):
        if btns[i] != 0:
            btns[i] = 1

    
    string = bytearray()
    
    #pack buttons
    nb = len(btns)
    string.append(nb)
    btns_extra = []
    if nb%8 != 0:
        btns_extra = btns[nb - nb%8 : nb]
        del btns[nb - nb%8 : nb]

    for i in list(range(nb//8)):
        buff = btns[0:8]
        del btns[0:8]
        buff.reverse()
        byte = '0b' + ''.join([str(i) for i in buff])
        string.append(int(byte,2))

    if nb%8 != 0:
        buff = btns_extra
        buff.reverse()
        byte = '0b' + ''.join([str(i) for i in buff])
        string.append(int(byte,2))

    #pack axes
    string.append(len(axes))

    for i in axes:
        if i < 0:
            i += 2**16 #convert negative numbers to two's complement
        [string.append(i) for i in (struct.pack('H' , i))]

    return string





def test_pack_unpack():
    """Check if the pack and unpack functions are working properly

    Return arguments:
    working -- a boolean that specifies True if all tests pass, otherwise False
    """
    working = True
    a = pack([1,1,0,1,0,0,0,1,1,1,1,1,1,1,0,1,1,0,1,1,0,0,1,0,1,0,1,0],[3879, 298, 23, 4849, 3212, -6876])
    b = pack([1,1,0,1,1,0,1,1,0,0,1,0],[3879,-6876])
    c = pack([1,1,0,0,1,1],[31])
    d = pack([1,0,1,0,1,0,1,1],[-32767, 32767])
    working = working and (a == pack(unpack(a)[0], unpack(a)[1]))
    working = working and (b == pack(unpack(b)[0], unpack(b)[1]))
    working = working and (c == pack(unpack(c)[0], unpack(c)[1]))
    working = working and (d == pack(unpack(d)[0], unpack(d)[1]))

    return working




def test_control_input(controller_type):
    """emit test signals to all axes and buttons of a specified controller

    Keyword arguments:
    controller_type -- string of what type of controller to setup and emit to system

    Output:
    sample button presses and axis motion is generated and emitted to system as current controller type.
    --output should be observable in jstest.
    --buttons should be pressed sequentially starting at the first button and working forward.
    --axes should be following elipses of random direction and proportions
    WARNING -- run this function for the Unknown type of controller at your own risk.
    -- it is excessively slow, and will probably take control of the system (mouse) away from you
    """

    btn_events, axis_events, controller_type = setup_controller(controller_type)

    
    with uinput.Device(btn_events + axis_events) as device:
        #setup sample input data

        print('Emitting test signals in 5 seconds')
        time.sleep(5)
        
        num_btns = len(btn_events)
        num_axes = len(axis_events)

        btns = [0]*num_btns
        axes = [0]*num_axes

        pi = math.pi

        print('Emitting test control input for ' + controller_type + ' controller')
        
        for i in list(range(100000)):

            axes = [0]*num_axes
            
            if i%10000 == 0:
                mod = [(random.random()*2-1)*32767 for i in list(range(num_axes))]



            cosine = math.cos(i/10000.0*2*pi)
            sine = math.sin(i/10000.0*2*pi)
            
            for j in list(range(num_axes))[:num_axes-1:2]:
                axes[j] = int(cosine * mod[j])
                axes[j+1] = int(sine * mod[j+1])

            #case for even or odd number of axes
            if num_axes >= 2:
                axes[num_axes-2] = int(cosine * mod[num_axes-2])
                if num_axes%2 == 0:
                    axes[num_axes-1] = int(sine * mod[num_axes-1])

            
            btns = [0]*num_btns
            btns[i//1000 % num_btns] = 1


            #emit sample input data
            emit_controller(device, btn_events,axis_events,btns,axes)

    
    return





if __name__ == "__main__":
    main()
