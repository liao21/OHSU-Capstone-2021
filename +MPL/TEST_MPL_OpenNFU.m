% Create Arm and Roc Grasp Command and send to OpenNFU
hSink = PnetClass(22000, 9027,'192.168.7.2');
hSink.initialize();
mce = MPL.MudCommandEncoder;
structRoc = MPL.RocTable.readRocTable('WrRocDefaults.xml');
mplAngles = zeros(1,27);
%%
mplAngles(MPL.EnumArm.ELBOW) = 0;
mplAngles(MPL.EnumArm.WRIST_FE) = -0.1;
rocValue = 0;
rocId = 6;
fprintf('Hand Shape: "%s" %d%%\n',structRoc(rocId).name,rocValue*100);
mplAngles(structRoc(rocId).joints) = interp1(structRoc(rocId).waypoint,structRoc(rocId).angles,rocValue);
msg = mce.AllJointsPosVelCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20));
hSink.putData(msg)