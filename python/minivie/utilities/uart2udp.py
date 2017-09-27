import serial
import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

ser = serial.Serial('/dev/ttymxc3', 115200, timeout=2.0)

# clear buffer
while ser.in_waiting:  # Or: while ser.inWaiting():
    print(ser.read(100))
print('Buffer Clear\n')

pckt_sz = 221
pckt_cnt = 0

while True:
    # assume newbytes create new packet
    pckt = ser.read(pckt_sz)
    if len(pckt) > 0:
        sock.sendto(pckt, ('localhost', 9027))
        print(pckt)
        pckt_cnt += 1
        print( 'Read {}\n'.format(pckt_cnt) )
        chk_sum = sum(pckt[:-1])%256
        if chk_sum == pckt[-1]:
            print( 'Checksum Valid {}\n'.format(chk_sum ) )
        else:
            print( 'Checksum Invalid {} not {}\n'.format(chk_sum,pckt[-1] ) )
    else:
        print('No Data')
        time.sleep(1.0)


