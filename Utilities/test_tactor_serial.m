function s = test_tactor_serial
% Simple test of tactor control with a GUI.


commandVals = zeros(1,5);

s = instrfind('port','COM15');
if isempty(s)
    s = serial('com15','Baudrate',57600,'Timeout',0.1);
    fprintf('Opening port %s...','com15')
    fopen(s);
    fprintf('Done\n');
end

f = UiTools.create_figure('TactorControlTest');
uicontrol(f,...
    'Style','text',...
    'String','Press the number key for the corresponding tactor id',...
    'Position', [230 200 120 50])

set(f,'WindowKeyPressFcn',@(src,evt)keyDown(evt.Key));
set(f,'WindowKeyReleaseFcn',@(src,evt)keyUp(evt.Key));


    function keyDown(key)
        switch key
            case {'1' '2' '3' '4' '5'}
                id = str2double(key);
                newVals = zeros(1,5);
                newVals(id) = 180;
                
                if ~isequal(commandVals,newVals)
                    %fwrite(s,sprintf('[%d,%d,%d,%d,%d]',vals))
                    fprintf('Activating Tactor #%s\n',key);
                    commandVals = newVals;
                else
                    fprintf('Activated Tactor #%s\n',key);
                end
        end
    end

    function keyUp(key)
        switch key
            case {'1' '2' '3' '4' '5'}
                id = str2double(key);
                commandVals(id) = 0;
                
                fwrite(s,sprintf('[%d,%d,%d,%d,%d]',vals))
                fprintf('Deactvating Tactor #%s\n',key);
                pause(0.01)
        end
    end
end
