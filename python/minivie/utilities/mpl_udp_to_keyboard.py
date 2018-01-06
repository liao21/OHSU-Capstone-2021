import keyboard
from utilities import Udp
from mpl import JointEnum

# Simple program to control keyboard with PythonVIE and Myo bands
#
# The scenario should be set to NfuUdp as this follows the VulcanX MUD data protocol
#
# Set the mapping of arm motion to keyboard events below
#
# Press ESC to regain control and terminate program
#
# Revisions:
#   29DEC2017 Armiger: Created


def mud_to_keyboard(bytes):
    import struct

    RIGHT_ARM = False

    velocity = [0.0] * 27
    length = len(bytes)
    # print(length)
    if length == 108:
        # Unity position command
        # print(len(raw_chars))
        angles = struct.unpack("27f", bytes)

    if length == 329:
        # Vulcan X PVI command
        values = struct.unpack("HBB81fB", bytes)
        angles = values[3:30]
        velocity = values[30:57]
        impedance = values[57:84]

    if length == 221:
        # Vulcan X PV command
        values = struct.unpack("HBB54fB", bytes)
        angles = values[3:30]
        velocity = values[30:57]

    if velocity[JointEnum.WRIST_FE] > 0:
        print('Wrist Flex')
        if RIGHT_ARM:
            keyboard.press('left')
            keyboard.release('right')
            keyboard.release('space')
        else:
            keyboard.press('right')
            keyboard.release('left')
            keyboard.release('space')
    elif velocity[JointEnum.WRIST_FE] < 0:
        print('Wrist Extend')
        if RIGHT_ARM:
            keyboard.press('right')
            keyboard.release('left')
            keyboard.release('space')
        else:
            keyboard.press('left')
            keyboard.release('right')
            keyboard.release('space')

    elif velocity[JointEnum.MIDDLE_MCP] > 0:
        print('Hand Close')
        keyboard.press('space')
        keyboard.release('left')
        keyboard.release('right')
    else:
        print('RELEASED')
        keyboard.release('left')
        keyboard.release('right')
        keyboard.release('space')


def main():
    import time

    # create object and start
    udp = Udp()
    udp.name = 'MplUdpKeyboard'
    udp.timeout = 0.5
    udp.onmessage = mud_to_keyboard

    # Add a bail out key to terminate emulation
    keyboard.add_hotkey('esc', lambda: udp.close())

    for i in reversed(range(3)):
        print('Starting in {} seconds'.format(i+1))
        time.sleep(1.0)

    udp.connect()


if __name__ == "__main__":
    main()


