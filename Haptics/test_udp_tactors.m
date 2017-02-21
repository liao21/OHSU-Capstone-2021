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

%% home the tactor and set max angle

hTactors.maxAngle = 45; % in degrees
hTactors.tactorVals = zeros(1,5) + 255;

%% this is code for a 1000-cycle test, it goes from home (255 in this config)
% to 66% deflection of max angle (set above to 45)
for loop = 1 : 1000
    hTactors.tactorVals(3) = 255;
    pause(0.2);
    hTactors.tactorVals(3) = fix(255/3);
    pause(0.2);
end
hTactors.tactorVals(3) = 255;

%% quick code block to deliver arbitrary deviation to the motors
% this particular code drives 3rd motor, assumes that the motors is at home
% at 255
dx = 160;
hTactors.tactorVals = zeros(1,5) + 120;
pause(0.3);
for dx = 120:-1:85
    hTactors.tactorVals(3) = 255 - dx;
    pause(0.05);
end
pause
hTactors.tactorVals(3) = 120;

%% this is a quick code block for a level discrimination
% change 'order' to determine which one is delivered first

order = 2;
d1 = 100;
d2 = 150;

if order == 1
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.2);
    hTactors.tactorVals(3) = 255 - d1;
    pause(0.2);
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.4);
    
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.2);
    hTactors.tactorVals(3) = 255 - d2;
    pause(0.2);
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.4);
    
else
    
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.2);
    hTactors.tactorVals(3) = 255 - d2;
    pause(0.2);
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.4);
    
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.2);
    hTactors.tactorVals(3) = 255 - d1;
    pause(0.2);
    hTactors.tactorVals = zeros(1,5) + 255;
    pause(0.4);
end
%% CLOSE THE TACTORS
try
hTactors.close
end
run('cleanup.m');