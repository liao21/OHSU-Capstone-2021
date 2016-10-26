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
hTactors.tactorVals = [0 0 0 0 0];
hTactors.transmit


%% Setup Wireless TPS
obj = WirelessFingerTPS.getInstance;

% get input linearization ranges
minMaxSensor.thumb = [200 10000];
minMaxSensor.index = [200 10000];
minMaxSensor.middle = [200 10000];
minMaxSensor.ring = [200 10000];
minMaxSensor.little = [200 10000];

% this is the output range
minMaxTactor = [0 255];

% label the sensors
thumbSensor = 1;
indexSensor = 2;
middleSensor = 3;
ringSensor = 4;
littleSensor = 5;

%% Control loop 


StartStopForm([])

while StartStopForm
    drawnow
    
    sensorData = obj.getdata(); % returns 12x1
    % do some mapping
    outputData = sensorData(1:5);
    
    % bound the input vals from 0 to 1
    outputData(thumbSensor) = (outputData(thumbSensor) - minMax.thumb(1)) ./ diff(minMax.thumb);
    outputData(indexSensor) = (outputData(indexSensor) - minMax.index(1)) ./ diff(minMax.index);
    outputData(middleSensor) = (outputData(middleSensor) - minMax.middle(1)) ./ diff(minMax.middle);
    outputData(ringSensor) = (outputData(ringSensor) - minMax.ring(1)) ./ diff(minMax.ring);
    outputData(littleSensor) = (outputData(littleSensor) - minMax.little(1)) ./ diff(minMax.little);
    
    % now bound everything to minMaxTactor bounds
    outputData = max(min(outputData, 1), 0) * diff(minMaxTactor) + minMaxTactor(0);
    disp(outputData');
   
    % do some range checking
    hTactors.tactorVals = outputData([thumbSensor, indexSensor, middleSensor, ringSensor, littleSensor]);
    hTactors.transmit();
    
    pause(0.02)
    
end

%% hTactors
hTactors.close
