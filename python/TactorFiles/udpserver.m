udp_port = 12001;
ip = '10.113.64.96';

udp = pnet('udpsocket', udp_port);
pnet(udp,'udpconnect', ip, udp_port);

figHandle = figure;
drawnow;
while ishandle(figHandle),
    newData = input('Enter angle measures (1-180): ', 's');
    pnet(udp,'write', newData);
    pnet(udp,'writepacket');
    pause(0.01);
    drawnow;
end

pnet(udp,'close');