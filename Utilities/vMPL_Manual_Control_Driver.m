% RUN vMPL_Manual_Control_GUI.m in order to use the GUI

varType = 'uint8';

%range in degrees that the upperArmAngles can attain
range = [215 -160 135 150 180 60 120];
%offset from 0 that the upperArmAngles minimum value can attain
offset = [-40 0 -45 0 -90 -15 -60];
%slider position for zero
initial = -offset./range;

%convert to radians
range = degtorad(range);
offset = degtorad(offset);

%approximate hand angles for the various grips in radians
Tip = [0 1 1 1 0.1 1.1 1.1 1 0 1 1 1 1 1.1 1.3 1 1.5 0 1.5 1];
Lateral = [0 1 1 1 0.1 1.1 1.1 1 0 1 1 1 1 1.1 1.3 1 0.7 0.7 0.7 0.7];
%Cylindrical = [0 1.2 1.2 1.2 0 1.2 1.2 1.2 0 1.1 1.2 1.2 0 1 1.2 1.2 1.5 0.3 1.4 0];
Cylindrical = [0 1.4 1.4 1.4 0 1.4 1.4 1.4 0 1.4 1.4 1.4 0 1.4 1.4 1.4 1.5 0.3 1.4 0];

% Set which hand to use. true for left hand, false for right hand
leftHand = true;

% Create a UDP interface object
UdpLocalPort = 56789;
if leftHand
    UdpDestinationPort = 25100; % 25100 = Left; 25000 = Right;
else
    UdpDestinationPort = 25000;
end
UdpAddress = '127.0.0.1'; % IP address of VulcanX '127.0.0.1';
hArm = PnetClass(UdpLocalPort,UdpDestinationPort,UdpAddress);
hArm.initialize();

% Create variables to store MPL actuator angles
upperArmAngles = zeros(1,7);
handAngles = zeros(1,20);


%vMPL_Manual_Control_GUI;