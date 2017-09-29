% Create Arm and Roc Grasp Command and send to OpenNFU
hSink = PnetClass(9028, 9027,'192.168.7.2');
hSink.initialize();
%hSink.enableLogging = true;
mce = MPL.MudCommandEncoder;
structRoc = MPL.RocTable.readRocTable('WrRocDefaults.xml');
mplAngles = zeros(1,27);

%% Send P[V] Command
mplAngles(MPL.EnumArm.ELBOW) = 0;
mplAngles(MPL.EnumArm.WRIST_FE) = 0;
mplAngles(MPL.EnumArm.WRIST_ROT) = 0;
rocValue = min(max( 0 ,0),1);
rocId = 8;
fprintf('Hand Shape: "%s" %d%%\n',structRoc(rocId).name,rocValue*100);
mplAngles(structRoc(rocId).joints) = interp1(structRoc(rocId).waypoint,structRoc(rocId).angles,rocValue);
msg = mce.AllJointsPosVelCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20));
hSink.putData(msg)

hSink.getAllData();

%% Send Impedance Command
mplAngles(MPL.EnumArm.ELBOW) = 2.4;
mplAngles(MPL.EnumArm.WRIST_FE) = -0.0;
rocValue = 0;
rocId = 8;
fprintf('Hand Shape: "%s" %d%%\n',structRoc(rocId).name,rocValue*100);
mplAngles(structRoc(rocId).joints) = interp1(structRoc(rocId).waypoint,structRoc(rocId).angles,rocValue);

stiffnessCmd = [5 5 5 5 1 5 1.5 0.05*ones(1,20)]; % 16 Nm/rad Upper Arm  0.1-1 Hand
msg = mce.AllJointsPosVelImpCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20),stiffnessCmd);
hSink.putData(msg)

%% Send limb to idle
UDPMSGID_NFU_IDLE = 10;
msg = mce.CreateCmdMessage(UDPMSGID_NFU_IDLE, cast(UDPMSGID_NFU_IDLE, 'uint8'));
hSink.putData(msg)

%% soft_reset
UDPMSGID_NFU_SOFTRESET = 11;
bytes = mce.CreateCmdMessage(UDPMSGID_NFU_SOFTRESET, cast(UDPMSGID_NFU_SOFTRESET, 'uint8'));
hSink.putData(bytes);

%% Save data log
%hSink.saveLog('test.log')
