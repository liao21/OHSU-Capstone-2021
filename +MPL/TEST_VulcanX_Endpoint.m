% Demonstrate Endpoint Control of MPL using Joystick and VulcanX (physical
% and/or virtual MPL)
%
% 6/30/2016 Armiger: Created 

hSink = MPL.MplVulcanXSink;
hSink.setPortDefaults();
hSink.initialize();

hJoystick = JoyMexClass();
hJoystick.axisDeadband(:) = 0.1;

%% Synch Current position and target position
perceptData = hSink.getPercepts();
jointAngles = perceptData.jointPercepts.position; %radians
hSink.putData(jointAngles);

%% Smooth Home
hSink.gotoSmooth();

%% Set motion state variables
rocTableValues = 0.0;
graspsId = 1;
endpointVelocityMode = true;

%%
gainWristOrient = 0.9;
gainGrasp = 0.01;
gainEndpointPos = 0.1;

% 6 = trigger
% 4 = three finger
% 5 = Cyl
% 7 = Spherical
grasps = [6 5 4 7];

StartStopForm([]);
while StartStopForm
    pause(0.02)  % 50 Hz
    hJoystick.update();
    axVal = hJoystick.axisVal .* hJoystick.axisActive;
    
    if endpointVelocityMode
        % Translate the hand
        endPtVelocities = [-axVal(3); -axVal(1); axVal(4)].*gainEndpointPos;
        Rx = hJoystick.buttonVal(2) - hJoystick.buttonVal(1);
        Ry = hJoystick.buttonVal(7) - hJoystick.buttonVal(8);
        Rz = hJoystick.buttonVal(5) - hJoystick.buttonVal(6);
        rVal =  hJoystick.buttonVal(3) - hJoystick.buttonVal(4);
    else
        % Orient the hand
        endPtVelocities = [0 0 0];
        Rx = axVal(2) * gainWristOrient;
        Ry = -axVal(3) * gainWristOrient;
        Rz = -axVal(4) * gainWristOrient;
        rVal =  hJoystick.buttonVal(3) - hJoystick.buttonVal(4);
    end
    
    if hJoystick.buttonsPressed(10)
        disp('Mode Change')
        endpointVelocityMode = ~endpointVelocityMode;
    end
    if hJoystick.buttonsPressed(9)
        disp('Grasp Change')
        graspsId = graspsId + 1;
        if graspsId > length(grasps)
            graspsId = 1;
        end
    end
    
    endPtOrientationVelocities = [Rx; Ry; Rz];
    
    rocMode = hSink.hMud.ROC_MODE_POSITION;
    rocTableIDs = grasps(graspsId);
    rocTableValues = rocTableValues + (rVal*gainGrasp);
    rocTableValues = max(min(rocTableValues,1),0);
    rocWeights  = 1;
    msg = hSink.hMud.EndpointVelocity6HandRocGrasps( ...
        endPtVelocities, endPtOrientationVelocities, ...
        rocMode, rocTableIDs, rocTableValues, rocWeights);
    
    hSink.hUdp.putData(msg);
end
