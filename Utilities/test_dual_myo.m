% Setup the Myo and the limb for output debug
hMyo = Inputs.MyoUdp.getInstance();
hMyo.initialize()

hSink = MPL.MplUnitySink;
hSink.setPortDefaults()
hSink.initialize()
mplAngles = zeros(1,27);
hSink.putData(mplAngles*pi/180)

pause(1)
hMyo.getData();
pause(1)

%% Plot the orientation of the myo bands in their native coordinates as side by side moving triads

f = figure(99);
clf;
ax1 = subplot(1,2,1);
title('Primary Myo')
ax2 = subplot(1,2,2);
title('Secondary Myo')

daspect(ax1,[1 1 1]);
daspect(ax2,[1 1 1]);

PlotUtils.triad(eye(4),0.2,ax1);
PlotUtils.triad(eye(4),0.2,ax2);

hT1 = PlotUtils.triad(eye(4),2,ax1);
hT2 = PlotUtils.triad(eye(4),2,ax2);

StartStopForm([])
while StartStopForm()
    drawnow
    hMyo.getData();
    [R1, R2] = hMyo.getRotationMatrix;
    F1 = [R1 [0; 0; 0]; 0 0 0 1];
    F2 = [R2 [0; 0; 0]; 0 0 0 1];
    set(hT1,'Matrix', F1);
    set(hT2,'Matrix', F2);
    a1 = LinAlg.decompose_R(F1);
    a2 = LinAlg.decompose_R(F2);
    fprintf('MYO1: Rx:%6.1f Ry:%6.1f Rz:%6.1f | MYO2: Rx:%6.1f Ry:%6.1f Rz:%6.1f\n',a1,a2)
    
end


%%
hRef = PlotUtils.triad(eye(4),0.4);
hT = PlotUtils.triad(eye(4),2);
view(-170,15)
StartStopForm([])
Fref = eye(4);
Fref2 = eye(4);
while StartStopForm()
    drawnow
    hMyo.getData();
    q = hMyo.Orientation';
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
    q = hMyo.SecondMyo.Orientation';
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
    hSink.putData(mplAngles*pi/180)

end


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
    q = hMyo.Orientation';
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
    q = hMyo.SecondMyo.Orientation';
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
    hSink.putData(mplAngles*pi/180)

end
