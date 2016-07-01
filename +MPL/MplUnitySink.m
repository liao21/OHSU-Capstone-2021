classdef MplUnitySink < Common.DataSink
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
    %     enum AllJointsType
    %     {
    %     SHOULDER_FE,	SHOULDER_AB_AD,
    %     HUMERAL_ROT,
    %     ELBOW, 
    %     WRIST_ROT,		WRIST_AB_AD,	WRIST_FE,
    %     INDEX_AB_AD, 	INDEX_MCP,		INDEX_PIP,		INDEX_DIP,
    %     MIDDLE_AB_AD,	MIDDLE_MCP,	MIDDLE_PIP,	MIDDLE_DIP,
    %     RING_AB_AD,	RING_MCP,		RING_PIP,		RING_DIP,
    %     LITTLE_AB_AD,	LITTLE_MCP,	LITTLE_PIP,	LITTLE_DIP,
    %     THUMB_CMC_AD_AB,	THUMB_CMC_FE,	THUMB_MCP,		THUMB_IP
    %     };
    % 
    %     enum FingerType
    %     {
    %     INDEX_AB_AD, 	INDEX_MCP,		INDEX_PIP,		INDEX_DIP,
    %     MIDDLE_AB_AD,	MIDDLE_MCP,	MIDDLE_PIP,	MIDDLE_DIP,
    %     RING_AB_AD,	RING_MCP,		RING_PIP,		RING_DIP,
    %     LITTLE_AB_AD,	LITTLE_MCP,	LITTLE_PIP,	LITTLE_DIP,
    %     THUMB_CMC_AD_AB,	THUMB_CMC_FE,	THUMB_MCP,		THUMB_IP
    %     };
    %
    % 28-Mar-2016 Armiger: Created
    properties
        % Handles
        hUdp;  % Handle to Udp port.  local port is setup to receive percepts and send to command port
        
        MplAddress;        % vMpl IP (127.0.0.1)
        MplCmdPort;        % Data Port (L=25100 R=25000)
        MplLocalPort;      % Percept Port (L=25101 R=25001)
        
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
                reply = questdlg('Select Arm','Unity','Left','Right','Left');
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
            
            % create message
            msg = typecast(single(mplAngles),'uint8');
            
            % write message
            obj.hUdp.putData(msg);
            
        end
    end
end
