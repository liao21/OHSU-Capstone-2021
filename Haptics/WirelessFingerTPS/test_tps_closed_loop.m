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
hTactors.maxAngle = 60;
hTactors.tactorVals = [0 0 0 0 0];


%% Setup Wireless TPS
obj = WirelessFingerTPS.getInstance;

% get input linearization ranges
minMaxSensor.thumb = [325 450];
minMaxSensor.index = [300 500];
minMaxSensor.middle = [300 500];
minMaxSensor.ring = [300 500];
minMaxSensor.little = [300 500];

% this is the output range
minMaxTactor = [0 150];

% label the sensors
thumbSensor = 1;
indexSensor = 2;
middleSensor = 3;
ringSensor = 4;
littleSensor = 5;

%% Control loop 


StartStopForm([])
keepIndices = 1:6;
collectedMinMax = [inf(1, length(keepIndices)); zeros(1, length(keepIndices))];

while StartStopForm
    drawnow
    
    sensorData = obj.getdata(); % returns 12x1
    % do some mapping
    outputData = sensorData(keepIndices);
%     disp(outputData');
    
    collectedMinMax(1, :) = min([outputData'; collectedMinMax(1, :)], [], 1);
    collectedMinMax(2, :) = max([outputData'; collectedMinMax(2, :)], [], 1);
    
    % bound the input vals from 0 to 1
    outputData(thumbSensor) = (outputData(thumbSensor) - minMaxSensor.thumb(1)) ./ diff(minMaxSensor.thumb);
    outputData(indexSensor) = (outputData(indexSensor) - minMaxSensor.index(1)) ./ diff(minMaxSensor.index);
    outputData(middleSensor) = (outputData(middleSensor) - minMaxSensor.middle(1)) ./ diff(minMaxSensor.middle);
    outputData(ringSensor) = (outputData(ringSensor) - minMaxSensor.ring(1)) ./ diff(minMaxSensor.ring);
    outputData(littleSensor) = (outputData(littleSensor) - minMaxSensor.little(1)) ./ diff(minMaxSensor.little);
    
    % now bound everything to minMaxTactor bounds
    outputData = max(min(outputData, 1), 0) * diff(minMaxTactor) + minMaxTactor(1);
%     disp(outputData');
   
    % do some range checking
%     hTactors.tactorVals = outputData([littleSensor, ringSensor, middleSensor, indexSensor, thumbSensor]);
    hTactors.tactorVals = outputData([thumbSensor, indexSensor, middleSensor, ringSensor, littleSensor]);
    fprintf('%6.0f %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f\n', hTactors.tactorVals, sensorData(keepIndices(1:5)));
%     hTactors.transmit();
    
    pause(0.02)
    
end

%% hTactors
try
hTactors.close
end
try
obj.close
end
save('collectedMinMax', 'collectedMinMax');
unloadlibrary('PPSDaq');
run('cleanup.m');