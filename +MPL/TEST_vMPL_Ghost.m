% TEST_vMPL_Unity
% See also: MPL.EnumArm for a list of joint enumerations
hSink = MPL.MplUnitySink();
hSink.MplAddress = '127.0.0.1';
hSink.MplCmdPort = 25000;
hSink.MplLocalPort = 25001;
hSink.initialize();hSink.initialize()

%%
ang = zeros(1,27);
ang(1) = 32*pi/180;
ang(2) = -13*pi/180;
ang(3) = 17*pi/180;
ang(4) = 63*pi/180;

hSink.putData(ang)

%%
%The new Ghost Limb port numbers are 25010 (left) and 25110 (right).
hSinkGhost = MPL.MplUnitySink();
hSinkGhost.MplAddress = '127.0.0.1';
hSinkGhost.MplCmdPort = 25110;
hSinkGhost.MplLocalPort = 25111;
hSinkGhost.initialize();

%%
ang = zeros(1,27);
ang(1) = 66*pi/180;
ang(2) = -13*pi/180;
ang(3) = 17*pi/180;
ang(4) = rand(1);
hSinkGhost.putData(ang)


% You can now change both the color of the ghost limbs and if they should
% be enabled/disabled using the CONFIG file or using UDP communication.
% The port to send the color and enable/disable values to is: 27000  
%
% The enable/disable should be sent first: 1.0 == enabled,  0.0 == disabled
% 
% The color values should be sent next (R,G,B,A in this order) which need
% to be between 0.0-1.0 since unity determines color on a 0-1 scale instead
% of a 0-256 scale.  
% 
% If you would like any other features to be added or run into any issues
% please let me know.  
% 

%%
hP = PnetClass(12234,27000);
hP.initialize()
%%
hP2 = PnetClass(12234,27100);
hP2.initialize()

%%

c1 = uisetcolor;

hP.putData(typecast(single([1.0, c1, 0.8]),'uint8'))

c2 = uisetcolor;
hP2.putData(typecast(single([1.0, c2, 0.8]),'uint8'))







%% Synch Current position and target position
perceptData = hSink.getPercepts();
jointAngles = perceptData.jointPercepts.position; %radians
hSink.putData(jointAngles);

%% Smooth Home
hSink.gotoSmooth([0.1 -0.5 0.2 1.9 0.1 0.0 0.0]);

%%
hSink.gotoSmooth([0.5 -0.5 0.2 0.9 0.1 0.0 0.0]);

%%
ang = zeros(1,27);
ang(1) = 37*pi/180;
ang(2) = -13*pi/180;
ang(3) = 17*pi/180;
ang(4) = 63*pi/180;

hSink.putData(ang)
