classdef MplVulcanXSink < Common.DataSink
    % Data for controlling JHU/APL MPL/vMPL VulcanX Environment
    % Requires Utilities\PnetClass.m
    %
    % This data sink is used with the vMPL system.  Note this only supports
    % the all DOM PV command
    %
    % 28-Mar-2016 Armiger: Created
    properties
        % Handles
        hUdp;  % Handle to Udp port.  local port is setup to receive percepts and send to command port
        
        MplAddress = '127.0.0.1';   % VulcanX IP (127.0.0.1)
        MplCmdPort = 9027;          % MUD Port (L=9024 R=9027)
        MplLocalPort = 25001;       % Percept Port (L=25101 R=25001)

        % Create MUD message translator
        hMud = MPL.MudCommandEncoder();
        
    end
    methods
        function success = initialize(obj)
            % setup data stream via udp
            % Input arguments: 
            %   None
            %
            
            % PnetClass(localPort,remotePort,remoteIP)
            obj.hUdp = PnetClass(...
                obj.MplLocalPort,obj.MplCmdPort,obj.MplAddress);
            obj.hUdp.initialize();
            
            success = true;
            
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
            msg = obj.hMud.AllJointsPosVelCmd(mplAngles(1:7),zeros(1,7),mplAngles(8:27),zeros(1,20));

            % write message
            obj.hUdp.putData(msg);
            
        end
    end
end
