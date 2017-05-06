classdef LeapMotion < handle
    properties
        hUdp
    end
    methods
        function initialize(obj,port)
            % initialize the leap motion udp streaming object
            %
            % Arguments:
            %
            % port - port to listen for udp messages (default = 14001)
            
            if nargin < 2
                port = 14001;
            end
            
            obj.hUdp = PnetClass(port);
            obj.hUdp.initialize();
            
        end
        
        function frame = getData(obj)
            % return the frame data structure
            m = obj.hUdp.getData();
            if isempty(m)
                frame = [];
            else
                try
                    frame = parse_lines(m);
                catch ME
                    char(m)
                    rethrow(ME)
                end
            end
        end
        
        function close(obj)
            obj.hUdp.close()
        end
        
    end
    
    methods (Static = true)
        function preview
            %% Inputs.LeapMotion.preview()
            
            h = Inputs.LeapMotion;
            h.initialize();
            
            clf
            hold on
            daspect([1 1 1])
            scale = 10;
            [X,Y,Z] = sphere();
            FVC = surf2patch(X*scale,Y*scale,Z*scale);
            
            hGlobal = hgtransform('Matrix',makehgtform('xrotate',pi/2));
            
            for iHand = 1:2
                hHand(iHand) = hgtransform('Parent',hGlobal,'Visible','off');
                
                hPatchTransform(iHand) = hgtransform('Parent',hHand(iHand));
                hHandPatch = patch(FVC,'facecolor','cyan','Parent',hPatchTransform(iHand),'edgecolor','None');
                
                hHandDot = line(0,0,'Parent',hPatchTransform(iHand));
                hHandDot.Marker = '.';
                hHandDot.Color = 'r';
                
                hFingers(iHand) = line(0,0,'Parent',hHand(iHand));
                hFingers(iHand).Marker = '.';
                
                hArm(iHand) = line(0,0,'Parent',hHand(iHand));
                hArm(iHand).Marker = '.';
                
            end
            
            hT = PlotUtils.triad(eye(4),50);
            set(hT,'Parent',hGlobal);
            
            view(3);
            axis([-300 300 -300 300 0 500]);
            
            %
            StartStopForm([])
            while StartStopForm
                drawnow limitrate
                frame = h.getData();
                if isempty(frame)
                    continue
                end
                
                set(hHand,'Visible','off');
                for i = 1:frame.hands
                    
                    nx = frame.hand(i).x_basis' ./ norm(frame.hand(i).x_basis);
                    ny = frame.hand(i).y_basis' ./ norm(frame.hand(i).y_basis);
                    nz = frame.hand(i).z_basis' ./ norm(frame.hand(i).z_basis);
                    
                    R = [nx ny nz];
                    [U, ~, V] = svd(R);
                    R2 = U*V'; % Square up the rotation matrix
                    
                    R3 = LinAlg.makeRotationMtx(LinAlg.decompose_R(R2));
                    
                    T = [R3 frame.hand(i).position'; 0 0 0 1];
                    
                    hPatchTransform(i).Matrix = T;
                    
                    fingerData = nan(3,frame.hand(i).fingers*4*3);
                    idx = 0;
                    for j = 1:frame.hand(i).fingers
                        
                        for k = 1:4
                            idx = idx + 1;
                            fingerData(:,idx) = frame.hand(i).finger(j).bone(k).start';
                            idx = idx + 1;
                            fingerData(:,idx) = frame.hand(i).finger(j).bone(k).end';
                            idx = idx + 1;
                        end
                    end
                    hFingers(i).XData = fingerData(1,:);
                    hFingers(i).YData = fingerData(2,:);
                    hFingers(i).ZData = fingerData(3,:);
                    
                    dx = 20;
                    armData = [frame.arm(i).wrist_position' frame.arm(i).elbow_position'];
                    armData = [fliplr(armData)-(frame.arm(i).direction'*dx) armData+(frame.arm(i).direction'*dx)];
                    armData = [armData armData(:,1)];
                    
                    hArm(i).XData = armData(1,:);
                    hArm(i).YData = armData(2,:);
                    hArm(i).ZData = armData(3,:);
                    
                    set(hHand(i),'Visible','on');
                end
            end
            
            h.close()
            
        end
    end
end




function frame = parse_lines(m)
%#ok<*ST2NM>
% Frame id: 1318805, timestamp: 13876662340, hands: 1, fingers: 5
%   Right hand, id 524, position: (35.7776, 259.081, 45.0254), fingers: 5
%   x_basis: (0.933604, 0.348578, -0.0233529), y_basis: (4.2963e-005, 2.61786e-012, 4.00578e-011), z_basis: (1.45856e-019, 6.40941e-010, 5.437
% 09e+022)
%   Arm x_basis: (0.898448, 0.415938, -0.135902), wrist position: (57.4761, 231.841, 113.927), elbow position: (150.328, 104.211, 337.652)
%     Thumb finger, id: 5240, length: 51.115784mm, width: 20.787615mm
%       Bone: Metacarpal, start: (28.5436, 221.038, 93.8392), end: (28.5436, 221.038, 93.8392), direction: (0, 0, 0)
%       Bone: Proximal, start: (28.5436, 221.038, 93.8392), end: (-6.81825, 220.277, 57.6276), direction: (0.698584, 0.0150395, 0.71537)
%       Bone: Intermediate, start: (-6.81825, 220.277, 57.6276), end: (-29.0024, 219.898, 32.6072), direction: (0.663381, 0.0113466, 0.748196)
%       Bone: Distal, start: (-29.0024, 219.898, 32.6072), end: (-44.9525, 219.562, 16.1033), direction: (0.694867, 0.0146431, 0.71899)
%     Index finger, id: 5241, length: 57.678459mm, width: 19.856331mm
%       Bone: Metacarpal, start: (28.3205, 245.07, 93.3736), end: (6.69853, 263.023, 24.2656), direction: (0.289823, -0.240647, 0.926332)
%       Bone: Proximal, start: (6.69853, 263.023, 24.2656), end: (-0.70677, 263.54, -17.2129), direction: (0.175741, -0.0122505, 0.98436)
%       Bone: Intermediate, start: (-0.70677, 263.54, -17.2129), end: (-0.814376, 255.391, -39.4745), direction: (0.00453913, 0.343733, 0.939057)
%       Bone: Distal, start: (-0.814376, 255.391, -39.4745), end: (1.16992, 245.916, -53.1533), direction: (-0.118412, 0.565401, 0.816272)
%     Middle finger, id: 5242, length: 65.719978mm, width: 19.501554mm
%       Bone: Metacarpal, start: (38.5828, 251.87, 91.2843), end: (26.9523, 272.678, 24.6725), direction: (0.164391, -0.294121, 0.941525)
%       Bone: Proximal, start: (26.9523, 272.678, 24.6725), end: (20.7205, 281.895, -21.2746), direction: (0.131822, -0.194962, 0.971912)
%       Bone: Intermediate, start: (20.7205, 281.895, -21.2746), end: (18.6913, 279.829, -49.0143), direction: (0.0727547, 0.0740649, 0.994596)
%       Bone: Distal, start: (18.6913, 279.829, -49.0143), end: (18.0607, 275.506, -66.9202), direction: (0.0342162, 0.234564, 0.971498)
%     Ring finger, id: 5243, length: 63.191509mm, width: 18.556967mm
%       Bone: Metacarpal, start: (50.2978, 255.743, 89.5654), end: (48.9149, 277.573, 29.9295), direction: (0.0217703, -0.343658, 0.938842)
%       Bone: Proximal, start: (48.9149, 277.573, 29.9295), end: (47.8497, 294.103, -10.6412), direction: (0.0243087, -0.377204, 0.925811)
%       Bone: Intermediate, start: (47.8497, 294.103, -10.6412), end: (47.7916, 299.037, -37.3595), direction: (0.00213717, -0.181603, 0.98337)
%       Bone: Distal, start: (47.7916, 299.037, -37.3595), end: (48.1339, 298.886, -55.6809), direction: (-0.0186771, 0.00821505, 0.999792)
%     Pinky finger, id: 5244, length: 49.540974mm, width: 16.483747mm
%       Bone: Metacarpal, start: (64.2789, 252.616, 87.8218), end: (70.0903, 277.182, 34.716), direction: (-0.0988328, -0.417791, 0.903152)
%       Bone: Proximal, start: (70.0903, 277.182, 34.716), end: (77.3316, 293.84, 5.17277), direction: (-0.208799, -0.480326, 0.851874)
%       Bone: Intermediate, start: (77.3316, 293.84, 5.17277), end: (81.2021, 300.569, -12.3698), direction: (-0.201765, -0.350758, 0.914472)
%       Bone: Distal, start: (81.2021, 300.569, -12.3698), end: (84.3033, 302.999, -28.8102), direction: (-0.183442, -0.143749, 0.972463)

s = string(char(m));
l = s.splitlines;

offset = 1;

frame.id = str2double(l(offset).extractBetween('id:',','));
frame.timestamp = str2double(l(offset).extractBetween('timestamp:',','));
frame.hands = str2double(l(offset).extractBetween('hands:',','));
frame.fingers = str2double(l(offset).extractAfter('fingers:'));

for iHand = 1:frame.hands
    offset = offset + 1;
    frame.hand(iHand).name = strtrim(l(offset).extractBefore('hand'));
    frame.hand(iHand).id = str2double(l(offset).extractBetween('id',','));
    frame.hand(iHand).position = str2num(char(l(offset).extractBetween('position: (',')')));
    frame.hand(iHand).fingers = str2double(l(offset).extractAfter('fingers: '));
    
    offset = offset + 1;
    frame.hand(iHand).x_basis = str2num(char(l(offset).extractBetween('x_basis: (',')')));
    frame.hand(iHand).y_basis = str2num(char(l(offset).extractBetween('y_basis: (',')')));
    frame.hand(iHand).z_basis = str2num(char(l(offset).extractBetween('z_basis: (',')')));
    
    offset = offset + 1;
    frame.arm(iHand).direction= str2num(char(l(offset).extractBetween('Arm x_basis: (',')')));
    frame.arm(iHand).wrist_position= str2num(char(l(offset).extractBetween('wrist position: (',')')));
    frame.arm(iHand).elbow_position= str2num(char(l(offset).extractBetween('elbow position: (',')')));
    for iFinger = 1:frame.hand(iHand).fingers
        offset = offset + 1;
        frame.hand(iHand).finger(iFinger).name = strtrim(l(offset).extractBefore('finger'));
        frame.hand(iHand).finger(iFinger).id = str2double(l(offset).extractBetween('id:',','));
        frame.hand(iHand).finger(iFinger).length = str2double(l(offset).extractBetween('length: ','mm'));
        frame.hand(iHand).finger(iFinger).width = str2double(l(offset).extractBetween('width: ','mm'));
        
        for iBone = 1:4
            offset = offset + 1;
            frame.hand(iHand).finger(iFinger).bone(iBone).name = strtrim(l(offset).extractBetween('Bone: ',','));
            frame.hand(iHand).finger(iFinger).bone(iBone).start = str2num(char(l(offset).extractBetween('start: (',')')));
            frame.hand(iHand).finger(iFinger).bone(iBone).end = str2num(char(l(offset).extractBetween('end: (',')')));
            frame.hand(iHand).finger(iFinger).bone(iBone).direction = str2num(char(l(offset).extractBetween('direction: (',')')));
        end
    end
end
end
