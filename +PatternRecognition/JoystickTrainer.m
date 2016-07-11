classdef JoystickTrainer < PatternRecognition.TrainingInterfaceBase
    % generate training events using joystick
    properties (Access = public)
        JoystickId                  % System ID for desired joystickJoystick Id (0,1,2,etc)
        JoystickButtonNext          % List of buttons to go to next class
        JoystickButtonPrevious      % List of buttons to go to previous class
        JoystickButtonTrain         % List of buttons to train
        JoystickButtonClear         % List of buttons to clear data
        JoystickAxis                % axis value for changing class. can be (-) to flip axis for next/previous
        JoystickAxisThreshold       % limit until joystick axis registers event
        
        ClassChangeCounts = 15;     % Controls how many updates to wait before changing class

        AnalogEnable = 1;   % Allows class to be changed using either the right-hand gamepad
        % buttons OR the left-hand D-pad or analog
        % stick.  Note if the joystick is an improper
        % mode then this can lead to unexpected rapid
        % scanning through classes
    end
    properties (SetAccess = protected)
        hJoystick       % handle to joystick, used to add data to interface
        hListen         % handle to event listener, displaying current class
    end
    
    methods
        function success = initialize(obj,TrainingManager)
            % Connect joystick and set user preferences
            %
            % Optionally, pass handle to training manager to receive event
            % notifications

            obj.Verbose = 1;
            
            success = false;
            
            obj.JoystickId = UserConfig.getUserConfigVar('joystickId',0);
            obj.JoystickButtonNext = UserConfig.getUserConfigVar('joystickButtonNext',[4 8]);
            obj.JoystickButtonPrevious = UserConfig.getUserConfigVar('joystickButtonPrevious',[2 6]);
            obj.JoystickButtonTrain = UserConfig.getUserConfigVar('joystickButtonTrain',[3 11]);
            obj.JoystickButtonClear = UserConfig.getUserConfigVar('joystickButtonClear',1);
            obj.JoystickAxis = UserConfig.getUserConfigVar('joystickAxis',1);
            obj.JoystickAxisThreshold = UserConfig.getUserConfigVar('joystickAxisThreshold',0.7);
            
            try
                obj.hJoystick = JoyMexClass(obj.JoystickId);
                obj.hJoystick.doSwapAxes = false;
            catch ME
                fprintf('[%s] Warning: Joystick is disabled. \n %s \n',mfilename,ME.message);
                obj.hJoystick = [];
            end
            
            if nargin > 1
                % Optionally, connect to the manager to receive
                % notifications
                obj.hListen = addlistener(TrainingManager,'CurrentClass',@(src,evt) eventCurrentClass(obj,src,evt) );
            end
            
            if ~isempty(obj.hJoystick)
                success = true;
            end
            
        end
        function update(obj)
            % Joystick buttons change classes, another button trains data
            
            if isempty(obj.hJoystick)
                return
            end
            
            % get handle for joystick
            joy = obj.hJoystick;
            
            % synch the joystick deadband with that of the gui
            joy.axisDeadband(obj.JoystickAxis) = obj.JoystickAxisThreshold;
            
            % Check joystick for buttons, if any, add this to training data
            [success, msg] = joy.getdata();
            if ~success
                fprintf('[%s] Error getting Joystick command.  Is it still connected? Error="%s"\n',mfilename,msg);
                obj.close()
                return
            end
            
            % Add data if training button is pressed
            if any(joy.buttonVal(obj.JoystickButtonTrain))
                % Return after this point so that class changes aren't
                % allowed if you are adding data
                if any(joy.buttonsPressed(obj.JoystickButtonTrain))
                    notify(obj,'StartAdd');
                end
                return
            end
            if any(joy.buttonsReleased(obj.JoystickButtonTrain))
                notify(obj,'StopAdd');
                notify(obj,'ForceRetrain');
            end
            
            % change target Class
            
            % go to previous if the button is pressed or if it is held long
            % enough or if analog switching is enabled and the analog axis
            % is depressed in the correct direction
            
            if any(joy.buttonsPressed(obj.JoystickButtonPrevious)) || ...
                    any(joy.buttonsHeldCount(obj.JoystickButtonPrevious) > obj.ClassChangeCounts) || ...
                    (obj.AnalogEnable && ...
                    (sign(obj.JoystickAxis) * joy.axisVal(abs(obj.JoystickAxis)) >= obj.JoystickAxisThreshold) && ...
                    joy.axisHeldCount(obj.JoystickAxis) == 1 || joy.axisHeldCount(obj.JoystickAxis) > obj.ClassChangeCounts )
                % move to next class, redraw, done
                notify(obj,'NextClass'); % Broadcast notice of event
                return
            end
            if any(joy.buttonsPressed(obj.JoystickButtonNext)) || ...
                    any(joy.buttonsHeldCount(obj.JoystickButtonNext) > obj.ClassChangeCounts) || ...
                    (obj.AnalogEnable && ...
                    (sign(obj.JoystickAxis) * joy.axisVal(abs(obj.JoystickAxis)) < -obj.JoystickAxisThreshold) && ...
                    joy.axisHeldCount(obj.JoystickAxis) == 1 || joy.axisHeldCount(obj.JoystickAxis) > obj.ClassChangeCounts )
                notify(obj,'PreviousClass'); % Broadcast notice of event
                return
            end
            
            % Check for clear command
            if joy.buttonVal(obj.JoystickButtonClear)
                notify(obj,'ClearClass'); % Broadcast notice of event
                return
            end
            
        end        
        function close(obj)
            obj.hJoystick.close();
            obj.hJoystick = [];
            
            delete(obj.hListen);
            obj.hListen = [];
        end
    end
    methods (Access = private)
        function eventCurrentClass(obj,src,evt)
            % Read the class change broadcast message
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            if obj.Verbose
                fprintf('[%s] New Class: %d - %s\n',...
                    mfilename, evt.NewClassId, evt.NewClassName);
            end
            
        end
    end
    methods (Static = true)
        function hManager = Test
            %% Test Joystick interface.  Add GUI for monitoring
            
            hManager = PatternRecognition.TrainingManager.Test;
            
            hInterface = PatternRecognition.JoystickTrainer();
            hManager.attachInterface(hInterface);
            hInterface.initialize(hManager);

            hInterface = PatternRecognition.GuiTrainer();
            hManager.attachInterface(hInterface);
            hInterface.initialize(hManager);
            
            StartStopForm([])
            while StartStopForm()
                pause(0.02);
                hManager.update()
            end
            
        end
    end
end
