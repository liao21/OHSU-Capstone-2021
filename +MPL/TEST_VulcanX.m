% Simple test program to create communications interface between matlab and
% the JHU/APL Virtual Integration Environment
% 
% Requires the MiniVIE development environment:
% git clone https://bitbucket.org/rarmiger/minivie.git
%
% See also: TEST_VulcanX_Endpoint

hSink = MPL.MplVulcanXSink;
hSink.setPortDefaults();
hSink.initialize()

upperArmAngles = zeros(1,7);
handAngles = zeros(1,20);

%% Specify joint angles and transmit bytes
upperArmAngles(1) = 0.3;
upperArmAngles(4) = 0.9;
hSink.putData([upperArmAngles handAngles]);

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Controlling Hand via ROC
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Specify joint angles and ROC command
graspId = 1;
graspValue = 0.5;
upperArmAngles(1) = 0.3;
upperArmAngles(3) = 0.0;
upperArmAngles(4) = 1;
msg = hSink.hMud.ArmPosVelHandRocGrasps(upperArmAngles,zeros(1,7),1,graspId,graspValue,1);
hSink.hUdp.putData(msg);

%% Specify joint angles using MiniVIE ROC command (user editable)
localRoc = MPL.RocTable.createRocTables();
graspId = 2;
graspValue = 0.8;
roc = localRoc(graspId+1);
handAngles = interp1(roc.waypoint,roc.angles,graspValue);
upperArmAngles(1) = 0.3;
upperArmAngles(3) = 0.3;
upperArmAngles(4) = 1.3;
msg = hSink.hMud.AllJointsPosVelCmd(upperArmAngles,zeros(1,7),handAngles,zeros(1,20));
hSink.hUdp.putData(msg);
