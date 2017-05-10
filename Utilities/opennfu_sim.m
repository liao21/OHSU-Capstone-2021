% Open NFU heartbeat simulator
a = PnetClass(9027, 9028, '127.0.0.1');
a.initialize()

%%
while StartStopForm
    drawnow
    msg = [
        typecast(uint16(22),'uint8')' % length
        uint8(203) % msgID
        uint8(1) % nfu_state
        uint8(1) % lc_software_state
        uint8([1 2 3 4 5 6 7])' % lmc_software_state
        typecast(single(22.34),'uint8')' % bus_voltage
        typecast(single(50.2),'uint8')' % nfu_ms_per_CMDDOM
        typecast(single(50.1),'uint8')' % nfu_ms_per_ACTUATEMPL
        ];
    a.putData(msg)
    pause(1.0)
end