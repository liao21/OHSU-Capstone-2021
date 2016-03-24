% test Myo Arm
%
% Objective is to use an upper and lower arm myo band to control the upper
% and lower joints based on position data as applicable.  This would enable
% above and below arm amuptees full control of the arm
%
%
%

% Above Elbow Case:  MYO mounted to left humerus, LED down, logo up, logo
% in lateral direction.
isLeft = 0;

% Create Myo input
hMyo = Inputs.MyoUdp.getInstance();
hMyo.initialize()

% Create Unity Sink

% Left vMPL Command             Broadcast	VULCANX	vMPLEnv	25100
% Right vMPL Command            Broadcast	VULCANX	vMPLEnv	25000
if isLeft
    hSink = PnetClass(43897,25100,'127.0.0.1');
else
    hSink = PnetClass(43897,25000,'127.0.0.1');
end
hSink.initialize()
mplAngles = zeros(1,27,'single');
hSink.putData(typecast(mplAngles*pi/180,'uint8'))

pause(1)
hMyo.getData();
pause(1)

%%
f = figure(1);
clf
daspect([1 1 1])
PlotUtils.triad(eye(4),0.2)
hRef = PlotUtils.triad(eye(4),0.4);
hT = PlotUtils.triad(eye(4),2);
view(-170,15)
StartStopForm([])
Fref = eye(4);

while StartStopForm()
    drawnow
    hMyo.getData();
    q = hMyo.Quaternion(:,end);
    R = LinAlg.quaternionToRMatrix(q);
    [U, S, V]=svd(R);
    R = U*V'; % Square up the rotaiton matrix

    F = [R [0; 0; 0]; 0 0 0 1];
    set(hT,'Matrix', F);
    %F_offset = makehgtform('yrotate',pi/2,'xrotate',yawOffset);
    if isequal(Fref, eye(4))
        Fref = F;
        set(hRef,'Matrix', Fref)
    end
    newXYZ = LinAlg.decompose_R(pinv(Fref)*F);
    
    if isLeft
        mplAngles(1) = -newXYZ(3);
        mplAngles(2) = -newXYZ(2);
        mplAngles(3) = -newXYZ(1);
    else
        mplAngles(1) = newXYZ(3);
        mplAngles(2) = -newXYZ(2);
        mplAngles(3) = newXYZ(1);
    end        
    mplAngles(4) = 90;
    hSink.putData(typecast(mplAngles*pi/180,'uint8'))

    
end

return
%%
f = figure(1);
clf
daspect([1 1 1])
PlotUtils.triad()
hT = PlotUtils.triad();
view(-170,15)
StartStopForm([])
yawOffset = 0;
while StartStopForm()
    drawnow
    a.getData();
    q = a.Quaternion(:,end);
    R = [LinAlg.quaternionToRMatrix(q) [0; 0; 0]; 0 0 0 1];
    set(hT,'Matrix', R);
    F_offset = makehgtform('yrotate',pi/2,'xrotate',yawOffset);
    newXYZ = LinAlg.decompose_R(F_offset*R)
    if yawOffset == 0
        yawOffset = -newXYZ(1);
    end
    %set(hT,'Matrix', F_offset*R);
    
end
%%
f = figure(1);
clf
daspect([1 1 1])
PlotUtils.triad(eye(4),0.2)
hT = PlotUtils.triad(eye(4),2);
view(-170,15)
StartStopForm([])
Fref = eye(4);
while StartStopForm()
    drawnow
    a.getData();
    q = a.Quaternion(:,end);
    R = LinAlg.quaternionToRMatrix(q);
    
    F = [R [0; 0; 0]; 0 0 0 1];
    set(hT,'Matrix', F);
    %F_offset = makehgtform('yrotate',pi/2,'xrotate',yawOffset);
    if isequal(Fref, eye(4))
        Fref = F;
    end
    newXYZ = LinAlg.decompose_R(pinv(Fref)*F)
    %set(hT,'Matrix', F_offset*R);
    
end


return
%%






hMyo = Inputs.MyoUdp.getInstance();
hMyo.initialize()

hSink = PnetClass(43897);
hSink.initialize()
mplAngles = zeros(1,27,'single');
hSink.putData(typecast(mplAngles*pi/180,'uint8'),'127.0.0.1',25000)

pause(1)
hMyo.getData();
pause(1)

%%
f = figure(1);
clf
daspect([1 1 1])
PlotUtils.triad(eye(4),0.2)
hRef = PlotUtils.triad(eye(4),0.4);
hT = PlotUtils.triad(eye(4),2);
view(-170,15)
StartStopForm([])
Fref = eye(4);
Fref2 = eye(4);
while StartStopForm()
    drawnow
    hMyo.getData();
    q = hMyo.Quaternion(:,end);
    R = LinAlg.quaternionToRMatrix(q);
    [U, S, V]=svd(R);
    R = U*V'; % Square up the rotaiton matrix

    F = [R [0; 0; 0]; 0 0 0 1];
    set(hT,'Matrix', F);
    %F_offset = makehgtform('yrotate',pi/2,'xrotate',yawOffset);
    if isequal(Fref, eye(4))
        Fref = F;
        set(hRef,'Matrix', Fref)
    end
    newXYZ = LinAlg.decompose_R(pinv(Fref)*F);
    %set(hT,'Matrix', F_offset*R);

    % Compute relative orientation between myo 1 and myo 2
    q = hMyo.SecondMyo.Quaternion(:,end);
    R2 = LinAlg.quaternionToRMatrix(q);
    [U, S, V] = svd(R2);
    R2 = U*V'; % Square up the rotaiton matrix

    F2 = [R2 [0; 0; 0]; 0 0 0 1];
    if isequal(Fref2, eye(4))
        Fref2 = F2;
    end
    
    %disp(hMyo.Quaternion(:,end) - hMyo.SecondMyo.Quaternion(:,end))
    
    relXYZ = LinAlg.decompose_R(pinv(pinv(Fref)*F)*pinv(Fref2)*F2);
    EL = relXYZ(3);
    
    mplAngles(1) = newXYZ(3);
    mplAngles(2) = -newXYZ(2);
    mplAngles(3) = newXYZ(1);
    mplAngles(4) = EL;
    mplAngles(1:4);
    hSink.putData(typecast(mplAngles*pi/180,'uint8'),'127.0.0.1',25000)

    
    
end

return
%%
f = figure(1);
clf
daspect([1 1 1])
PlotUtils.triad()
hT = PlotUtils.triad();
view(-170,15)
StartStopForm([])
yawOffset = 0;
while StartStopForm()
    drawnow
    a.getData();
    q = a.Quaternion(:,end);
    R = [LinAlg.quaternionToRMatrix(q) [0; 0; 0]; 0 0 0 1];
    set(hT,'Matrix', R);
    F_offset = makehgtform('yrotate',pi/2,'xrotate',yawOffset);
    newXYZ = LinAlg.decompose_R(F_offset*R)
    if yawOffset == 0
        yawOffset = -newXYZ(1);
    end
    %set(hT,'Matrix', F_offset*R);
    
end
%%
f = figure(1);
clf
daspect([1 1 1])
PlotUtils.triad(eye(4),0.2)
hT = PlotUtils.triad(eye(4),2);
view(-170,15)
StartStopForm([])
Fref = eye(4);
while StartStopForm()
    drawnow
    a.getData();
    q = a.Quaternion(:,end);
    R = LinAlg.quaternionToRMatrix(q);
    
    F = [R [0; 0; 0]; 0 0 0 1];
    set(hT,'Matrix', F);
    %F_offset = makehgtform('yrotate',pi/2,'xrotate',yawOffset);
    if isequal(Fref, eye(4))
        Fref = F;
    end
    newXYZ = LinAlg.decompose_R(pinv(Fref)*F)
    %set(hT,'Matrix', F_offset*R);
    
end
