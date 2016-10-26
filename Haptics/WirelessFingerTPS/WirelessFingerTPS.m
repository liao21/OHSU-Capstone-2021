classdef WirelessFingerTPS < handle
    % Class object for Wireless FingerTPS sensor system.  Instantiate
    % object with:
    %   obj = WirelessFingerTPS.getInstance;
    %
    % Note that there is a hardware dependancy in:
    % fingertps_hw-05bc.txt
    % The first line contians the OS enumerated com port
    % 
    % HW connection and calibration information is located in the
    % @WirelessFingerTPS directory
    % fingertps_hw-05bc.txt contains the lines:
    %   HwD600ComPort	8
    %   HwD600BluetoothAddress	"00043e2605bc"
    % which are specific to the PC and Bluetooth Module
    %
    % $Log: WirelessFingerTPS.m  $
    % Revision 1.10 2011/01/25 14:47:50EST Armiger, Robert S. (ArmigRS1-a) 
    % updated port numbers
    % Revision 1.9 2010/08/05 16:16:53EDT armigrs1-a 
    % updated to send normalized output
    % Revision 1.8 2010/05/21 11:33:18EDT armigrs1-a 
    % removed unused setup method
    % Revision 1.7 2010/05/21 11:31:05EDT armigrs1-a 
    % added storage of lib warnings
    %
    properties
        numSensors
        WirelesstpsState
        id = mfilename;     % conform to Data Source format
        calibrationMinMax;
        libWarnings = '';        
    end
    properties (Constant = true)
        % CHANGE BY LMC: 'PPSDaq' to 'PPSDaq.dll'
        libName = 'PPSDaq'; %'PPSDaq';
        configfile = 'fingertps-05bc.cfg';
        
        % Index of each sensor value from TPS
        % Looking at the socket array on the TPS wrist unit
        % with the label up, the port numbers are:
        % (3)(2)(1)
        % (6)(5)(4)
        Thumb = 5;
        Index = 1;
        Middle = 2;
        Ring = 3;
        Little = 4;
        Palm = 6;

    end
    methods (Access = private)
        function obj = WirelessFingerTPS
        end
    end
    methods (Static)
        function singleObj = getInstance
            persistent localObj
            if isempty(localObj) || ~isvalid(localObj)
                localObj = WirelessFingerTPS;
                
                strWarnings = load_library();
                if ~isempty(strWarnings)
                    localObj.libWarnings = strWarnings;
                end                
                try
                    % Need to move to directory where TPS HW files are
                    % located for initialize
                    pathStr = fileparts(which(mfilename));
                    cwd = pwd;
                    cd(pathStr);
                    calllib(WirelessFingerTPS.libName,'ppsInitialize',WirelessFingerTPS.configfile);
                    cd(cwd)
                catch ME
                    localObj.WirelesstpsState = 0;
                    rethrow(ME);
                end
                
                localObj.WirelesstpsState = 1;
                
                calllib(WirelessFingerTPS.libName,'ppsStart')
                
                localObj.numSensors = calllib(WirelessFingerTPS.libName,'ppsGetRecordSize');
            end
            singleObj = localObj;
        end
    end
    methods
        function [normData sensorData ] = getdata(obj)
            persistent lastData
            if isempty(lastData)
                lastData = zeros(obj.numSensors,1);
            end
            
            nFrames = int32(1);
            timeStampPtr = libpointer('ulongPtr',zeros(nFrames,1));
            dataPtr = libpointer('singlePtr',zeros(obj.numSensors,1));
            calllib(obj.libName,'ppsGetData',nFrames,timeStampPtr,dataPtr);
            data = get(dataPtr,'Value');
            if isempty(data)
                sensorData = lastData;
            else
                sensorData = data;
                lastData = sensorData;
            end
            
            normData = sensorData;
            if isempty(obj.calibrationMinMax)
                return
            else
                sensorId = [...
                    WirelessFingerTPS.Index ...
                    WirelessFingerTPS.Middle ...
                    WirelessFingerTPS.Ring ...
                    WirelessFingerTPS.Little ...
                    WirelessFingerTPS.Thumb ...
                    ];
                
                for i = 1:length(sensorId)
                    iSensor = sensorId(i);
                    range = obj.calibrationMinMax(iSensor,2) - obj.calibrationMinMax(iSensor,1);
                    offset = obj.calibrationMinMax(iSensor,1);
                    normData(iSensor) = (sensorData(iSensor) - offset) ./ range;
                end
            end
            
        end
        function calibrate(obj)
            % This function will prompt the use to apply the max force per
            % fingertip and record the baseline value
            
            fingerName = {'Index' 'Middle' 'Ring' 'Little' 'Thumb'};
            sensorId = [...
                WirelessFingerTPS.Index ...
                WirelessFingerTPS.Middle ...
                WirelessFingerTPS.Ring ...
                WirelessFingerTPS.Little ...
                WirelessFingerTPS.Thumb ...
                ];
                
            nFingers = 5;
            for iFinger = 1:nFingers
                maxVal = 0;
                
                h = msgbox(...
                    sprintf('Begin Calibration of: %s \n Apply Max Force, then release and press OK when done',fingerName{iFinger}),...
                    'Calibration','help');
                
                while ishandle(h)
                    sensorData = getdata(obj);
                    currentVal = sensorData(sensorId(iFinger));
                    
                    fprintf('Current Value is: %d \n',currentVal);
                    
                    % get max recorded value
                    if currentVal > maxVal
                        maxVal = currentVal;
                    end
                    pause(0.05);
                end
                
                fprintf('Max Value was: %d \n',maxVal);
                fprintf('Baseline Value was: %d \n',currentVal);
                
                obj.calibrationMinMax(sensorId,1) = currentVal;
                obj.calibrationMinMax(sensorId,2) = maxVal;
            end
            
        end
        
        function preview(obj)
            tmr = timer;
            set(tmr,'Period',0.05);
            set(tmr,'TimerFcn',@plot_data);
            set(tmr,'ExecutionMode','fixedRate');
            
            
            tmpSample = getdata(obj);
            
            nChannels = length(tmpSample);
            nSamples = 100;
            
            data = zeros(nSamples,nChannels);
            
            figure(1);
            clf;
            hLines = plot(data);
            
            hText = zeros(size(hLines));
            
            for i = 1:nChannels
                hText(i) = text(1.05*nSamples,0,num2str(i));
                set(hText(i),'Color',get(hLines(i),'Color'));
            end
            
            start(tmr);
            return;
            
            function plot_data(src,evt) %#ok<INUSD>
                offset = linspace(0,10,nChannels);

                try
                    
                    newSample = getdata(obj);
                    % shift buffer left
                    data = circshift(data,[-1 0]);
                    data(nSamples,:) = newSample(:);
                    for iJnt = 1:nChannels
                        set(hLines(iJnt),'XData',1:nSamples);
                        pltData = data(:,iJnt) + offset(iJnt);
                        set(hLines(iJnt),'YData',pltData);
                        pos = get(hText(iJnt),'Position');
                        set(hText(iJnt),'Position',[pos(1) mean(pltData) pos(3)]);
                    end
                    drawnow
                catch ME
                    stop(src);
                    delete(src);
                end
                
            end %% plot_data
        end %% preview
        
        function mask = getmask(obj)
            nData = obj.numSensors;
            mask = zeros(1,nData);
            
            validIds = 1:nData;
            mask(validIds) = 1;
        end
        
        function close(obj)
            calllib(obj.libName,'ppsStop');
            obj.WirelesstpsState = 0;
%             unloadlibrary('PPSDaq');
        end
    end
end

function strWarnings = load_library()
strWarnings = [];
if ~libisloaded(WirelessFingerTPS.libName)
    [notfound,strWarnings] = loadlibrary('PPSDaq.dll','PPSDaq.h');
    if isempty(notfound)
        fprintf('Library %s loaded sucessfully\n',WirelessFingerTPS.libName);
    end
    if~isempty(warning)
        fprintf('Warnings produced while parsing header file %s \n',WirelessFingerTPS.libName);
        disp(strWarnings);
    end
end
end