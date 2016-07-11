classdef ChangeClassEventData < event.EventData
    % Class for holding new class name and id as event data.
    % Usage:
    % evtdata = PatternRecognition.ChangeClassEventData(newState);
    % notify(obj,'ClassChange',evtdata);
    %
    % Revisions:
    % 2016JUL02 Armiger: Created
    properties
        NewClassName
        NewClassId
    end
    
    methods
        function data = ChangeClassEventData(newClassId,newClassName)
            data.NewClassId = newClassId;
            data.NewClassName = newClassName;
        end
    end
end