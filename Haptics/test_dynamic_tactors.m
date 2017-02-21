%% Setup Tactors
% 192.168.1.1:12001 - ServoUDP
% 192.168.1.1:8089
% VibroUDP or TactorUDP
% TactorPort = '192.168.1.1:12001'; 
% TactorType = 'ServoUDP';
TactorPort = '192.168.1.1:12001'; 
TactorType = 'ServoUDP';
maxAngle = 70;
pulseNum = 1;
pulseWidth = 0.20;
pulseGap = 0.20;

switch TactorType
    case 'ServoUDP'
        hTactors = BluetoothTactor_UDP(TactorPort, maxAngle);
    case 'VibroUDP'
        hTactors = TactorUdp(TactorPort);
    case 'VibroBluetooth'
        hTactors = BluetoothTactor(TactorPort);
end
hTactors.initialize();

%% update via:
hTactors.maxAngle = 60;
hTactors.tactorVals = [0 0 0 0 0];
hTactors.transmit

% this is the output range
minMaxTactor = [0 255];

%% Control loop 

StartStopForm([])
buttonGUI = buttons_1to5();
handles = guidata(buttonGUI);

% 
dt = 0.01;
[f, t] = createWaveform(dt, pulseWidth, pulseNum, pulseGap);
f = f * 150;
tactorNum = 0;

figure;
nameCell = {'INDEX', 'NOTHING', 'NONE', 'NONE', 'NONE'};
trialCounter = 12;
gca;
axis off;
textHandle = text(0.5, 0.5, '.', 'HorizontalAlignment', 'center');

while StartStopForm && ishandle(handles.figure1)
    drawnow
       
    % do some range checking
    startTic = tic;
    if get(handles.button1, 'Value')
        tactorNum = 1;
        set(handles.button1, 'Value', 0);
    elseif get(handles.button2, 'Value')
        tactorNum = 2;
        set(handles.button2, 'Value', 0);
    elseif get(handles.button3, 'Value')
        tactorNum = 3;
        set(handles.button3, 'Value', 0);
    elseif get(handles.button4, 'Value')
        tactorNum = 4;
        set(handles.button4, 'Value', 0);
    elseif get(handles.button5, 'Value')
        tactorNum = 5;
        set(handles.button5, 'Value', 0);
    end
    drawnow;
    
    % send stuff
    if tactorNum >  0
        currTime = toc(startTic);
        currVals = zeros(1, 5);
        while currTime <= t(end)
            currVals(tactorNum) = f(find(currTime >= t, 1, 'last'));
            hTactors.tactorVals = currVals;
            hTactors.transmit();
            pause(dt);
            currTime = toc(startTic);
        end
        
        hTactors.tactorVals = zeros(1, 5);
        hTactors.transmit;
        
        delete(textHandle);
        textHandle = text(0.5, 0.5, [num2str(trialCounter) ' - ' nameCell{tactorNum}], 'FontSize', 128, 'HorizontalAlignment', 'center');
        trialCounter = trialCounter + 1;
        
        tactorNum = 0;
        
    end
    
    
    
    drawnow;
    pause(0.01)
    
end

%% hTactors
try
hTactors.close
end
try
    delete(buttonGUI)
end
run('cleanup.m');