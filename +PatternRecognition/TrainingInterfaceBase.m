classdef TrainingInterfaceBase < Common.MiniVieObj
    % This class generates events related to starting and stopping training
    % that should be subscribed to by a TrainingManager.  
    events
        % Events triggered by Interface
        ClearClass      % clear data for the current class
        ClassChange     % change the current class number; contains new class data
        NextClass       % relative class change (+1)
        PreviousClass   % relative class change (-1)
        StartAdd        % start adding data 
        StopAdd         % stop adding data
        ForceRetrain    % force the classifier to retrain
    end
    properties
        Verbose = 0;    % control frinting to console
    end
    methods (Abstract)
        update(obj)     % update funciton will be called by Manager
    end
end
