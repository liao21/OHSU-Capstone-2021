classdef MobileTrainer < PatternRecognition.TrainingInterfaceBase
    % Send retrain cues via node.js interface, allowing smartphone training   
    properties
        % Added 7/31/15 Palmer: Mobile support
        MobileRecvPort = 3001;
        MobileSendPort = 3002;
        AddStateMobile = 0;
        % End Palmer
                
        AddState = 0;  % The mode state whether to add new data
        NodeSocket = -1;
        SendSocket = -1;
        
        CurrentClass = 1;
    end
    methods
        function initialize(obj, TrainingManager)

            obj.TrainingManager = TrainingManager;
            
            obj.NodeSocket = PnetClass(obj.MobileRecvPort, obj.MobileSendPort, 'localhost');
            obj.NodeSocket.initialize();
            obj.SendSocket = PnetClass(3003, obj.MobileSendPort, 'localhost');
            obj.SendSocket.initialize();
            obj.AddStateMobile = 0;
            
            % update the gui with our state information
            status = struct();
            status.apiver = '1.0';
            status.current_movement = obj.TrainingManager.getClassNames{obj.CurrentClass};
            status.movements = cellstr(obj.TrainingManager.getClassNames);
            sampleCounts = obj.TrainingManager.getClassLabelCount;
            status.sample_count = num2str(sampleCounts(obj.CurrentClass));
            
            obj.SendSocket.putData(char(savejson('', status, 'NoRowBracket', '1')));
            
        end
        function [doAddData, doTrain] = update(obj)
            
            [doAddData, doTrain] = deal(false);
            
            mobileTrain = false;
            mobileAddData = obj.AddStateMobile;
            
            % Added 7/31/15 Palmer: Mobile support
            if isequal(obj.NodeSocket,-1)
                return
            end
            
            % get any incoming data
            [d, n]= obj.NodeSocket.getAllData;
            if n > 0
                for i = 1:n
                    data = loadjson(char(d{i}));
                    switch data.type
                        case 'prev'
                            obj.CurrentClass = obj.CurrentClass + 1;
                            if obj.CurrentClass > obj.SignalClassifier.NumClasses
                                % wrap to bottom
                                obj.CurrentClass = 1;
                            end
                            mobileTrain = false;
                            mobileAddData = false;
                            notify(obj,'PreviousClass'); % Broadcast notice of event
                        case 'next'
                            obj.CurrentClass = obj.CurrentClass - 1;
                            if obj.CurrentClass < 1
                                % wrap to top
                                obj.CurrentClass = obj.SignalClassifier.NumClasses;
                            end
                            mobileTrain = false;
                            mobileAddData = false;
                            notify(obj,'NextClass'); % Broadcast notice of event
                        case 'start'
                            mobileTrain = false;
                            mobileAddData = true;
                        case 'stop'
                            mobileTrain = true;
                            mobileAddData = false;
                        otherwise
                            fprintf('invalid command received\n');
                    end
                    obj.AddStateMobile = mobileAddData;
                end
                
                % update the gui with our state information
                status = struct();
                status.apiver = '1.0';
                status.current_movement = obj.SignalClassifier.getClassNames{obj.CurrentClass};
                status.movements = cellstr(obj.SignalClassifier.getClassNames);
                sampleCounts = obj.TrainingData.getClassLabelCount;
                status.sample_count = num2str(sampleCounts(obj.CurrentClass));
                
                obj.SendSocket.putData(char(savejson('', status, 'NoRowBracket', '1')));
            end
            % End Palmer
            
            doAddData = mobileAddData;
            doTrain = mobileTrain;
            
        end
        function close(obj)
            if ~isequal(obj.NodeSocket,-1)
                obj.NodeSocket.close;
            end
        end
    end % methods
end % classdef