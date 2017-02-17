%% Setup Tactors
% 192.168.1.1:12001 - ServoUDP
% 192.168.1.1:8089
% VibroUDP or TactorUDP
TactorPort = '192.168.1.1:12001'; 
TactorType = 'ServoUDP';

switch TactorType
    case 'ServoUDP'
        hTactors = BluetoothTactor_UDP(TactorPort);
    case 'VibroUDP'
        hTactors = TactorUdp(TactorPort);
    case 'VibroBluetooth'
        hTactors = BluetoothTactor(TactorPort);
end
hTactors.initialize();

%% update via:
hTactors.maxAngle = 90; % in degrees
hTactors.tactorVals = [0 0 0 0 0]; % 0 to 255, corresponds to channels 8-12
hTactors.transmit

%% hTactors
try
hTactors.close
end
run('cleanup.m');