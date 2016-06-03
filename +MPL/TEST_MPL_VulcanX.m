% Simple test program to create communications interface between matlab and
% the JHU/APL Virtual Integration Environment
% 
% Requires the MiniVIE development environment
% git clone https://bitbucket.org/rarmiger/minivie.git


%% Quick test of vMPL / MPL control via VulcanX
%  Create the udp transmission via pnet
UdpLocalPort = 22000;
UdpDestinationPort = 9027; %9024 = Left; 9027 = Right; 
UdpAddress = '127.0.0.1'; 

% PnetClass(localPort,remotePort,remoteIP)
hSink = PnetClass(UdpLocalPort,UdpDestinationPort,UdpAddress);
hSink.initialize()

% Create the command encoder which translates joint angles to
% command bytes
mce = MPL.MudCommandEncoder;
upperArmAngles = zeros(1,7);
handAngles = zeros(1,20);

%% Specify joint angles and transmit bytes
upperArmAngles(1) = 0.3;
upperArmAngles(4) = 0.9;
msg = mce.AllJointsPosVelCmd(upperArmAngles,zeros(1,7),handAngles,zeros(1,20));
hSink.putData(msg);

%% Specify joint angles and ROC command
graspId = 1;
graspValue = 0;
upperArmAngles(1) = 0.3;
upperArmAngles(3) = 0.0;
upperArmAngles(4) = 1;
msg = mce.ArmPosVelHandRocGrasps(upperArmAngles,zeros(1,7),1,graspId,graspValue,1);
hSink.putData(msg);
