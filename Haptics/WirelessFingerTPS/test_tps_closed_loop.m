%% Setup Tactors
TactorPort = '127.0.0.1:12001';
TactorType = 'VibroUDP';

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


%% Control loop 


StartStopForm([])

while StartStopForm
    drawnow
    
    sensorData = obj.getdata(); % returns 12x1
    % do some mapping
    outputData = sensorData(1:5);
    disp(outputData')
   
    % do some range checking
    hTactors.tactorVals = outputData;
    hTactors.transmit();
    
    pause(0.02)
    
end
    
