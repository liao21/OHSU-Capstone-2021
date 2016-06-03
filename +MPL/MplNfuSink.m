classdef MplNfuSink < Common.DataSink
    % Data for controlling JHU/APL MPL via NFU
    % Requires Utilities\PnetClass.m
    %
    % This data sink is used with the physical MPL system.  Note this only
    % supports the all DOM PV command and simply acts as a wrapper for the
    % joint position command to ensure all sinks can be treated the same
    %
    % 28-Mar-2016 Armiger: Created
    properties
        % Handles
        hNfu;  % Handle to Nfu comm device
    end
    methods
        function success = initialize(obj)
            % setup data stream via udp
            % Input arguments: 
            %   None
            %
            
            obj.hNfu = MPL.NfuUdp.getInstance;
            status = obj.hNfu.initialize();
            success = (status == 0);
            
        end
        function close(obj) %#ok<MANU>
            % Since this class didn't explicitly create the NFU object, no
            % need to close it
        end
        function putData(obj, mplAngles)
            % Get current joint angles and send commands to vMpl
            % Input arguments: 
            %   mplAngles - array of joint angles in radians [1,27];
            
            if any(abs(mplAngles)) > pi
                error('mplAngles out of range.  Expected all values to be from -pi to pi')
            end
            
            obj.hNfu.sendAllJoints(mplAngles);            
        end
    end
end
