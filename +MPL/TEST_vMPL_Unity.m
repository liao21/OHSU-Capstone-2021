% TEST_vMPL_Unity
% See also: MPL.EnumArm for a list of joint enumerations
hSink = MPL.MplUnitySink();
hSink.setPortDefaults()
% hSink.MplLocalPort = 9999
hSink.initialize()

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
