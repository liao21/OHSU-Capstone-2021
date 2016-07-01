classdef MplUnitySink < MPL.MplSink
    % Data for controlling JHU/APL vMPL Unity Environment
    % Requires Utilities\PnetClass.m
    %
    % This data sink is used with the vMPL system
    %
    % Communications Info:
    %     Data should be sent in little endian format.
    % 
    %     Message               Transmission Type	Source	Target	Port
    %     Left vMPL Command             Broadcast	VULCANX	vMPLEnv	25100
    %     Right vMPL Command            Broadcast	VULCANX	vMPLEnv	25000
    %     Left vMPL Percepts            Broadcast	vMPLEnv	VULCANX	25101
    %     Right vMPL Percepts           Broadcast	vMPLEnv	VULCANX	25001
    %     Left Virtual Hand Command     Broadcast	VULCANX	vMPLEnv	25300
    %     Right Virtual Hand Command	Broadcast	VULCANX	vMPLEnv	25200
    %     Left Virtual Hand Percepts	Broadcast	vMPLEnv	VULCANX	25301
    %     Right Virtual Hand Percepts	Broadcast	vMPLEnv	VULCANX	25201
    % 
    % See also: MPL.EnumArm
    %
    % 28-Mar-2016 Armiger: Created
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
                reply = questdlg('Select Arm','Unity','Left','Right','Left');
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
            
            % Set port params using arm side defualts
            if IsLeftArm
                % Left
                obj.MplCmdPort = 25100;
                obj.MplLocalPort = 25101;
                obj.MplAddress = '127.0.0.1';
            else
                % Right
                obj.MplCmdPort = 25000;
                obj.MplLocalPort = 25001;
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
            
            % create message
            msg = typecast(single(mplAngles),'uint8');
            
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
            %         perceptData.jointPercepts
            % 
            %             position: [1x27 single]
            %             velocity: [1x27 single]
            %         (TODO) segmentPercepts
            
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
            nJoints = 27;
            nBytesPerFloat = 4;
            floatData = typecast(packets(1:nJoints*nBytesPerFloat*3),'single');
            floatData = reshape(floatData,3,nJoints);
            
            
            %data = extract_mpl_percepts_v2(packets);
            data.jointPercepts.position = floatData(1,:);
            data.jointPercepts.velocity = floatData(2,:);
            
            armDegrees = round(data.jointPercepts.position(1:7) * 180 / pi);
            fprintf(['[%s] Arm Angles: SHFE=%6.1f | SHAA=%6.1f | HUM=%6.1f'...
                '| EL=%6.1f | WR=%6.1f | DEV=%6.1f | WFE=%6.1f Degrees\n'],...
                mfilename,armDegrees);
            
        end % getPercepts
    end
end
