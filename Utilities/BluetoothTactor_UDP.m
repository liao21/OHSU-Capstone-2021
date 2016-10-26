classdef BluetoothTactor_UDP < handle
    % Class for interfacing bluetooth vibro tactor controller.  Basic
    % command protocol is: [ 0, 0, 0, 0, 0]
    properties
        hUDP
        hTimer
        udpPort = 12001;
        udpIP = '127.0.0.1';
        echoResponse = 0;
        echoCommand = 0;
        maxAngle = 45;
        
        tactorVals = [0 0 0 0 0];
    end
    methods
        function obj = BluetoothTactor_UDP(udpIPAndPort, maxAngleInput)
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
            
            if nargin > 1
                obj.maxAngle = maxAngleInput;
            end
            
        end
        function initialize(obj)
            % Open the port
            
            % create refresh timer
            obj.hTimer = UiTools.create_timer('BluetoothTactorTimer',@(src,evt) obj.transmit );
            obj.hTimer.Period = 0.1;
            
            
            fprintf('Opening %s:%f...',obj.udpIP, obj.udpPort)
            % create the serial port
            
            
            obj.hUDP = pnet('udpsocket', obj.udpPort);
            pnet(obj.hUDP,'udpconnect', obj.udpIP, obj.udpPort)
            obj.udpPort
            obj.udpIP
            
            fprintf('Done\n');
            
            start(obj.hTimer);
            
        end
        
        function transmit(obj)
            % send the current values through the udp port
            newData = sprintf('%d %d %d %d %d', round(double(obj.tactorVals) ./ 255 .* obj.maxAngle)); % !!!!
            
            % print out the tactor values, to std. out or udp port
            try
                pnet(obj.hUDP,'write', newData);
                pnet(obj.hUDP,'writepacket');
                
                if obj.echoCommand
                fprintf('[%s.m %s echo] %s\n', ...
                    mfilename, datestr(now,'dd-mmm-yyyy HH:MM:SS.FFF PM'), newData);
                end
            catch ME
                ME.message
            end
            
            
        end %transmit
        function close(obj)
            try
                stop(obj.hTimer)
            end
            try
                delete(obj.hTimer)
                obj.hTimer = [];
            end
            try
                pnet(obj.hUDP,'close');
                obj.hUDP = [];
            end
            clear mex;
        end
    end
end

