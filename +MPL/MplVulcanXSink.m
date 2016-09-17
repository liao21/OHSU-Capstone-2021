classdef MplVulcanXSink < MPL.MplSink
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
        hMud = MPL.MudCommandEncoder(); % MUD message translator
    end
    methods
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
                        % No changes to port settings
                        return
                end
            end
            
            % Issue warning if settings are not empty
            if ~isempty(obj.MplAddress) || ...
                    ~isempty(obj.MplCmdPort) || ...
                    ~isempty(obj.MplLocalPort)
                warning('Overwriting port parameters settings');
            end
            
            % Set port params using arm side defaults
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
        function data = getPercepts(obj,nRetries)
            % Get percepts data via UDP port and convert to structure of
            % sensor values
            %
            % Note this function will retry several times before erroring
            % out
            %
            % Inputs:
            %   nRetries - number of times to attempt to get packet data
            %
            % Outputs:
            %   data -  
            %     perceptData.jointPercepts
            %            position: [1x27 single]
            %            velocity: [1x27 single]
            %              torque: [0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
            %         temperature: [0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
            %
            %     perceptData.segmentPercepts
            %               fstnForce: [14x5 double]
            %               fstnAccel: [3x5 double]
            %         contactPercepts: [0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
            
            if nargin < 2
                nRetries = 5;
            end
            
            for iTry = 1:nRetries
                % Read buffered udp packets
                packets = obj.hUdp.getData;
                if isempty(packets)
                    % Wait for a half CAN cycle and retry
                    pause(0.01);
                else
                    % success
                    break;
                end
            end
            
            assert(~isempty(packets),'Unable to get percept data on port %d. Check VulcanX. Check Firewall.',obj.MplLocalPort);
            
            % convert packets to percept struct
            data = extract_mpl_percepts_v2(packets);
            armDegrees = round(data.jointPercepts.position(1:7) * 180 / pi);
            if obj.Verbose
                fprintf(['[%s] Arm Angles: SHFE=%6.1f | SHAA=%6.1f | HUM=%6.1f'...
                    '| EL=%6.1f | WR=%6.1f | DEV=%6.1f | WFE=%6.1f Degrees\n'],...
                    mfilename,armDegrees);
            end
        end % getPercepts
    end
end
