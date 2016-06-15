classdef BluetoothTactor < handle
    % Class for interfacing bluetooth vibro tactor controller.  Basic
    % command protocol is: [ 0, 0, 0, 0, 0]
    properties
        hSerial
        hTimer
        comPort = 'DEBUG'
        echoResponse = 0;
        
        tactorVals = [0 0 0 0 0];
    end
    methods
        function obj = BluetoothTactor(comPort)
            % Constructor.  Provide a string based name for the com port
            % (e.g. COM5)
            if nargin > 0
                obj.comPort = comPort;
            end
            
        end
        function initialize(obj)
            % Open the port

            % create refresh timer
            obj.hTimer = UiTools.create_timer('BluetoothTactorTimer',@(src,evt) obj.transmit );
            obj.hTimer.Period = 0.1;
            
            
            if isempty(obj.comPort)
                % Create simulated port
                obj.hSerial = [];
                return
            elseif strcmpi(obj.comPort, 'debug')
                % Create simulated port
                obj.hSerial = 'DEBUG';
                fprintf('Opening port %s...',obj.comPort)
            else
                fprintf('Opening port %s...',obj.comPort)
                % create the serial port
                s = instrfind('port',obj.comPort);
                if isempty(s)
                    s = serial(obj.comPort,'Baudrate',57600,'Timeout',0.5,'Terminator',0);
                    fopen(s);
                end
                
                obj.hSerial = s;
            end
            
            fprintf('Done\n');
                        
            start(obj.hTimer);
            
        end
        
        function transmit(obj)
            % send the current values through the serial port
            
            % print out the tactor values, to std. out or serial port
            if ~strcmpi(obj.comPort, 'DEBUG')
                fprintf(obj.hSerial, '[%d,%d,%d,%d,%d]', obj.tactorVals);
                fprintf('[%s] [%d,%d,%d,%d,%d]\n', mfilename, obj.tactorVals);
                
                % Read down receive buffer, not interested in response
                nBytes = obj.hSerial.BytesAvailable;
                if nBytes > 0
                    c = char(fread(obj.hSerial,nBytes,'char')');
                    if obj.echoResponse
                        disp(c)
                    end
                end
            else
                fprintf('[%d,%d,%d,%d,%d]\n', obj.tactorVals);
            end
            
        end %transmit
        function close(obj)
            try
                stop(obj.hTimer)
            end
            try
                delete(obj.hTimer)
            end
            try
                if ~isempty(obj.hSerial)
                    fclose(obj.hSerial);
                end
            end
            try
                delete(obj.hSerial)
            end
        end
    end
end

