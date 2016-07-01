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
            obj.hTactors = BluetoothTactor(obj.TactorPort);
            obj.hTactors.initialize();
            
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
            
            obj.hSink.putData(mplAngles);
            
        end
        function update_sensory(obj)
            
            try
                % percepts will be sent to the local port
                percepts = obj.hSink.getPercepts; %gets latest packets
            catch ME
                warning('MplVulcanX:NoPercepts',ME.message);
            end
            
            if ~isempty(obj.TactorPort)
                % parse the percept packet
                
                % extract torqueVals
                tactorVals = zeros(1,5);
                sensorVals = percepts.jointPercepts.torque([...
                    MPL.EnumArm.THUMB_MCP,...
                    MPL.EnumArm.INDEX_MCP,...
                    MPL.EnumArm.MIDDLE_MCP,...
                    MPL.EnumArm.RING_MCP,...
                    MPL.EnumArm.LITTLE_MCP]);
                minSensor = 0.05;
                sensorVals(1) = -sensorVals(1);
                sensorVals = max(sensorVals,minSensor);
                
                % scale the torque values and perform mapping
                tactorVals(5) = interp1([minSensor 0.1],[0 255],sensorVals(1),'linear',255);
                tactorVals(4) = interp1([minSensor 0.3],[0 255],sensorVals(2),'linear',255);
                tactorVals(3) = interp1([minSensor 0.3],[0 255],sensorVals(3),'linear',255);
                tactorVals(2) = interp1([minSensor 0.3],[0 255],sensorVals(4),'linear',255);
                tactorVals(1) = interp1([minSensor 0.3],[0 255],sensorVals(5),'linear',255);
                
                obj.hTactors.tactorVals = double(round(tactorVals));
            end
        end
    end
end
