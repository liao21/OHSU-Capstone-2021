function s = test_tactor_serial
% Simple test of tactor control with a GUI.

DEBUG = true;

comPort = 'COM8';

lowVal = 0;
highVal = 180;

commandVals = zeros(1,5);


if DEBUG
    s = 1;
else
    s = instrfind('port',comPort);
    if isempty(s)
        s = serial(comPort,'Baudrate',57600,'Timeout',0.1,'Terminator','CR');
        fprintf('Opening port %s...',comPort)
        fopen(s);
        fprintf('Done\n');
    end
end

f = UiTools.create_figure('TactorControlTest');
uicontrol(f,...
    'Style','text',...
    'String','Press the number key ("1" "2" "3" "4" "5") for the corresponding tactor id',...
    'Position', [230 200 120 50])

set(f,'WindowKeyPressFcn',@(src,evt)keyDown(evt.Key));
set(f,'WindowKeyReleaseFcn',@(src,evt)keyUp(evt.Key));

    function keyDown(key)
        switch key
            case {'1' '2' '3' '4' '5'}
                id = str2double(key);
                newVals = zeros(1,5) + lowVal;
                newVals(id) = highVal;
                
                if ~isequal(commandVals,newVals)
                    commandVals = newVals;
                    fprintf(s,'[%d,%d,%d,%d,%d]',commandVals);
                    fprintf('Activating Tactor #%s\n',key);
                else
                    fprintf('Activated Tactor #%s\n',key);
                end
        end
    end

    function keyUp(key)
        switch key
            case {'1' '2' '3' '4' '5'}
                id = str2double(key);
                commandVals(id) = lowVal;
                
                fprintf(s,'[%d,%d,%d,%d,%d]',commandVals);
                fprintf('Deactvating Tactor #%s\n',key);
                pause(0.01)
        end
    end
end
