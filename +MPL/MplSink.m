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
            % updated.
            %
            % Usage:
            % gotoSmooth(obj, anglesRadians)
            %
            % Inputs:
            %   anglesRadians - 1x7 array OR 1x27 array of arm joint angles
            %   in radians
            %
            % The algorithm here applys linear segments with parabolic
            % blends, delivering a velocity limited result.
            %
            % Step 1: compute the minimum time required for all the joints.
            % the actual time will be the max of these
            %
            % Step 2: generate trajectories for all joints (note, check the
            % maximum speed required)
            %
            % Step 3: execute motion
            % 
            % 
            % Revisions:
            %   2016JUN01 Armiger: Created
            %   2016SEP21 Armiger: Changed motions to lspb approach
            
            if nargin < 2
                anglesRadians = [0.0 -0.3 0.0 1.9 0.0 0.0 0.0 zeros(1,20)];
            end
            
            assert((length(anglesRadians) == 7) || ...
                (length(anglesRadians) == 27),'Expected an array of length 7 or 27');
            
            assert (all(abs(anglesRadians)) <= pi, ...
                'mplAngles out of range.  Expected all values to be from -pi to pi');

            anglesRadians = obj.enforceLimits(anglesRadians);

            % RSA: repeat the get percepts command to make sure that there
            % aren't too many buffered.  
            for iRepeat = 1:5
                perceptData = obj.getPercepts();
                jointAngles = perceptData.jointPercepts.position; %radians
            end            
            
            assert(~isempty(jointAngles),'Unable to get percept data on port %d. Check Network Connectivity. Check Firewall.',obj.MplLocalPort);

            %%
            % constants
            numJointsMpl = length(properties(MPL.EnumArm));
            dt = 0.02;  % CAN refresh rate

            targetPos = double(jointAngles); % instatiate with current position
            targetPos(1:length(anglesRadians)) = anglesRadians; % update with input positions

            % compute time
            tMin = zeros(numJointsMpl,1);

            % Maximum move velocity
            vMax = 0.4;
            
            for i = 1:numJointsMpl
                % compute minimum time
                qf = targetPos(i);
                q0 = jointAngles(i);
                tMin(i) = abs(qf - q0) / vMax;
            end
            
            fprintf('[%s.m] Minimum time for move is %6.1f\n',mfilename,max(tMin));
            
            % add 10% to get nice blends 
            tMax = max(tMin) * 1.1;
            t = 0:dt:tMax;
            numSteps = length(t);
            tFinal = max(t);
                        
            qAll = zeros(numJointsMpl,numSteps);
            
            % generate joint trajectories
            for i = 1:numJointsMpl
                % compute minimum time
                qf = targetPos(i);
                q0 = jointAngles(i);
                q = lspb(q0,qf,vMax,tFinal);
                qAll(i,:) = q;
            end
            
            % execute move
            for i = 1:numSteps
                anglesTransmit = qAll(:,i);
                obj.putData(anglesTransmit);
                
                fprintf(['[%s] Arm Angles: SHFE=%6.1f | SHAA=%6.1f | HUM=%6.1f'...
                    '| EL=%6.1f | WR=%6.1f | DEV=%6.1f | WFE=%6.1f Degrees\n'],...
                    mfilename,anglesTransmit(1:7)*180/pi);

                pause(dt)
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
