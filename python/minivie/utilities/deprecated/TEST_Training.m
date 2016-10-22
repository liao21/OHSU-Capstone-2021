classes = {'Wrist Rotate In'
    'Wrist Rotate Out'
    'Wrist Flex In'
    'Wrist Extend Out'
    'Hand Open'
    'Tip Grasp'
    'Lateral Grasp'
    'Spherical Grasp'
    'No Movement'};

hData = PnetClass(round(999*rand)+6000, 10001,'127.0.0.1');
hData.initialize()
hSource = Inputs.SignalSimulator;
hSource.initialize(0:7)

hSink = PnetClass(round(200*rand)+5000, 3003,'127.0.0.1');
hSink.initialize()

for id = 1:length(classes)
    % set the class name
    disp(classes{id})
    payload = uint8([id classes{id}]);
    msg = uint8([10 2+length(payload) payload]);
    hSink.putData(msg)
    
    tic
    while toc < 2
        
        drawnow
        
        emg = uint8(120*(hSource.getData(1)-1.2));
        quat = typecast(single([1 0 0 0]),'uint8');
        acc = typecast(single([0 0 0]),'uint8');
        gyro = typecast(single([0 0 0]),'uint8');
        msg = cat(2,emg,quat,acc,gyro);
        hData.putData(msg)
        
        pause(1/200)
        
    end
end
%%
payload = uint8([4 '']);
msg = uint8([10 2+length(payload) payload]);
hSink.putData(msg)
