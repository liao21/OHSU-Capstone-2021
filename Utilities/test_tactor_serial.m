function hTactor = test_tactor_serial
% Simple test of tactor control with a GUI.

lowVal = 0;
highVal = 200;

hTactor = BluetoothTactor('COM8');
% hTactor = BluetoothTactor('DEBUG');
hTactor.initialize()

f = UiTools.create_figure('TactorControlTest');
uicontrol(f,...
    'Style','text',...
    'String','Press the number key ("1" "2" "3" "4" "5") for the corresponding tactor id',...
    'Position', [230 200 120 50])

set(f,'WindowKeyPressFcn',@(src,evt)keyDown(evt.Key));
set(f,'WindowKeyReleaseFcn',@(src,evt)keyUp(evt.Key));
set(f,'CloseRequestFcn',@(src,evt) closeFig() );

    function keyDown(key)
        switch key
            case {'1' '2' '3' '4' '5'}
                id = str2double(key);
                hTactor.tactorVals(id) = highVal;
                end
        end

    function keyUp(key)
        switch key
            case {'1' '2' '3' '4' '5'}
                id = str2double(key);
                hTactor.tactorVals(id) = lowVal;
        end
    end
    function closeFig()
        hTactor.close()
        delete(f)
    end
end
