classdef TactorUdp < handle
    % Class for interfacing bluetooth vibro tactor controller.  Basic
    % command protocol is: [ 0, 0, 0, 0, 0]
    % values sent to C# executable are 5 floats with range [0-255]
    properties
        hUDP

        udpPort = 8089;
        udpIP = '127.0.0.1';
        echoResponse = 0;
        echoCommand = 0;
        maxAngle = 45;
        
        tactorVals = [0 0 0 0 0];
    end
    methods
        function obj = TactorUdp(udpIPAndPort)
            % Constructor.  Provide a string based name for the com port
            % (e.g. COM5)
            if nargin > 0
                try
                    udpIPAndPort = strsplit(udpIPAndPort, ':');
                    obj.udpIP = udpIPAndPort{1};
                    obj.udpPort = str2double(udpIPAndPort{2});
                catch
                    warning('invalid IP and port, using localhost:12001');
                end
            end
            
        end
        function initialize(obj)
            % Open the port
            obj.hUDP = PnetClass(8090, obj.udpPort, obj.udpIP);
            obj.hUDP.initialize();
        end
        
        function transmit(obj)
            % send the current values through the udp port

            cmd = obj.tactorVals;
            % validate inputs
            cmd = round(cmd);
            cmd(cmd > 255) = 255;
            cmd(cmd < 0) = 0;
            
            obj.hUDP.putData(single(cmd))
            
            if obj.echoCommand
                fprintf('[%s.m %s echo] %f %f %f %f %f\n', ...
                    mfilename, datestr(now,'dd-mmm-yyyy HH:MM:SS.FFF PM'), cmd);
            end
            
            
        end %transmit
        function close(obj)
            try
                obj.hUDP.close();
                obj.hUDP = [];
            end
        end
    end
end

