classdef MplSink < Common.DataSink
    % Abstract Class for controlling JHU/APL MPL/vMPL 
    %
    % This data sink is used with the vMPL system.  Note this only supports
    % the all DOM PV command
    %
    properties
        % Handles
        hUdp;  % Handle to Udp port.  local port is setup to receive percepts and send to command port
        
        MplAddress;         % Command IP (127.0.0.1)
        MplCmdPort;         % Command Port e.g. (L=9024 R=9027)
        MplLocalPort;       % Percept Port e.g. (L=9026 R=9029)

        MplJointLimits      % [27x2] matrix of each joints limits.  These are read in from the config xml file
        Verbose = 1;        % Control Console Printing Verbosity
    end
    methods (Abstract = true)
        putData(obj)
        getPercepts(obj)
    end
    methods
        function success = initialize(obj)
            % setup data stream via udp
            % Input arguments:
            %   None
            %
            
            % if nothing is set, bring up selection dialog
            if isempty(obj.MplAddress) && isempty(obj.MplCmdPort) ...
                    && isempty(obj.MplLocalPort)
                obj.setPortDefaults;
            end
            
            % if local port not set, cannot continue
            if isempty(obj.MplLocalPort)
                error('UDP Port Not Specified');
            end
            
            % set joint limits
            loadLimits(obj);
            
            % PnetClass(localPort,remotePort,remoteIP)
            obj.hUdp = PnetClass(...
                obj.MplLocalPort,obj.MplCmdPort,obj.MplAddress);
            obj.hUdp.initialize();
            
            pause(0.02);
            
            % check for percepts
            if ~isempty(obj.hUdp.getData)
                fprintf('[%s] Percepts are available on Port %d\n',mfilename,obj.MplLocalPort);
            else
                fprintf('[%s] Percepts NOT available on Port %d\n',mfilename,obj.MplLocalPort);
            end
            
            success = true;
            
        end
        function success = gotoSmooth(obj, anglesRadians)
            % Send incremental updates in a blocking while loop to achieve
            % a desired position.  Requires that percepts are active and
            % updated
            %
            % gotoSmooth(obj, anglesRadians)
            %
            % Inputs:
            %   anglesRadians - 1x7 array OR 1x27 array of arm joint angles
            %   in radians
            
            if nargin < 2
                anglesRadians = [0.0 -0.3 0.0 1.9 0.0 0.0 0.0 zeros(1,20)];
            end
            
            assert((length(anglesRadians) == 7) || ...
                (length(anglesRadians) == 27),'Expected an array of length 7 or 27');
            
            assert (all(abs(anglesRadians)) <= pi, ...
                'mplAngles out of range.  Expected all values to be from -pi to pi');

            anglesRadians = obj.enforceLimits(anglesRadians);
            
            % Get current position
            jointAngles = [];
            nRetries = 5;
            for iTry = 1:nRetries
                perceptData = obj.getPercepts();
                if ~isempty(perceptData)
                    jointAngles = perceptData.jointPercepts.position; %radians
                    break;
                end
            end
            
            assert(~isempty(jointAngles),'Unable to get percept data on port %d. Check VulcanX. Check Firewall.',obj.MplLocalPort);
            
            vMax = 0.1;
            tolArm = 2.5*pi/180;
            tolHand = 10*pi/180;
            tolConverge = 1e-6;
            timeoutCount = 0;
            maxTries = 400;
            convergeCount = 0;
            targetPos = jointAngles; % instatiate with current position
            targetPos(1:length(anglesRadians)) = anglesRadians; % update with input positions
            lastActualPosition = jointAngles;
            while 1
                pause(0.02);
                
                perceptData = obj.getPercepts();
                if isempty(perceptData)
                    continue
                end
                currentPos = perceptData.jointPercepts.position;
                delta = targetPos - currentPos;
                
                if all(abs(delta(1:7)) < tolArm) && all(abs(delta(8:27)) < tolHand)
                    fprintf('[%s] Move Complete\n', mfilename)
                    break
                elseif (timeoutCount > maxTries)
                    disp(delta)
                    warning('Unable to complete move');
                    success = false;
                    return
                elseif all( abs( lastActualPosition - currentPos ) < tolConverge)
                    fprintf('[%s] Move Converged\n', mfilename)
                    convergeCount = convergeCount + 1;
                    
                    if convergeCount > 20
                        break
                    end
                else
                    timeoutCount = timeoutCount + 1;
                end

                [maxVal, maxId] = max(abs(delta' * 180/pi));
                jointNames = properties(MPL.EnumArm);
                
                %fprintf('Max Error: %6.1f degrees Joint: %s Desired: %6.1f Actual: %6.1f\n',...
                %    maxVal,jointNames{maxId},targetPos(maxId)*180/pi,currentPos(maxId)*180/pi)
                
                % make only incremental changes at each timestep
                delta(delta > vMax) = vMax;
                delta(delta < -vMax) = -vMax;
                
                newPos = currentPos + delta;
                lastActualPosition = currentPos;
                obj.putData(newPos);
            end
            
            success = true;
        end
        function success = loadLimits(obj)
            % check and load joint limits from the user config xml file
            %
            % Get joint names from enumeration
            % Use this as a based string to then get xml defaults from user
            % config file
            jointNames = fieldnames(MPL.EnumArm);
            numJoints = length(jointNames);
            obj.MplJointLimits = repmat([0 0],numJoints,1); 
            
            for i = 1:numJoints
                r = UserConfig.getUserConfigVar(strcat(jointNames{i},'_LIMITS'),[0 0.5]);
                
                obj.MplJointLimits(i,1) = r(1) * pi / 180;
                obj.MplJointLimits(i,2) = r(2) * pi / 180;
            end
            
            success = true;

        end
        function anglesOut = enforceLimits(obj,mplAngles)
            % Apply the joint limits to the angles provided as input
            % Input:
            %   mplAngles - [27x1] array of joint angles in radians
            %
            % Output:
            %   anglesOut - [27x1] array of joint angles, clipped to limit
            %       range as specified in the MplJointLimits property
            
            anglesOut = mplAngles;
            
            for i = 1:length(anglesOut)
                anglesOut(i) = min(max(anglesOut(i),obj.MplJointLimits(i,1)),obj.MplJointLimits(i,2));
            end  
        end
        function close(obj)
            % Cleanup and close udp port
            if ~isempty(obj.hUdp)
                obj.hUdp.close();
                obj.hUdp = [];
            end
        end
    end
end
