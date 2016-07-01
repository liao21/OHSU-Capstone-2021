% Sample Myo UDP controller for games
% By David Samson
% July 1, 2016

% Send controller data via UDP
% Matlab packs data 

a = PnetClass(3452,5005,'192.168.56.101');
a.initialize;

joystickType = 'Default'; % SNES equivalent. May use 2 axes and up to 8 buttons
a.putData([255 uint8('T') uint8(joystickType)]) %send joystick selection to reciever


% Load training data file
hData = PatternRecognition.TrainingData();
hData.loadTrainingData();
%hData.loadTrainingData('C:\Users\samsoda1\Desktop\EMG Biointerfacing Lab\VIE Introduction Materials\user.trainingData');


% Create EMG Myo Interface Object
hMyo = Inputs.MyoUdp.getInstance();
hMyo.initialize();
 
% Create LDA Classifier Object
hLda = SignalAnalysis.Lda;
hLda.initialize(hData);
hLda.train();
hLda.computeError();

% Store the 6 most recent states of the predicted hand motion.
% Current motion is determined by the mode of these states
% Start with no movement (9)
state = [9 9 9 9 9 9];


% Create arrays to hold the buttons and the control axes
btns = [0 0 0 0];
axes = [0 0];

%%

% May want to tweak which classes cause what button presses/axis movement
StartStopForm([]); 
while StartStopForm 
    
    btns = [0 0 0 0]; %reset buttons after each loop
    %axes = [0 0]; %hold axes from previous loop
    
    % Get the appropriate number of EMG samples for the 8 myo channels
    emgData = hMyo.getData(hLda.NumSamplesPerWindow,1:8);
    
    % Extract features and classify
    features2D = hLda.extractfeatures(emgData);
    [classDecision, voteDecision] = hLda.classify(reshape(features2D',[],1));
    
    
    
    % Push current class decision into state buffer
    state(2:end) = state(1:end-1);
    state(1) = classDecision;
    state;
    classDecision = mode(state);
    
    
    % Perform controller states based on class decision mode
    % setup for left/right input and one button for jumping
    switch(classDecision)
        case 1 % Wrist rotate in
            fprintf('wrist rotate in\n');
            axes(1) = 32767; %joystick X = right
        case 2 % Wrist rotate out
            fprintf('wrist rotate out\n');
            axes(1) = -32767; %joystick X = left
        case 3 % Wrist flex in
            fprintf('wrist flex in\n');
            axes(1) = 32767;  %joystick X = right
        case 4 % Wrist extend out
            fprintf('wrist extend out\n');
            axes(1) = -32767;  %joystick X = left
        case 5 % Cylindrical grasp
            fprintf('cylindrical grasp\n');
            btns(1) = 1;   %press jump button
        case 6 % Tip grasp
            fprintf('tip grasp\n');
            btns(1) = 1;   %press jump button
        case 7 % Lateral grasp
            fprintf('lateral grasp\n');
            btns(1) = 1;   %press jump button
        case 8 % Hand open
            fprintf('hand open\n');
            btns(1) = 1;   %press jump button
        case 9 % No movement
            fprintf('no movement\n');
            btns = [0 0 0 0]; %reset buttons
            axes = [0 0];  %reset axes
        case 10 % wrist abduction
            fprintf('wrist abduction\n');
            axes(2) = -32767;   %joystick Y = Up
        case 11 %wrist adduction
            fprintf('wrist adduction\n');
            axes(2) = 32767;    %joystick Y = Down
            
    end
    
    %format buttons and axes for sending over UDP
    btn0 = binvec2dec(btns);
    btn0 = typecast(uint64(btn0),'uint8');
    btn0 = btn0(1:ceil(length(btns)/8));
    axis0 = typecast(int16(axes),'uint8');
    
    msg = uint8([length(btns) btn0 length(axes) axis0]);
    a.putData(msg); 
    
    drawnow; 
end

%a.putData([255 uint8('Q')]) % interrupt code to quit running UDP reciever