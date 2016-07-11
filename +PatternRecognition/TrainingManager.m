classdef TrainingManager < handle
    % Class for handling online retraining
    % Container for holding various training interface objects
    % E.g. GUI, Joysitck, mobile App
    % Handles all the connections of GUIs, joysticks, mobile apps etc.
    %     events
    %         % Events signify to a GUI that the training event occured
    %         DataCountChange
    %     end
    properties
        SignalSource        % Required because manager should store data from live source
        SignalClassifier    % Required because manager should trigger a retrain event
        TrainingData        % Required becuase manager should store the latest data
        Interfaces = {};  % Typically should inherit from TrainingInterfaceBase
        
        % if an interface adds data, trigger a retrain event when exceeding
        % this value
        RetrainCounts = 25;         % Controls how many samples to wait before auto retrain
        
        Verbose = 1; % Controls message verbosity to console
    end
    properties (SetAccess = protected)
        ClassId = 7;
        RetrainCounter;
    end
    properties (Access = private)
        AddState = 0;  % The mode state whether to add new data
    end
    events
        DataCountChange     % Called when data added
        CurrentClass        % Called when current class changed
    end
    
    methods (Access = private)
        % Private functions mainly for handling events from the optional
        % GUI
        function eventClassChange(obj,src,evt)
            % change the class based on input from the GUI.  The changed
            % value can be read from the event source
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            if obj.Verbose
                fprintf('[%s] New Class: %d - %s\n',...
                    mfilename, evt.NewClassId, evt.NewClassName);
            end
            
            assert(evt.NewClassId > 0,'New class must be 1 or greater');
            assert(evt.NewClassId <= length(obj.getClassNames),'New class must be <= NumClasses');
            
            obj.ClassId = evt.NewClassId;
            
            ClassNames = obj.getClassNames;
            evtdata = PatternRecognition.ChangeClassEventData(...
                obj.ClassId,ClassNames{obj.ClassId});
            notify(obj,'CurrentClass',evtdata);
            
        end
        function eventNext(obj,src,evt)
            % Increment the class value
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            
            obj.ClassId = obj.ClassId + 1;
            if obj.ClassId > length(obj.getClassNames)
                obj.ClassId = 1;
            end
            
            ClassNames = obj.getClassNames;
            evtdata = PatternRecognition.ChangeClassEventData(...
                obj.ClassId,ClassNames{obj.ClassId});
            notify(obj,'CurrentClass',evtdata);
            
        end
        function eventPrevious(obj,src,evt)
            % Increment the class value
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            
            obj.ClassId = obj.ClassId - 1;
            if obj.ClassId < 1
                obj.ClassId = length(obj.getClassNames);
            end
            
            ClassNames = obj.getClassNames;
            evtdata = PatternRecognition.ChangeClassEventData(...
                obj.ClassId,ClassNames{obj.ClassId});
            notify(obj,'CurrentClass',evtdata);
            
        end
        function eventStartAdd(obj,src,evt)
            % change add data mode
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            
            obj.AddState = 1;
        end
        function eventStopAdd(obj,src,evt)
            % change add data mode
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            
            obj.AddState = 0;
        end
        function eventClearClass(obj,src,evt)
            % clear the data and retrain
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            
            clearCurrentClassData(obj);
            retrain(obj);
        end
        function eventRetrain(obj,src,evt)
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            retrain(obj);
        end
    end
    
    methods
        function obj = TrainingManager(source, classifier, data)
            % Creator
            initialize(obj,source,classifier,data);
        end
        function initialize(obj)
            obj.SignalSource = source;
            obj.SignalClassifier = classifier;
            obj.TrainingData = data;
        end
        function attachInterface(obj,hInterface)
            
            % TODO: Prevent re-add
            obj.Interfaces = cat(1,obj.Interfaces,{hInterface});
            
            % subcribe to the interface's events
            addlistener(hInterface,'ClearClass',    @(src,evt)eventClearClass(obj,src,evt));
            addlistener(hInterface,'ClassChange',   @(src,evt)eventClassChange(obj,src,evt));
            addlistener(hInterface,'NextClass',     @(src,evt)eventNext(obj,src,evt));
            addlistener(hInterface,'PreviousClass', @(src,evt)eventPrevious(obj,src,evt));
            addlistener(hInterface,'StartAdd',      @(src,evt)eventStartAdd(obj,src,evt));
            addlistener(hInterface,'StopAdd',       @(src,evt)eventStopAdd(obj,src,evt));
            addlistener(hInterface,'ForceRetrain',  @(src,evt)eventRetrain(obj,src,evt));
            
            % When a new interface is added, it might set the current
            % class on startup
            %obj.ClassId = obj.Interface
            
        end
        function allClassNames = getClassNames(obj)
            % get class names from the data object
            allClassNames = obj.TrainingData.ClassNames();
        end
        function classLabelCount = getClassLabelCount(obj)
            % get class names from the data object
            classLabelCount = obj.TrainingData.getClassLabelCount();
        end
        function update(obj)
            % get commands from all interfaces
            
            % update interfaces
            for i = 1:length(obj.Interfaces)
                try
                    obj.Interfaces{i}.update();
                catch ME
                    warning(ME.message)
                end
            end
            
            % Check for add command
            addData = obj.AddState;
            
            if addData
                obj.RetrainCounter = obj.RetrainCounter + 1;
            else
                obj.RetrainCounter = 0;
            end
            
            if obj.RetrainCounter > obj.RetrainCounts
                obj.RetrainCounter = 1;
                obj.retrain();
            end
            
            % If training, add the current data as training data to
            % that class
            if addData
                % Add a new sample of data based on the ClassId property
                assert(~isempty(obj.ClassId),'No class is selected to tag new data');
                
                % TODO: signals might have already been acquired by the
                % signal source.  Provide a way to set the current signals
                % without re-running source
                
                % Get intent from data stream
                [~,~,~,~,rawEmg,~,features] ...
                    = getIntent(obj.SignalSource,obj.SignalClassifier);
                
                obj.TrainingData.addTrainingData(obj.ClassId, features, ...
                    rawEmg(1:obj.SignalClassifier.NumSamplesPerWindow,:)')
                notify(obj,'DataCountChange'); % Broadcast notice of event
            end
            
        end
        function retrain(obj)
            % perform retraining
            if ~isempty(obj.TrainingData.getClassLabels) && ...
                    obj.TrainingData.SampleCount > 1
                % retrain
                obj.SignalClassifier.train();
                obj.SignalClassifier.computeError();
                obj.SignalClassifier.computeGains();
                obj.SignalClassifier.computeConfusion();
            end
        end
        function clearCurrentClassData(obj)
            clearClass = obj.ClassId;
            numDisabled = obj.TrainingData.disableLabeledData(clearClass);
            fprintf('[%s] %d samples disabled for class: %d\n',mfilename,numDisabled,clearClass);
            notify(obj,'DataCountChange'); % Broadcast notice of event  -- change to DataCountChange
        end
    end
    methods (Static = true)
        function hManager = Test
            % PatternRecognition.TrainingManager.Test
            % create a default training manager
            
            Source = Inputs.SignalSimulator();
            Source.initialize
            TrainingData = PatternRecognition.TrainingData('SimData.trainingData');
            SignalClassifier = SignalAnalysis.Lda();
            SignalClassifier.NumSamplesPerWindow = 250;
            SignalClassifier.initialize(TrainingData)
            
            hManager = PatternRecognition.TrainingManager(Source,SignalClassifier,TrainingData);
        end
    end
end