classdef MplUnity < Scenarios.OnlineRetrainer
    % Scenario for controlling JHU/APL vMPL Unity Environment
    % Requires Utilities\UiTools
    %
    % This scenario is used with the vMPL system
    %
    % 29-Apr-2015 Armiger: Created
    properties
        % Handles
        hSink;  % Handle to Udp port.  local port is setup to receive percepts and send to command port
        
        DemoMyoElbow = 0;
        DemoMyoShoulder = 0;
        DemoMyoShoulderLeft = 0;
        
        Fref = eye(4);
        Fref2 = eye(4);
        
    end
    methods
        function initialize(obj,SignalSource,SignalClassifier,TrainingData)
            
            % Extend Scenario model to include communications with the
            % limb system via vMpl or the NFU
            
            fprintf('[%s] Starting vMpl\n',mfilename);
            
            %  Create the udp transmission via pnet
            obj.hSink = MPL.MplUnitySink;
            success = obj.hSink.initialize();
            if ~success
                return
            end
            
            obj.DemoMyoElbow = str2double(UserConfig.getUserConfigVar('myoElbowEnable','0'));
            obj.DemoMyoShoulder = str2double(UserConfig.getUserConfigVar('myoElbowShoulder','0'));
            obj.DemoMyoShoulderLeft = str2double(UserConfig.getUserConfigVar('myoElbowShoulderLeft','0'));
            
            obj.getRocConfig();
            
            % Remaining superclass initialize methods
            initialize@Scenarios.OnlineRetrainer(obj,SignalSource,SignalClassifier,TrainingData);
            
        end
        function update(obj)
            % This is the main funciton called by the timer
            try
                update@Scenarios.OnlineRetrainer(obj); % Call superclass update method
                
                if ~isempty(obj.SignalSource)
                    obj.update_control();
                end
                
                % obj.update_sensory();
                
                if obj.Verbose
                    % print backspace and new line
                    fprintf('\b\n');
                end
                
            catch ME
                UiTools.display_error_stack(ME);
            end
            
        end
        function update_control(obj)
            % Get current joint angles and send commands to vMpl
            %
            % Process steps include:
            %   - get joint angles from the JointAngles properties
            %       -Alternatively this could / should come from the arm
            %       state model
            %   - find the grasp roc number corresponding to the grasp name
            %   - Apply any manual override changes
            %       - TODO, remove this
            %   - get joint angles based on roc table
            %       - Currently only applies to hand.
            %       - if it's a whole arm roc, it should overwrite the
            %       upper arm joint values
            
            m = obj.ArmStateModel;
            rocValue = m.structState(m.RocStateId).Value;
            rocId = m.structState(m.RocStateId).State;
            
            % check for endpoint control command.  Currently hijacking the
            % state variable
            
            if length(rocId) >= 3
                warning('Endpoint Mode not supported by MplUnity');
                return
            end
            
            if isa(rocId,'Controls.GraspTypes')
                % convert char grasp class name (e.g. 'Spherical') to numerical mpl
                % grasp value (e.g. 7)
                rocId = MPL.GraspConverter.graspLookup(rocId, {obj.RocTable.name});
            end
            
            % Note the joint ids for the MPL are different than the older
            % action bus definition
            jointIds = [
                MPL.EnumArm.SHOULDER_FE
                MPL.EnumArm.SHOULDER_AB_AD
                MPL.EnumArm.HUMERAL_ROT
                MPL.EnumArm.ELBOW
                MPL.EnumArm.WRIST_ROT
                MPL.EnumArm.WRIST_AB_AD
                MPL.EnumArm.WRIST_FE
                ];
            
            mplAngles = zeros(1,27);
            %mplAngles(1:7) = obj.JointAnglesDegrees(jointIds) * pi/180;
            mplAngles(1:7) = [m.structState(jointIds).Value];
            
            % Generate vMpl message.  If local roc table exists, use it
            
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
            
            % one myo transradial case
            if obj.DemoMyoElbow
                % Demo for using myo band for elbow angle
                try
                    if obj.DemoMyoShoulder
                        % if using motion control for both elbow and
                        % shoulder, get elbow from 'lower' band
                        % ang = obj.SignalSource.SecondMyo.getEulerAngles;
                        %[R1, R2] = obj.SignalSource.getRotationMatrix();
                        %R2 = pinv(R2)*R1
                        %ang = LinAlg.decompose_R(R2);
                        
                        % two myo TR case elbow determined later
                        ang = [0 -90 0];
                    else                        
                        ang = obj.SignalSource.getEulerAngles;
                    end
                    EL = ang(2) + 90;
                    EL = EL * pi/180;
                    mplAngles(4) = EL;
                end
            end
            
            % Trans humeral case
            if obj.DemoMyoShoulder && ~obj.DemoMyoElbow
                
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
            
            % two myo transradial case
            if obj.DemoMyoShoulder && obj.DemoMyoElbow
                
                [R, R2] = obj.SignalSource.getRotationMatrix();
                
                F = [R [0; 0; 0]; 0 0 0 1];
                if isequal(obj.Fref, eye(4))
                    obj.Fref = F;
                end
                newXYZ = LinAlg.decompose_R(pinv(obj.Fref)*F);
                
                % Compute relative orientation between myo 1 and myo 2
                F2 = [R2 [0; 0; 0]; 0 0 0 1];
                if isequal(obj.Fref2, eye(4))
                    obj.Fref2 = F2;
                end
               
                
                relXYZ = LinAlg.decompose_R(pinv(pinv(obj.Fref)*F)*pinv(obj.Fref2)*F2)
                EL = relXYZ(3);
                
                if obj.DemoMyoShoulderLeft
                    % left side angle decomposition
                    mplAngles(1) = -newXYZ(3) * pi / 180;
                    mplAngles(2) = -newXYZ(2) * pi / 180;
                    mplAngles(3) = -newXYZ(1) * pi / 180;
                    mplAngles(4) = -EL * pi/180;
                else
                    mplAngles(1) = newXYZ(3) * pi/180;
                    mplAngles(2) = -newXYZ(2) * pi/180;
                    mplAngles(3) = newXYZ(1) * pi/180;
                    mplAngles(4) = EL * pi/180;
                end
                mplAngles(1:4);
                
            end
            obj.hSink.putData(mplAngles);
            
        end
        function update_sensory(obj)
            % Not implemented
        end
    end
end
