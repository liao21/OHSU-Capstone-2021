classdef MplVulcanXSink < Common.DataSink
    % Data for controlling JHU/APL MPL/vMPL VulcanX Environment
    % Requires Utilities\PnetClass.m
    %
    % This data sink is used with the vMPL system.  Note this only supports
    % the all DOM PV command
    %
    % Example usage:
    %
    %     hSink = MPL.MplVulcanXSink;
    %     hSink.setPortDefaults();
    %     hSink.initialize();
    % 
    %     %% Synch Current position and target position
    %     perceptData = hSink.getPercepts();
    %     jointAngles = perceptData.jointPercepts.position; %radians
    %     hSink.putData(jointAngles);
    % 
    %     %% Smooth Home
    %     hSink.gotoSmooth();
    %
    % 28-Mar-2016 Armiger: Created
    properties
        % Handles
        hUdp;  % Handle to Udp port.  local port is setup to receive percepts and send to command port
        hMud = MPL.MudCommandEncoder(); % MUD message translator

        MplAddress;         % VulcanX IP (127.0.0.1)
        MplCmdPort;         % MUD Port (L=9024 R=9027)
        MplLocalPort;       % Percept Port (L=25101 R=25001)
        
        Verbose = 1;        % Control Console Printing Verbosity 
    end
    methods
        function success = initialize(obj)
            % setup data stream via udp
            % Input arguments: 
            %   None
            %

            if isempty(obj.MplLocalPort)
                error('UDP Port Not Specified');
            end
            
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
        function setPortDefaults(obj,IsLeftArm)
            % setDefaults
            % Input arguments: 
            %   IsLeftArm - Optional: Specifying true/false for this value
            %               will overwrite the port parameters to the
            %               local defaults. If this is omitted, a prompt
            %               will appear for the user to select Left / Right
            %

            if nargin < 2
                % prompt to select a side
                reply = questdlg('Select Arm','VulcanX','Left','Right','Left');
                switch reply
                    case 'Left'
                        IsLeftArm = true;
                    case 'Right'
                        IsLeftArm = false;
                    otherwise
                        % Arm is not initialized
                        return
                end
            end

            % Issue warning if settings are not empty
            if ~isempty(obj.MplAddress) || ...
                    ~isempty(obj.MplCmdPort) || ...
                    ~isempty(obj.MplLocalPort)
                warning('Overwriting port parameters settings');
            end
            
            % Set port params using arm side defualts
            if IsLeftArm
                % Left
                obj.MplCmdPort = 9024;
                obj.MplLocalPort = 9026;
                obj.MplAddress = '127.0.0.1';
            else
                % Right
                obj.MplCmdPort = 9027;
                obj.MplLocalPort = 9029;
                obj.MplAddress = '127.0.0.1';
            end
        end        
        function close(obj)
            % Cleanup and close udp port
            if ~isempty(obj.hUdp)
                obj.hUdp.close();
                obj.hUdp = [];
            end
        end
        function putData(obj, mplAngles)
            % Get current joint angles and send commands to vMpl
            % Input arguments: 
            %   mplAngles - array of joint angles in radians [1,27];
            
            if any(abs(mplAngles)) > pi
                error('mplAngles out of range.  Expected all values to be from -pi to pi')
            end
            
            % generate MUD message using joint angles
            
            %             % 0 to 256 for upper arm (256 is off)
            %             % upper arm around 40
            %             % wrist around 20, start around 40
            %             % hand is 0 to 16 (16 is off)
            %             % 0 to 1.5 for hand is useful range
            %             
            %             imp = [256*ones(1,4) 256*ones(1,3) 15.6288*ones(1,20)];
            %             imp = [256*ones(1,4) 256*ones(1,3) 0.5*ones(1,20)];
            % 
            %             imp(7+mpl_hand_enum.THUMB_CMC_AD_AB) = 16;
            % 
            %             % 15.5 
            %             % 15.
            %             msg = obj.hMud.AllJointsPosVelImpCmd(mplAngles(1:7),zeros(1,7),mplAngles(8:27),zeros(1,20),imp);
            
            % Non - impendance command
            msg = obj.hMud.AllJointsPosVelCmd(mplAngles(1:7),zeros(1,7),mplAngles(8:27),zeros(1,20));

            % write message
            obj.hUdp.putData(msg);
            
        end
        function data = getPercepts(obj)
            
            % Read buffered udp packets
            packets = obj.hUdp.getData;
            
            if isempty(packets)
                % No data ready
                data = [];
            else
                % convert packets to percept struct
                data = extract_mpl_percepts_v2(packets);
                armDegrees = round(data.jointPercepts.position(1:7) * 180 / pi);
                fprintf(['[%s] Arm Angles: SHFE=%6.1f | SHAA=%6.1f | HUM=%6.1f'...
                    '| EL=%6.1f | WR=%6.1f | DEV=%6.1f | WFE=%6.1f Degrees\n'],...
                    mfilename,armDegrees);
            end
            
        end % getPercepts
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
                anglesRadians = [0.0 -0.3 0.0 1.9 0.0 0.0 0.0];
            end
            
            assert((length(anglesRadians) == 7) || ...
                (length(anglesRadians) == 27),'Expected an array of length 7 or 27')
            
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
            
            assert(~isempty(jointAngles),'Unable to get percept data');

            vMax = 0.1;
            tolArm = 2.5*pi/180;
            tolHand = 10*pi/180;
            timeoutCount = 0;
            maxTries = 300;
            targetPos = jointAngles;
            targetPos(1:length(anglesRadians)) = anglesRadians;
            while 1
                pause(0.02); 
                
                perceptData = obj.getPercepts();
                if isempty(perceptData)
                    continue
                end
                currentPos = perceptData.jointPercepts.position;
                delta = targetPos - currentPos;
                delta(delta > vMax) = vMax;
                delta(delta < -vMax) = -vMax;
                
                if all(abs(delta(1:7)) < tolArm) && all(abs(delta(8:27)) < tolHand)
                    fprintf('[%s] Move Complete\n', mfilename)
                    break
                elseif (timeoutCount > maxTries)
                    error('Unable to complete move');
                else
                    timeoutCount = timeoutCount + 1;
                end
                
                newPos = currentPos + delta;
                obj.putData(newPos);
            end
            
            success = true;
        end
    end
end
