classdef ParsePythonMyoLog
    % Parse the myo.py log files
    %
    % File contains IMU information, raw EMG, battery, and streaming rates
    %
    %
    % 1512398123.118280 Found device: hci0
    % 1512398123.119619 Starting connection to hci0
    % 1512398123.120556 Connecting to: C3:0A:EA:14:14:D9
    % 1512398133.477244 MAC: C3:0A:EA:14:14:D9 is handle 1025
    % 1512398133.478544 Setting Update Rate: hcitool -i hci0 cmd 0x08 0x0013 01 04 06 00 06 00 00 00 90 01 01 00 07 00
    % 1512398134.644036 IMU: 93186a2a1d27c10cb10dc1f644101518b428cc08
    % 1512398134.645898 E1: d88058ebcd7f7facd680240912488e80
    % 1512398134.651175 E2: e47f80f1fd548080066e80fbffbdd680
    % 1512398134.658422 IMU: de182d2896298e0b70feed04a5f32c00110232ec
    % 1512398134.659516 E3: fd64b905f5c67f4aee13fbfc057fe131
    % 1512398134.665802 E0: ddda2afc3243f8f2db801d0627d7ffcc
    % 1512398134.681167 IMU: 151f61205b2de204a10916041df40df573e162c0
    % 1512398134.682435 E1: f6b300e9fca9a0bf073be5f30c989044
    % 1512398134.688912 E2: 29e3d4fafe9a807f1980be07fde07f80
    % 1512398134.703430 IMU: ad25c113cf2f70ffe00d5c0edbfac0e09ae126b3
    % 1512398134.704479 E3: 0f80fd1109807f7f217f2f1123807ff4
    % 1512398134.710934 E0: 137f48ff2fa57f80ff7f44fd037f43a7
    % 1512398134.718905 IMU: 042bd403232f09fd780b48091bfb84ca78e14bb4
    % 1512398134.720233 E1: f97f3600c87f8068f9c7330ebc75807f
    % 1512398134.726773 E2: 09801c20de1f2a7f087fb80a01807f7f
    % 1512398134.740953 IMU: bd2bc4f2c92c6101260cc1fe1ffb01aba3f0d9c8
    % 1512398134.742413 E3: 047fb5e4f6804e72127fe3dfbd807f33
    % 1512398134.749640 E0: e97ff8d5d17f7ff3f252f7ec14047fbe
    % 1512398134.763435 IMU: f926aee3c5297a0599ff6ee9b9029ead590414d0
    % 1512398134.765029 E1: ef8d28ccdef0bde405801bf5f18080ef
    % 1512398134.771269 E2: 0e80e5fa0480800d0a80bb0d0af31df0
    % 1512398134.779073 IMU: cc2026db3628ba0642fe6ce7410e9ecd7f12d0e3
    % 1512398134.780298 E3: eca9cd0d3b7f7fb506f4ef10207fd6a9
    % 1512398134.787107 E0: eaf2fef2109780b2fef6ee00216a95b9
    
    properties
        filePath = ''
        fileName = ''
        numLines = 0
        textLines
        isRead  % Binary label of lines read and processed
        unreadLines
        
        handleMsg
        emgMsg % Nominally at 200Hz;  2 samples streamed every 0.005 sec
        imuMsg % Nominally 50Hz; Accel, Angular Rate, Quaternion
        rateMsg
        batteryMsg % Battery
        
    end
    methods
        function obj = ParsePythonMyoLog(fullFilename)
            % Get filename and parse file
            % parse the raw myo emg log file
            
            if nargin < 1
                % Raise file selection dialog if no files provided
                
                % [obj.fileName, obj.filePath] = uigetfile('*.log','Select one or more log files','Multiselect','off');
                
                obj.filePath = '';
                s = dir('EMG*.log');
                obj.fileName = s(end).name;
            else
                [p,f,e] = fileparts(fullFilename);
                obj.filePath = p;
                obj.fileName = [f e];
            end
            
            %%%%%%%%%%%%%%%%%
            % read the file
            %%%%%%%%%%%%%%%%%
            filetext = fileread(fullfile(obj.filePath,obj.fileName));
            
            % Break file into obj.textLines
            obj.textLines = strsplit(filetext, '\n');
            obj.numLines = length(obj.textLines);
            obj.isRead = false(obj.numLines,1);
            fprintf('\nRead file: "%s" \t Found %d Lines\n',obj.fileName,obj.numLines);
            
            % Use for date conversion: Convert unix time (epoc 1970) to matlab time
            zone = -5*60*60;
            convertTime = @(posixtime)datetime(posixtime+zone,'ConvertFrom','posixtime');
            
            % Parse Line types
            % 1491529009.595366 MAC: F0:1C:CD:A7:2C:85 is handle 1025
            isHandleMsg = contains(obj.textLines,'handle');
            obj.isRead(isHandleMsg) = true;
            % Store handle Message
            if any(isHandleMsg)
                handleLines = obj.textLines(isHandleMsg)';
                obj.handleMsg.time = convertTime(str2double(extractBefore(handleLines,' MAC: ')));
                obj.handleMsg.value = handleLines;
            end
            
            % 1491553915.856260 Battery Level: 81
            isBatteryMsg = contains(obj.textLines, 'Battery Level');
            obj.isRead(isBatteryMsg) = true;
            if any(isBatteryMsg)
                batteryLines = obj.textLines(isBatteryMsg)';
                obj.batteryMsg.time = convertTime(str2double(extractBefore(batteryLines,' Battery Level: ')));
                obj.batteryMsg.value = str2double(extractAfter(batteryLines,' Battery Level: '));
            end
            
            % Parse Status Lines
            % 1491554022.125678 MAC: C3:0A:EA:14:14:D9 Port: 15002 EMG: 198.8 Hz IMU: 50.0 Hz BattEvts: 1
            isRateMsg = contains(obj.textLines,'MAC') & ~isHandleMsg;
            obj.isRead(isRateMsg) = true;
            if any(isRateMsg)
                rateLines = obj.textLines(isRateMsg)';
                obj.rateMsg.time = convertTime(str2double(extractBefore(rateLines,' MAC: ')));
                obj.rateMsg.rateEMG = str2double(extractBetween(obj.textLines(isRateMsg),' EMG: ', ' Hz'));
                obj.rateMsg.rateIMU = str2double(extractBetween(obj.textLines(isRateMsg),' IMU: ', ' Hz'));
            end
            
            % Parse IMU Lines
            % 1491554022.143426 IMU: ae04230910e4a838ec0190fa0f05d9ff55ffc600
            isImuMsg = contains(obj.textLines,'IMU') & ~isRateMsg;
            obj.isRead(isImuMsg) = true;
            if any(isImuMsg)
                imuLines = obj.textLines(isImuMsg)';
                
                timeIMU = extractBefore(imuLines,' IMU: ');
                dataIMU = extractAfter(imuLines,' IMU: ');
                
                isValid = strlength(dataIMU) == 40;
                fprintf('Omitting %d bad IMU lines\n',sum(~isValid))
                dataIMU = dataIMU(isValid);
                timeIMU  = timeIMU(isValid);
                
                
                imuVals = double(typecast(uint8(hex2dec(reshape([dataIMU{:}],2,[])')),'int16'));
                imu = reshape(imuVals, 10, [])';
                
                % Scaling constants for MYO IMU Data
                MYOHW_ORIENTATION_SCALE = 16384.0;
                MYOHW_ACCELEROMETER_SCALE = 2048.0;
                MYOHW_GYROSCOPE_SCALE = 16.0;
                
                imu = double(imu);
                obj.imuMsg.time = convertTime(str2double(timeIMU));
                obj.imuMsg.orientation = imu(:,1:4) ./ MYOHW_ORIENTATION_SCALE;
                obj.imuMsg.accelerometer = imu(:,5:7) ./ MYOHW_ACCELEROMETER_SCALE;
                obj.imuMsg.gyroscope = imu(:,8:10) ./ MYOHW_GYROSCOPE_SCALE;
                
                % get orientation as [3x3] rotation matrix.  Convert native
                % quaterion to matrix, but then do post processing to ensure it
                % is orthogonal.
                %
                % If a second myo is attached then the second output argument
                % can be used to query the [3x3] rotation matirx of that device
                
                R = LinAlg.quaternionToRMatrix(obj.imuMsg.orientation');
                for i = 1:size(R,3)
                    [U, ~, V] = svd(R(:,:,i));
                    R(:,:,i) = U*V'; % Square up the rotaiton matrix
                end
                
                obj.imuMsg.Rxyz = LinAlg.decompose_R(R)';
                
            end
            
            % Parse EMG
            %
            % 1491553915.854171 E0: 06092df2e0fb0e09f9f9991f0f11f48e
            % 1491553915.862235 E1: fdeb4aebfdcce30df100f6edd6083504
            % 1491553915.868435 E2: 0e15d93a1efceae900f82ef218fd18fd
            % 1491553915.883724 E3: f1f2d8d3d5135d1bfa0ea02505121ff4
            isEmgMsg0 = contains(obj.textLines,' E0: ');
            isEmgMsg1 = contains(obj.textLines,' E1: ');
            isEmgMsg2 = contains(obj.textLines,' E2: ');
            isEmgMsg3 = contains(obj.textLines,' E3: ');
            
            obj.isRead(isEmgMsg0) = true;
            obj.isRead(isEmgMsg1) = true;
            obj.isRead(isEmgMsg2) = true;
            obj.isRead(isEmgMsg3) = true;
            
            if any(isEmgMsg0 | isEmgMsg1 | isEmgMsg2 | isEmgMsg3)
                
                time0 = extractBefore(obj.textLines(isEmgMsg0),' E0: ');
                emg0 = extractAfter(obj.textLines(isEmgMsg0),' E0: ');
                time1 = extractBefore(obj.textLines(isEmgMsg1),' E1: ');
                emg1 = extractAfter(obj.textLines(isEmgMsg1),' E1: ');
                time2 = extractBefore(obj.textLines(isEmgMsg2),' E2: ');
                emg2 = extractAfter(obj.textLines(isEmgMsg2),' E2: ');
                time3 = extractBefore(obj.textLines(isEmgMsg3),' E3: ');
                emg3 = extractAfter(obj.textLines(isEmgMsg3),' E3: ');
                
                tString = cat(2,time0,time1,time2,time3);
                emgString = cat(2,emg0, emg1, emg2, emg3);
                
                % sort by date
                tNum = str2double(tString);
                [tSorted, idxSorted] = sort(tNum);
                emgString = emgString(idxSorted);
                
                % check all the
                isValid = strlength(emgString) == 32;
                fprintf('Omitting %d bad EMG obj.textLines (of %d)\n',sum(~isValid),length(isValid))
                
                emgString = emgString(isValid);
                tSorted  = tSorted(isValid);
                
                % note each converted data line has 2 samples
                dataEMG = reshape(typecast(uint8(hex2dec(reshape([emgString{:}],2,[])')),'int8'),16,[])';
                dataEMG = reshape(dataEMG',8,[])';
                % double the time vector to reflect two samples per message
                tDoubled = [tSorted(:) tSorted(:) + 0.005]';
                tDoubled = tDoubled(:);
                
                obj.emgMsg.time = convertTime(tDoubled);
                obj.emgMsg.value = dataEMG;
                
                % resort interleaved samples
                %             [tSorted, idxSorted] = sort(timeEMG);
                %             timeEMG = tSorted;
                %             dataEMG = dataEMG(idxSorted,:);
                
            end
            
            % Store Remaining Lines
            obj.unreadLines = obj.textLines(~obj.isRead)';
            
        end
        function plot(obj)
            close all
            figure
            obj.plot_myo_data(obj.emgMsg.time, obj.emgMsg.value, 'RAW EMG')
            figure
            obj.plot_myo_data(obj.imuMsg.time, obj.imuMsg.Rxyz, 'Rxyz')
            figure
            obj.plot_myo_data(obj.batteryMsg.time, obj.batteryMsg.value, 'Myo Batt %')
            figure
            obj.plot_myo_data(obj.rateMsg.time, [obj.rateMsg.rateEMG; obj.rateMsg.rateIMU]', 'Stream Rate')
        end
    end
    methods (Static = true)
        function plot_myo_data(time, data, strTitle)
            % Helper function that breaks data time history into subplots
            % find breaks:
            break_duration = 0.01;
            
            breaks = [0; find(diff(time) > break_duration); length(time)];
            
            cellTime = {};
            for i = 1:length(breaks)-1
                cellTime{i} = time(breaks(i)+1:breaks(i+1));
                cellEmg{i} = data(breaks(i)+1:breaks(i+1),:);
            end
            
            for i = 1:length(cellTime)
                subplot(length(cellTime),1,i)
                plot(cellTime{i},cellEmg{i})
                datetick('x','mmm/dd HH:MMPM','keepticks')
                %set(gca,'XTick',linspace(d2(1),d2(end),20))
                xtickangle(25)
                %ylim([18 26])
                if i == 1
                    title(strTitle)
                end
            end
        end
    end
end
