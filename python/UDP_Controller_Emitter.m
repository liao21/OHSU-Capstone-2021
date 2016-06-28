% Send controller data via UDP
% Matlab packs data 

j = JoyMexClass;
j.getdata;
a = PnetClass(3452,5005,'192.168.56.101');
a.initialize;

% Determine endianness of the machine and send to reciever.
[str, maxsize, endian] = computer; % may need to swapbytes() if python/matlab disagree
if endian == 'L'
    %send code to run in little endian mode
    a.putData([255 uint8('E') uint8('little')])
elseif endian == 'B'
    %send code to run in big endian mode
    a.putData([255 uint8('E') uint8('big')])
else
    errordlg('Unknown system architecture. Using default configuration.')
end

%change in future use so that option is selectable
joystickType = 'Default'; %setup arrays to determine which vector indexes get filtered.
a.putData([255 uint8('T') uint8(joystickType)]) %send joystick selection to reciever
% joystickType = a.getData()? Want to set joystickType to contain current setting

if strcmp(joystickType, 'SNES')
    btns = [1:8];
    axes = [2 1];
elseif strcmp(joystickType, 'Playstation')
    btns = [1:12];
    axes = [2 1 4 3 6 5];
elseif strcmp(joystickType, 'Unknown') % catch all case
    btns = [1:128];
    axes = [2 1 4 3 6 5];
else %default case (equivalent to SNES controller)
    btns = [1:8];
    axes = [2 1];
end
%%
StartStopForm([]); 
while StartStopForm 
    j.getdata;
    
    btn0 = binvec2dec(j.buttonVal(btns));
    btn0 = typecast(uint64(btn0),'uint8');
    btn0 = btn0(1:ceil(length(btns)/8));
    axis0 = typecast(int16(j.axisVal(axes)*(2^15-1)),'uint8');
    
    msg = uint8([length(btns) btn0 length(axes) axis0]);
    a.putData(msg); 
    
    disp(msg);
    
    drawnow; 
end

%a.putData([255 uint8('Q')]) % interrupt code to quit running UDP reciever