classdef EndpointController < Scenarios.OnlineRetrainer
    % Scenario for controlling JHU/APL MPL
    % Requires Utilities\UiTools
    %
    % This scenario is used with VulcanX running locally to the CAN bus
    %
    % 01-Sept-2010 Armiger: Created
    % 17-May-2013 Armiger: Isolated only the vulcanX components
    properties
        % Handles
        hMud;
        hUdp;  % Handle to Udp port.  local port is setup to receive percepts and send to command port
        hIntentUdp;  % Handle to Intent Udp port. 

        VulcanXAddress = '127.0.0.1';   % VulcanX IP (127.0.0.1)
        VulcanXCmdPort = 9027;          % MUD Port (L=9024 R=9027)
        VulcanXLocalPort = 25001;       % Percept Port (L=25101 R=25001)
        
        IntentAddress = '127.0.0.1';    % IP for class info streaming (127.0.0.1)
        IntentDestinationPort = 9094;   % Dest Port for class info streaming (L=9094 R=9095)
        IntentSourcePort = 58010;       % Src Port for class info streaming 

        IsRightSide = 0;
        
    end
    methods
        function obj = EndpointController
            % Creator
        end
        function initialize(obj,SignalSource,SignalClassifier,TrainingData)
            
            % Extend Scenario model to include communications with the
            % limb system via vulcanX or the NFU
            
            fprintf('[%s] Starting Endpoint Controller\n',mfilename);

            % Create MUD message translator
            obj.hMud = MPL.MudCommandEncoder();
            
            % PnetClass(localPort,remotePort,remoteIP)
            obj.hUdp = PnetClass(...
                obj.VulcanXLocalPort,obj.VulcanXCmdPort,obj.VulcanXAddress);
            obj.hUdp.initialize();

            % setup udp for intent streaming
            obj.hIntentUdp = PnetClass(...
                obj.IntentSourcePort,obj.IntentDestinationPort,obj.IntentAddress);
            obj.hIntentUdp.initialize();
            
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
                
                % Stream intent info:
                % obj.Intent.classOut = classOut;
                % obj.Intent.voteDecision = voteDecision;
                % obj.Intent.className = className;
                % obj.Intent.prSpeed = prSpeed;
                % obj.Intent.rawEmg = rawEmg;
                % obj.Intent.windowData = windowData;
                % obj.Intent.features2D = features2D;
                %obj.hIntentUdp.putData(uint8(obj.Intent.voteDecision));
                obj.hIntentUdp.putData(char(obj.Intent.className));
                
            catch ME
                UiTools.display_error_stack(ME);
            end
            
        end
        function update_control(obj)
            % Get current joint angles and send commands to VulcanX
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
            m.velocity([MPL.EnumArm.WRIST_ROT, MPL.EnumArm.WRIST_FE, MPL.EnumArm.WRIST_AB_AD])
            
            % check for endpoint control command.  Currently hijacking the
            % state variable
            
            if length(rocId) >= 8
                fprintf('Endpoint: %f %f %f %f %f %f %f %f\n',rocId)
                endPtVelocities = rocId(1:3)';
                endPtOrientationVelocities = rocId(4:6)';
                % rocMode = 1;
                % rocTableIDs = 1;
                % rocTableValues = 0;
                % rocWeights  = 1;
                rocMode = obj.hMud.ROC_MODE_VELOCITY;
                rocTableIDs = 1;
                rocTableValues = rocId(8);
                rocWeights  = 1;
                
                msg = obj.hMud.EndpointVelocity6HandRocGrasps( ...
                    endPtVelocities, endPtOrientationVelocities, ...
                    rocMode, rocTableIDs, rocTableValues, rocWeights);
                
                obj.hUdp.putData(msg);
                return
            end

            if isa(rocId,'Controls.GraspTypes')
                % convert char grasp class name (e.g. 'Spherical') to numerical mpl
                % grasp value (e.g. 7)
                rocId = MPL.GraspConverter.graspLookup(rocId);
            end
            
            % Note the joint ids for the MPL are different than the older
            % action bus definition
            % jointIds = [
            %     action_bus_enum.Shoulder_FE
            %     action_bus_enum.Shoulder_AbAd
            %     action_bus_enum.Humeral_Rot
            %     action_bus_enum.Elbow
            %     action_bus_enum.Wrist_Rot
            %     action_bus_enum.Wrist_Dev
            %     action_bus_enum.Wrist_FE
            %     ];
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
            
                        
            % Generate vulcanX message.  If local roc table exists, use it
            if ~isempty(obj.RocTable)

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

                % generate MUD message using joint angles
                msg = obj.hMud.AllJointsPosVelCmd(mplAngles(1:7),zeros(1,7),mplAngles(8:27),zeros(1,20));
            else
                % generate MUD message using joint angles and ROC
                % parameters
                msg = obj.hMud.ArmPosVelHandRocGrasps(mplAngles(1:7),zeros(1,7),1,rocId,rocVal,1);
            end
            
            % write message
            obj.hUdp.putData(msg);
            
        end
        function update_sensory(obj)
            
            % percepts will be sent to the local port
            p = obj.hUdp.getData; %gets latest packets
            if ~isempty(p) && length(p) >= 324
                r = reshape(typecast(p(1:324),'single'),3,27);
                if obj.Verbose > 1
                    fprintf('[%s] PerceptAngles: ',mfilename);
                    fprintf('%6.4f ',r(1,:)');
                    fprintf('\n');
                end
                
            else
                % No new data
            end
        
        end
        
    end
end

