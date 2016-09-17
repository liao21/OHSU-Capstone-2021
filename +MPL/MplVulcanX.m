classdef MplVulcanX < Scenarios.OnlineRetrainer
    % Scenario for controlling JHU/APL MPL
    % Requires Utilities\UiTools
    %
    % This scenario is used with VulcanX running locally to the CAN bus
    %
    % 01-Sept-2010 Armiger: Created
    % 17-May-2013 Armiger: Isolated only the vulcanX components
    properties
        % Handles
        hSource % use for getting kinematic data
        hSink   % send to vulcanx
        
        TactorPort = '';
        hTactors = [];

        DemoMyoElbow = 0;
        DemoMyoShoulder = 0;
        DemoMyoShoulderLeft = 0;
        
        Fref = eye(4);
        
    end
    methods
        function obj = MplVulcanX
            % Creator
            obj.hSink = MPL.MplVulcanXSink();
        end
        function initialize(obj,SignalSource,SignalClassifier,TrainingData)
            
            fprintf('[%s] Starting VulcanX\n',mfilename);
            obj.hSink.initialize();
            
            % Remaining superclass initialize methods
            initialize@Scenarios.OnlineRetrainer(obj,SignalSource,SignalClassifier,TrainingData);
            
            % tactor initialization ************************************
            obj.TactorPort = UserConfig.getUserConfigVar('TactorComPort','');
            
            if any(obj.TactorPort == ':') % this is a IP:port
                obj.hTactors = BluetoothTactor_UDP(obj.TactorPort);
            else
                obj.hTactors = BluetoothTactor(obj.TactorPort);
            end
            
            obj.hTactors.initialize();

            obj.DemoMyoElbow = str2double(UserConfig.getUserConfigVar('myoElbowEnable','0'));
            obj.DemoMyoShoulder = str2double(UserConfig.getUserConfigVar('myoElbowShoulder','0'));
            obj.DemoMyoShoulderLeft = str2double(UserConfig.getUserConfigVar('myoElbowShoulderLeft','0'));
            
        end
        function close(obj)
            % Cleanup and close tactors
            try
                obj.hTactors.close();
            end
            
            try
                obj.hSink.close();
            end
            
        end
        
        function update(obj)
            % This is the main function called by the timer
            try
                % Call superclass update method
                update@Scenarios.OnlineRetrainer(obj);
                
                if ~isempty(obj.SignalSource)
                    obj.update_control();
                end
                
                % update sensory if tactor input provided
                obj.update_sensory();
                
            catch ME
                UiTools.display_error_stack(ME);
            end
            
        end
        function update_control(obj)
            % Get current joint angles and send commands to VulcanX
            %
            % Process steps include:
            %   - get joint angles from the arm
            %       state model
            %   - find the grasp roc number corresponding to the grasp name
            %   - get joint angles based on roc table
            %       - if it's a whole arm roc, it should overwrite the
            %       upper arm joint values
            
            m = obj.ArmStateModel;
            rocValue = m.structState(m.RocStateId).Value;
            rocId = m.structState(m.RocStateId).State;
            if isa(rocId,'Controls.GraspTypes')
                % convert char grasp class name (e.g. 'Spherical') to numerical mpl
                % grasp value (e.g. 7)
                rocId = MPL.GraspConverter.graspLookup(rocId);
            end
            
            mplAngles = zeros(1,27);
            mplAngles(1:7) = [m.structState(1:7).Value];
            
            % Generate vulcanX message.  If local roc table exists, use it
            
            % check bounds
            rocValue = max(min(rocValue,1),0);
            % lookup the Roc id and find the right table
            iEntry = (rocId == [obj.RocTable(:).id]);
            if sum(iEntry) < 1
                error('Roc Id %d not found',rocId);
            elseif sum(iEntry) > 1
                warning('More than 1 Roc Tables share the id # %d',rocId);
                roc = obj.RocTable(find(iEntry,1,'first'));
            else
                roc = obj.RocTable(iEntry);
            end
            
            % perform local interpolation
            mplAngles(roc.joints) = interp1(roc.waypoint,roc.angles,rocValue);
            
            
            
            if obj.DemoMyoElbow
                % Demo for using myo band for elbow angle
                try
                    ang = obj.SignalSource.getEulerAngles;
                    EL = ang(2) + 90;
                    EL = EL * pi/180;
                    mplAngles(4) = EL;
                end
            end
            if obj.DemoMyoShoulder
                
                R = obj.SignalSource.getRotationMatrix();
                F = [R [0; 0; 0]; 0 0 0 1];
                
                if isequal(obj.Fref, eye(4))
                    % set offset the first time
                    obj.Fref = F;
                end
                
                newXYZ = LinAlg.decompose_R(pinv(obj.Fref)*F);
                
                if obj.DemoMyoShoulderLeft
                    % left side angle decomposition
                    mplAngles(1) = -newXYZ(3) * pi / 180;
                    mplAngles(2) = -newXYZ(2) * pi / 180;
                    mplAngles(3) = -newXYZ(1) * pi / 180;
                else
                    % right side angle decomposition
                    mplAngles(1) = newXYZ(3) * pi / 180;
                    mplAngles(2) = -newXYZ(2) * pi / 180;
                    mplAngles(3) = newXYZ(1) * pi / 180;
                end
            end
            
            obj.hSink.putData(mplAngles);
            
        end
        function update_sensory(obj)
            
            %%
            try
                % percepts will be sent to the local port
                percepts = obj.hSink.getPercepts; %gets latest packets
            catch ME
                warning('MplVulcanXSink:badPercepts','MplVulcanXSink.getPercepts FAILED: %s',...
                    ME.message);
                return
            end
            
            if ~isempty(obj.TactorPort) && ~isempty(percepts)
                % parse the percept packet
                
                % this function does two things: transfer function of
                % sensor to tactor command, then transmit command.
                % Consider isolating functionality
                
                % extract torqueVals
                % Note Flip signs here if needed
                tactorVals = zeros(1,5);
                indexSensorVal = double(percepts.jointPercepts.torque(MPL.EnumArm.INDEX_MCP));
                middleSensorVal = double(percepts.jointPercepts.torque(MPL.EnumArm.MIDDLE_MCP));
                ringSensorVal = double(percepts.jointPercepts.torque(MPL.EnumArm.RING_MCP));
                littleSensorVal = double(percepts.jointPercepts.torque(MPL.EnumArm.LITTLE_MCP));
                thumbSensorVal = double(percepts.jointPercepts.torque(MPL.EnumArm.THUMB_MCP));
                
                % TODO: Setup GUI to display sensor ranges and confirm
                % function
                
                if obj.Verbose
                fprintf('MPL Percepts: LittleMCP=%6.3f | RingMCP=%6.3f | MiddleMCP=%6.3f | IndexMCP=%6.3f | ThumbMCP=%6.3f\n',...
                    littleSensorVal,ringSensorVal,middleSensorVal,indexSensorVal,thumbSensorVal);
                end
                % start sensor to tactor command map
                thumbSensorLowHigh = [0.1 0.2];
                thumbActuatorLowHigh = [0 255];
                indexSensorLowHigh = [0 0.1];
                indexActuatorLowHigh = [0 255];
                middleSensorLowHigh = [0 0.1];
                middleActuatorLowHigh = [0 255];
                ringSensorLowHigh = [0 0.1];
                ringActuatorLowHigh = [0 255];
                littleSensorLowHigh = [0 0.1];
                littleActuatorLowHigh = [0 255];
                
                % check range for interpolation
                indexSensorVal = min(max(indexSensorVal,min(indexSensorLowHigh)),max(indexSensorLowHigh));
                middleSensorVal = min(max(middleSensorVal,min(middleSensorLowHigh)),max(middleSensorLowHigh));
                ringSensorVal = min(max(ringSensorVal,min(ringSensorLowHigh)),max(ringSensorLowHigh));
                littleSensorVal = min(max(littleSensorVal,min(littleSensorLowHigh)),max(littleSensorLowHigh));
                thumbSensorVal = min(max(thumbSensorVal,min(thumbSensorLowHigh)),max(thumbSensorLowHigh));
                
                % scale the torque values and perform mapping
                tactorVals(1) = interp1(littleSensorLowHigh,littleActuatorLowHigh,littleSensorVal,'linear');
                tactorVals(2) = interp1(ringSensorLowHigh,ringActuatorLowHigh,ringSensorVal,'linear');
                tactorVals(3) = interp1(middleSensorLowHigh,middleActuatorLowHigh,middleSensorVal,'linear');
                tactorVals(4) = interp1(indexSensorLowHigh,indexActuatorLowHigh,indexSensorVal,'linear');
                tactorVals(5) = interp1(thumbSensorLowHigh,thumbActuatorLowHigh,thumbSensorVal,'linear');
                
                % fprintf('[%d,%d,%d,%d,%d]\n', round(tactorVals));
                
                % send tactor commands to device
                obj.hTactors.tactorVals = double(round(tactorVals));
            end
        end
    end
end

