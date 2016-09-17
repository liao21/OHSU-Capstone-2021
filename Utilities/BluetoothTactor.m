classdef BluetoothTactor < handle
    % Class for interfacing bluetooth vibro tactor controller.  Basic
    % command protocol is: [ 0, 0, 0, 0, 0]
    %
    % Device should be paired through OS prior to connecting.  Passcode for
    % RN41 is '1234'.  Windows 'outgoing' port is the one for device comms
    %
    % Hardware vibrotacile outputs are:
    %
    % 1 = blue/black (Note, this motor is unreliable)
    % 2 = yellow/brown
    % 3 = red/green
    % 4 = orange/purple
    % 5 = yellow/grey
    %
    % Modes can be: 
    %   'DEBUG' - no physcial port opened.  Commands to console only 
    %   'COMX' - created bluetooth port and initializes. transmits to this
    %       port
    %   '' - Null object.  Device is null and no commands issued
    %
    % Note: Modes can be specified in user_config.xml file with keys:
    %   UserConfig.getUserConfigVar('TactorComPort','')
    % TODO: Set refresh rate as user config value
    %   
    properties
        hSerial
        hTimer
        comPort = 'DEBUG'
        echoResponse = 0;
        echoCommand = 1;
        
        tactorVals = [0 0 0 0 0];  % TODO: consider set/get method and check range
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
                % Create null object, but no timer object meaning no
                % refresh occurs
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
                    s = serial(obj.comPort,'Baudrate',57600,'Timeout',0.01,'Terminator',0);
                    fopen(s);
                end
                
                obj.hSerial = s;
            end
            
            fprintf('Done\n');
            
            start(obj.hTimer);
            
        end
        
        function success = setRefreshRate(obj,newRate)
            % set timer update rate in seconds
            
            success = 0;
            if isempty(obj.hTimer)
                warning('Timer Not Initialized');
                return
            elseif strcmp(obj.hTimer.Running,'on')
                % timer is running, stop, then restart
                stop(obj.hTimer);
                obj.hTimer.Period = newRate;
                start(obj.hTimer);
            else
                obj.hTimer.Period = newRate;
            end
            success = 1;
            
        end  
        function transmit(obj)
            % send the current values through the serial port
            % Note this is typically called by timer function
            
            % print out the tactor values, to std. out or serial port
            if strcmpi(obj.comPort, 'DEBUG')
                fprintf('[%d,%d,%d,%d,%d]\n', obj.tactorVals);
            else
                if obj.echoCommand
                    fprintf('[%s.m %s] [%d,%d,%d,%d,%d]\n', ...
                        mfilename, datestr(now,'dd-mmm-yyyy HH:MM:SS.FFF PM'), obj.tactorVals);
                end
                
                try
                    fprintf(obj.hSerial, '[%d,%d,%d,%d,%d]', obj.tactorVals);
                catch ME
                    ME.message
                end
                
                % Read down receive buffer, not interested in response
                nBytes = obj.hSerial.BytesAvailable;
                if nBytes > 0
                    c = char(fread(obj.hSerial,nBytes,'char')');
                    if obj.echoResponse
                        disp(c)
                    end
                end
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
                if ~isempty(obj.hSerial)
                    fclose(obj.hSerial);
                end
            end
            try
                if ~strcmpi(obj.comPort, 'DEBUG')
                    delete(obj.hSerial)
                end
                obj.hSerial = [];
            end
        end
    end
    methods (Static = true)
        function obj = Demo
            %% Demo functionality in DEBUG mode
            
            obj = BluetoothTactor('COM10');
            obj.initialize();
            
        end
    end        
end

