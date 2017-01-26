import socket
import struct
import sys
import traceback
import thread
import time


#input messages are delimeted by spaces
#integers are converted to bytes
#example input messages: 
#   "ts 255" becomes "\0x74\0x73\0xFF" ("ts\0xFF")
#   "pm infinity" becomes "\0x70\0x6D\0x69\0x6E\0x66\0x69\0x6E\0x69\0x74\0x79" ("pminfinity")
#UDP cues recieved from the specified port are displayed as well

UDP_IP = "127.0.0.1"
UDP_SENDTO_PORT = 8051
UDP_RECFROM_PORT = 8050
    
def main():
    MESSAGE = ""

    print('UDP target IP: ' + UDP_IP)
    print('UDP target port: ' + str(UDP_SENDTO_PORT))
    print('')

    message = ''

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


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
                        
                sock.sendto(message, (UDP_IP, UDP_SENDTO_PORT))
                print('Message "' + message + '" sent.\n')
            else:
                print('\nQuitting the program')
                sock.sendto('q', (UDP_IP, UDP_SENDTO_PORT))
                sock.sendto('q', (UDP_IP, UDP_RECFROM_PORT))
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
        time.sleep(0.05)     #wait for any UDP cues recieved to be printed
                    
def listener():
    #listen to any UDP cues recieved from the target

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_RECFROM_PORT))
    
    data = ''
    
    while data != 'q':
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        if sys.version_info[0] == 2:
            print('Received packet: "' + str(data) + '"')
        elif sys.version_info[0] == 3:
            print('Received packet: "' + str(data)[12:-2] + '"')
        
                    
if __name__ == "__main__":
    thread.start_new_thread(listener, ())
    main()
    
        