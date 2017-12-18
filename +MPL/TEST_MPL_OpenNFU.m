%%

% Create Arm and Roc Grasp Command and send to OpenNFU
hSink = PnetClass(9028, 9027,'192.168.7.2');
hSink.initialize();
hSink.enableLogging = true;
mce = MPL.MudCommandEncoder;
structRoc = MPL.RocTable.readRocTable('WrRocDefaults.xml');

%% Get arm current position:
msg = hSink.getAllData();
lastPerceptId = find(cellfun(@length,msg) == 879,1,'last');
if isempty(lastPerceptId)
    error('Percepts not found.  Check MPL Connection')
end

lastPercept = msg{lastPerceptId};
data = extract_mpl_percepts_v2(lastPercept);
mplAngles = double(data.jointPercepts.position)

%% Command arm to the current position to synch

msg = mce.AllJointsPosVelCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20));
hSink.putData(msg)



%% Send P[V] Command
mplAngles(MPL.EnumArm.ELBOW) = 100*pi/180;
mplAngles(MPL.EnumArm.WRIST_FE) = -35*pi/180;
mplAngles(MPL.EnumArm.WRIST_ROT) = 60*pi/180;
rocValue = min(max( 0.7 ,0),1);
rocId = 8;
fprintf('Hand Shape: "%s" %d%%\n',structRoc(rocId).name,rocValue*100);
mplAngles(structRoc(rocId).joints) = interp1(structRoc(rocId).waypoint,structRoc(rocId).angles,rocValue);
msg = mce.AllJointsPosVelCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20));
hSink.putData(msg)

hSink.getAllData();

%% Send Impedance Command
mplAngles(MPL.EnumArm.ELBOW) = 100*pi/180;
mplAngles(MPL.EnumArm.WRIST_FE) = -35*pi/180;
mplAngles(MPL.EnumArm.WRIST_ROT) = 60*pi/180;
rocValue = 14 / 20;
rocId = 8;
fprintf('Hand Shape: "%s" %3.0f%%\n',structRoc(rocId).name,rocValue*100);
mplAngles(structRoc(rocId).joints) = interp1(structRoc(rocId).waypoint,structRoc(rocId).angles,min(max( rocValue ,0),1));

stiffnessCmd = [40 40 40 20 3 40 5 0.2*ones(1,20)]; % 16 Nm/rad Upper Arm  0.1-1 Hand
rezeroTorque = 0;
if rezeroTorque
    stiffnessCmd(8:end) = 15.6288
end

msg = mce.AllJointsPosVelImpCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20),stiffnessCmd);
% msg = mce.AllJointsPosVelCmd(mplAngles(1:7), zeros(1,7), mplAngles(8:27), zeros(1,20));
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







%%  Create a percept recording for simulator
clc
hSink.getAllData();
cellMsg = {};
tic
for i = 1:500
    pause(0.02)
    msg = hSink.getData();
    cellMsg = cat(1,cellMsg,msg);
end
toc


%%
clc
fp = fopen('nfu_event_sim.csv','w');
for i = 1:length(cellMsg)
    fprintf(fp,'%02x,',cellMsg{i});
    fprintf(fp,'\n');
end
fclose(fp);





%%
return

% Create connection to MPL using VulcanX protocol

hSink = MPL.MplVulcanXSink;
hSink.MplAddress = '192.168.7.2';
hSink.MplCmdPort = 9027;
hSink.MplLocalPort = 9028;
hSink.initialize();

%%


hSink.gotoSmooth()


return
