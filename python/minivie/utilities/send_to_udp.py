import socket
import struct
import sys
import traceback

UDP_IP = "127.0.0.1"
UDP_PORT = 8051
MESSAGE = ""

print('UDP target IP: ' + UDP_IP)
print('UDP target port: ' + str(UDP_PORT))
print('')

message = ''

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#input messages are delimeted by spaces
#integers are converted to bytes
#example input messages: 
#   "ts 255" becomes "\0x74\0x73\0xFF" ("tm\0xFF")
#   "pm infinity" becomes "\0x70\0x6D\0x69\0x6E\0x66\0x69\0x6E\0x69\0x74\0x79" ("pminfinity")

while True:
    try:
        print('("quit" to quit)')
        if sys.version_info[0] == 2:
                input = raw_input('Message to send: ')
        elif sys.version_info[0] == 3:
                input = input('Message to send: ')
        
        if input.lower() != 'quit' and input.lower() != 'q':
            message = ''
            for token in input.split(' '):
                print('token: ' + token)
                if token.isdigit():
                    message = message + struct.pack('B', int(token))
                else:
                    message = message + token
                    
            sock.sendto(message, (UDP_IP, UDP_PORT))
            print('Message "' + message + '" sent.\n')
        else:
            print('\nQuitting the program')
            sock.sendto('q', (UDP_IP, UDP_PORT))
            sock.close()
            quit()
    except Exception as err:  # print the exception, and continue running UDP flow control loop
            try:
                exc_info = sys.exc_info()
            finally:
                print('\nError occured in execution loop.')
                traceback.print_exception(*exc_info)
                print('')
                del exc_info
    