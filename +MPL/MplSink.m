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
            
            assert(~isempty(jointAngles),'Unable to get percept data on port %d. Check VulcanX. Check Firewall.',obj.MplLocalPort);
            
            vMax = 0.1;
            tolArm = 2.5*pi/180;
            tolHand = 10*pi/180;
            timeoutCount = 0;
            maxTries = 400;
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
                    disp(delta)
                    error('Unable to complete move');
                else
                    timeoutCount = timeoutCount + 1;
                end
                
                newPos = currentPos + delta;
                obj.putData(newPos);
            end
            
            success = true;
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
