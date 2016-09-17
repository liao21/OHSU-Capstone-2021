classdef JoyMexClass < handle
    % Class Wrapper for JoyMex function
    % Emulates JavaJoystick class, but without haptic effect, however this has
    % been tested on both win32 and win64 systems
    % Created:  6/25/2011 Armiger
    %
    % Additionally, added functionality to get info about buttons being
    % held, released, etc which is useful dynamically and to prevent
    % 'bouncing' of mode switches etc.
    %
    % E.g. check property obj.buttonsReleased to only get the event when
    % the button comes up.  obj.buttonsPressed to only get the initial
    % falling state, or obj.buttonsHeld and obj.buttonsHeldCount to
    % determine long-term holds
    %
    % 
    
    properties
        doSwapAxes = true;
        name
        % double array of number the normalized dead for each axis
        axisDeadband
    end
    properties (SetAccess = private)
        id      % gamepad device number id

        nButtons
        nAxes
        nPov
        buttonVal       % Instantaneous button values
        axisVal         % Instantaneous axis values
        povVal          % Instantaneous pov value
        
        IsInitialized = false;
        
        % Logical array of buttons that went from up to down on last update 
        buttonsPressed
        
        % Logical array of buttons that went from down to up on last update 
        buttonsReleased

        % Logical array of buttons that went from down to down (held)
        buttonsHeld

        % double array of number of updates each button has been down
        buttonsHeldCount

        % Logical array of axes outside of deadband
        axisActive

        % Logical array of axes that went from up to down on last update 
        axisPressed
        
        % Logical array of axes that went from down to up on last update 
        axisReleased

        % Logical array of axes that went from down to down (held)
        axisHeld

        % double array of number of updates each axis has been down
        axisHeldCount
        
        % Internal state of axis and buttons at last update
        axisValLast
        buttonValLast
        
    end
    methods
        function obj = JoyMexClass(joyId)
            % JoyMexClass(joyId)
            % joyId should be a number 0 to 3 for which joystick to select
            %
            % Example Usage:
            %    myJoy = JoyMexClass(0)
            %    myJoy.preview
            %
            %    myJoy.getdata()
            %    myJoy.buttonVal(4)
            %    myJoy.axisVal(2)
            
            if nargin < 1
                obj.id = 0;
            else
                obj.id = joyId;
            end
            
            obj.initialize();
        end
        
        function initialize(obj)
            
            if obj.IsInitialized
                fprintf('Joystick Id = %d already initialized\n', obj.id);
                return
            end
            
            try
                % Note: Calling init twice will result in error
                fprintf('[%s] ',mfilename);
                JoyMEX('init',obj.id); 
            catch ME
                if strcmp(ME.identifier,'JoyMEX:NotFound')
                    error('Error Initializing Joystick Id = %d\n Error was: "%s"',obj.id,ME.message);
                else
                    disp(ME.message);
                end
            end
            
            % Get capabilities.  In earlier versions these were accurate,
            % but the mex file forces values 6 axes and 128 buttons
            obj.name = 'Unknown Joystick';
            obj.nAxes = 6;
            obj.nButtons = 128;
            obj.nPov = 0;

            obj.axisDeadband = 0.02*ones(1,obj.nAxes);
            
            % initialize joystick activity counters
            obj.buttonsHeldCount = zeros(1,obj.nButtons);
            obj.axisHeldCount = zeros(1,obj.nAxes);
            
            % call once to complete initialization
            obj.update();
            
            obj.IsInitialized = true;
        end
        function update(obj)
            % Call MEX Function
            
            % get current state
            [obj.axisVal, obj.buttonVal] = JoyMEX(obj.id);
            if obj.doSwapAxes
                obj.axisVal([1 2 3 4 5 6]) = obj.axisVal([2 1 6 3 4 5]);
            end

            % Handle the init case with unknown state
            if isempty(obj.axisValLast)
                obj.axisValLast = obj.axisVal;
            end
            if isempty(obj.buttonValLast)
                obj.buttonValLast = obj.buttonVal;
            end
            
            % Compare the two states to determine what changed
            buttonDiff = obj.buttonVal - obj.buttonValLast;
            obj.buttonsPressed = buttonDiff == 1;
            obj.buttonsReleased = buttonDiff == -1;

            % this could be | to return true the first press rather than
            % update#2 which is the first hold.  For that, the user can
            % just read obj.buttonVal
            obj.buttonsHeld = obj.buttonVal & obj.buttonValLast; 
            
            obj.buttonsHeldCount(obj.buttonsReleased) = 0;
            obj.buttonsHeldCount(obj.buttonsPressed) = 1;
            obj.buttonsHeldCount(obj.buttonsHeld) = obj.buttonsHeldCount(obj.buttonsHeld) + 1;

            % Compute difference of axis value
            % Axes outside deadband
            obj.axisActive = abs(obj.axisVal) > obj.axisDeadband;
            % Axes outside deadband @ last update
            axisActiveLast = abs(obj.axisValLast) > obj.axisDeadband;
            % Axis activation changes
            axisDiff = obj.axisActive - axisActiveLast;

            obj.axisPressed = axisDiff == 1;
            obj.axisReleased = axisDiff == -1;
            obj.axisHeld = obj.axisActive & axisActiveLast;
            
            obj.axisHeldCount(obj.axisReleased) = 0;
            obj.axisHeldCount(obj.axisPressed) = 1;
            obj.axisHeldCount(obj.axisHeld) = obj.axisHeldCount(obj.axisHeld) + 1;
            
            % Store state for next update
            obj.axisValLast = obj.axisVal;
            obj.buttonValLast = obj.buttonVal;

        end
        function resetButtonCounter(obj, id, val)
            % Reset the 'hold' timer for the joystick.
            % with no args it sets all buttons to 0
            % with 'id' only the specified button is set
            % with 'val' the counter is set to the value instead of zero
            
            
            if nargin < 3
                val = 0;
            end
            
            if nargin < 2
                obj.buttonsHeldCount(:) = val;
            else
                obj.buttonsHeldCount(id) = val;
            end
        end
        function [success, msg] = getdata(obj)
            %[success, msg] = getdata(obj)
            % Call JoyMex function to get latest button and axis values.
            % Returns true on successful read
            % If unsuccessful, error message is passed back

            success = false;
            msg = '';
            
            try
                update(obj);
            catch ME
                msg = ME.message;
                return
            end
            
            obj.povVal = -1;
                        
            success = true;
            
        end
        function preview(obj,timeout)
            % Run a loop to display joystick values in real time
            % preview(obj,timeout)
            % Default timeout is 15 sec
            
            if nargin < 2
                timeout = 15;
            end
            
            t = tic;
            while toc(t) < timeout
                
                getdata(obj);
                
                for i = 1:length(obj.axisVal)
                    fprintf('| %d ',i)
                    fprintf('%6.2f ',obj.axisVal(i));
                end
                
                for i = 1:obj.nPov
                    fprintf('| POV %d: ',i);
                    fprintf('%6.2f ',obj.povVal(i));
                end
                
                for i = 1:length(obj.buttonVal)
                    if obj.buttonVal(i)
                        fprintf('| %s ',num2str(i));
                    end
                end
                fprintf('\n')
                drawnow
            end
            disp('Done')
        end
    end
    methods (Static=true)
        function close
            % Cleanup all joysticks.
            clear('JoyMEX')
        end
    end
end
