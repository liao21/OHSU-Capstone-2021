classdef ParsePythonData
    %PARSEPYTHONDATA Summary of this class goes here
    %   Detailed explanation goes here
    %
    %
    %
    % OpenNFU Based parsing
    %
    %
    % Multiple logs are created usingthe python version of the MiniVIE
    %
    % TAC assessments:  These can be loaded and parsed directly in a batch
    %   process using the following:
    %   s = DataAnalysis.PostProcessing.processTacBatch('c:\path_to_files','MPL19')
    %   As a result, all TAC1_LOG.hdf5 files will be read and processed and
    %   written to a pptx file for results viewing
    % 
    
    properties
    end
    
    methods (Static = true)
        function data = getTACLog(file)
            
            % Initialize data storage struct
            data = struct(...
                'completion_time', {}, ...
                'move_complete', {}, ...
                'intent_time_history', {}, ...
                'position_time_history', {}, ...
                'target_error', {}, ...
                'target_joint', {}, ...
                'target_position', {},...
                'time_history', {}...
                );
            
            % Get file info
            info = h5info(file);
            trialNames = {info.Groups.Groups(:).Name};
            
            % Loop through trials and pull data
            for iTrial = 1:length(trialNames)
                data(iTrial) = struct(...
                    'completion_time', {NaN}, ...
                    'move_complete', {0}, ...
                    'intent_time_history', {DataAnalysis.ParsePythonData.removeNullCharacters(h5read(file, [trialNames{iTrial}, '/intent_time_history']))}, ...
                    'position_time_history', {h5read(file, [trialNames{iTrial}, '/position_time_history'])}, ...
                    'target_error', {h5read(file, [trialNames{iTrial}, '/target_error'])}, ...
                    'target_joint', {DataAnalysis.ParsePythonData.removeNullCharacters(h5read(file, [trialNames{iTrial}, '/target_joint']))}, ...
                    'target_position', {h5read(file, [trialNames{iTrial}, '/target_position'])},...
                    'time_history', {h5read(file, [trialNames{iTrial}, '/time_history'])}...
                    );
                % Completion time not always available
                try
                    data(iTrial).completion_time = h5read(file, [trialNames{iTrial}, '/completion_time']);
                    if data(iTrial).completion_time > 0
                        data(iTrial).move_complete = 1; % Will only get set if completion_time is non-negative (is set to -1 in python by default)
                    end
                catch
                    continue
                end
            end
        end
        
        function data = getMotionTesterLog(file)
            
            % Get file info
            info = h5info(file);
            
            % Get first level data
            allClassNames = DataAnalysis.ParsePythonData.removeNullCharacters(h5read(file, '/TrialLog/AllClassNames'));
            classIdToTest = h5read(file, '/TrialLog/ClassIdToTest');
            try
                % Newer versions have these datasets
                maxCorrect = h5read(file, '/TrialLog/MaxCorrect');
                timeout = h5read(file, '/TrialLog/Timeout');
            catch
                maxCorrect = NaN;
                timeout = NaN;
            end
            
            % Initialize data storage struct
            trial_data = struct(...
                'classDecision', {},...
                'targetClass', {} ...
                );
            
            data = struct(...
                'AllClassNames', {allClassNames'},...
                'ClassIdToTest', {classIdToTest'+1}, ...  % Convert from Python indexing
                'MaxCorrect', {maxCorrect},...
                'Timeout', {timeout},...
                'Data', trial_data ...
                );
            
            trialNames = {info.Groups.Groups.Groups(:).Name};
            
            % Loop through trials and pull data
            for iTrial = 1:length(trialNames)
                classDecision = h5read(file, [trialNames{iTrial}, '/classDecision']);
                classDecision = double(classDecision) + 1;
                targetClass = DataAnalysis.ParsePythonData.removeNullCharacters(h5read(file, [trialNames{iTrial}, '/targetClass']));
                targetClass = targetClass{1};
                data.Data(iTrial) = struct(...
                    'classDecision', {classDecision},...
                    'targetClass', {targetClass} ...
                    );
                
                % Fix class id to test
                % TODO: Figure out why not exported correctly from Python
                data.ClassIdToTest(iTrial) = strfndw(allClassNames, targetClass);
                
            end
        end
        
        function data = getCPCHBytes(file)
            
            % Initialize data storage struct
            data = struct(...
                          'raw_bytes', {}, ...
                          'timestamp', {} ...
                          );
                      
            % Get file info
            info = h5info(file);
            byteReads = {info.Groups(:).Name};  % This is simply each time bytes were read down from serial buffer
            
            % Loop through trials and pull data       
            for iRead = 1:length(byteReads)
                b = h5read(file, [byteReads{iRead}, '/rawbytes']);
                t = h5read(file, [logs{iLog}, '/timestamp']);
                t = [t{:}];
                data(iRead) = struct(...
                              'raw_bytes', {b}, ...
                              'timestamp', {t} ...
                              );
            end
        end
        
        function data = getDCellLog(file)
            
            % Initialize data storage struct
            data = struct(...
                          'strain', {}, ...
                          'timestamp', {} ...
                          );
                      
            % Get file info
            info = h5info(file);
            logs = {info.Groups(:).Name};  % This is simply each time bytes were read down from serial buffer
            
            % Loop through trials and pull data       
            for iLog = 1:length(logs)
                s = h5read(file, [logs{iLog}, '/strain']);
                t = h5read(file, [logs{iLog}, '/timestamp']);
                t = [t{:}];
                data(iLog) = struct(...
                              'strain', {s}, ...
                              'timestamp', {t} ...
                              );
            end
        end
        
        function [batt_vals, time_stamp] = get_hci_log(file)
            % DataAnalysis.ParsePythonData.get_hci_log('hci0_myo.log')
            if nargin < 1
                p = '';
                f = 'hci0_myo.log';
                %f = 'MPL_WWW_1999-12-31_19-00-25.log';
                file = fullfile(p,f);
            end
            
            %% Read file
            filetext = fileread(file);
            
            % Break file into lines
            lines = strsplit(filetext, '\n');
            fprintf('Found %d lines\n',length(lines))
            
            % Find Battery lines
            battId = ~cellfun(@(x)isempty(strfind(x,'Battery Level')),lines);
            battLines = lines(battId);
            fprintf('Found %d Battery Level lines\n',sum(battId))
            
            batt_vals = str2double(cellfun(@(x)regexp(x,'(?<=Battery Level: )[0-9]+','match'),battLines));
            
            % extract date string
            C = cellfun(@(x)regexp(x,'(?<=\]:).*(?=Battery Level)','match'),battLines);
            % convert to date number
            time_stamp = datenum(C,'yyyy-mm-dd HH:MM:SS,FFF');
            
            %% Plot all
            clf
            plot(time_stamp,batt_vals,'-')
            datetick('x','mmm/dd HH:MMPM','keepticks')
            %set(gca,'XTick',linspace(d2(1),d2(end),20))
            xtickangle(25)
            %ylim([18 26])
            ylabel('Volts')
            %% Plot by day
            clf
            days = unique(round(time_stamp));
            for i = 1:length(days)
                subplot(length(days),1,i)
                id = round(time_stamp - (-0.4)) == days(i);
                plot(time_stamp(id),batt_vals(id),'-')
                datetick('x','mmm/dd HH:MMPM','keepticks')
                %set(gca,'XTick',linspace(d2(1),d2(end),20))
                xtickangle(25)
                %ylim([18 26])
                ylabel('Battery %')
            end
            
            
        end
        
        function get_minivie_log(file)
            % DataAnalysis.ParsePythonData.get_minivie_log('hci0_myo.log')
            if nargin < 1
                p = '';
                f = 'hci0_myo.log';
                %f = 'MPL_WWW_1999-12-31_19-00-25.log';
                file = fullfile(p,f);
            else
                p = file
            end
            
            %%
            %p = 'C:\tmp\';
            s = rdir(fullfile(p,'*.log'));
            % Sort by date
            [~, id] = sort([s(:).datenum]);
            s = s(id);
            
            % Read full file and line splits as single string
            filetext = [];
            for i = 1:length(s)
                f = s(i).name;
                fprintf('%s\n',f)
                filetext = cat(2,filetext,fileread(f));
            end
            
            % Break file into lines
            lines = strsplit(filetext, '\n');
            fprintf('Found %d lines\n',length(lines))
            
            %
            
            % Find Battery lines
            %battId = ~cellfun(@(x)isempty(strfind(x,'Battery Level')),lines);
            
            %%
            
            % Joint Angle lines
            % can't do this since no guarantee log messages are in order
            %angleId = ~cellfun(@(x)isempty(strfind(x,'Joint Command:')),lines);
            % shift from Joint Command: line to data line: [ ]
            %angleId = circshift(angleId,1);
            %dLines = lines(angleId)';
            
            
            angleId = (cellfun(@length,lines) > 200) & (cellfun(@(x)sum(x == ','),lines) >= 27);
            dLines = lines(angleId)';
            
            
            %% Slow
            jointAngles = zeros(length(dLines),27);
            for i = 1:length(dLines)
                C = regexp(dLines{i},'(?<=INFO).*(?=\])','match');
                jointAngles(i,:) = str2num(strrep(C{1}(6:end),'''',''));
                if ~mod(i,1000000)
                    fprintf('%f %%',i/length(dLines))
                end
            end
            
            
            %% Plot all Joint Angles
            plot(jointAngles(:,1:7)*180/pi)
            legend('SHFE','SHAA', 'HR', 'EL', 'WROT', 'WDEV', 'WFE')
            ylabel('Joint Angle, deg')
            
            figure
            plot(jointAngles(:,8:27)*180/pi)
            m = properties(MPL.EnumArm);
            legend(m(8:end),'Interpreter','None')
            ylabel('Joint Angle, deg')
            
            %% Plot Joint Angles by day
            clf
            days = unique(round(time_stamp));
            for i = 1:length(days)
                subplot(length(days),1,i)
                id = round(time_stamp - (-0.4)) == days(i);
                plot(time_stamp(id),bus_voltage(id),'-')
                datetick('x','mmm/dd HH:MMPM','keepticks')
                %set(gca,'XTick',linspace(d2(1),d2(end),20))
                xtickangle(25)
                %ylim([18 26])
                ylabel('Volts')
            end
            
            
            
            %% Replay in unity
            a = MPL.MplUnitySink
            a.initialize()
            
            StartStopForm([])
            i = 0;
            while StartStopForm
                drawnow
                i = i + 1;
                a.putData(jointAngles(i,:))
            end
            
            
            
            
            
            
            %%
            C = cellfun(@(x)regexp(x,'(?<=bus_voltage'':\s).*(?=,\s''lc_)','match'),bLines);
            bus_voltage = str2double(C)
            
            
            %%
            
            %%%%%%%%%%%%%%%%%%
            % Parse Hearbeat lines
            %%%%%%%%%%%%%%%%%%
            
            % Find NFU Heartbeat
            battId = ~cellfun(@(x)isempty(strfind(x,'bus_voltage')),lines);
            bLines = lines(battId)';
            
            % extract date string
            C = cellfun(@(x)regexp(x,'.*(?= [NfuUdp)','match'),bLines);
            % convert to date number
            time_stamp = datenum(C,'yyyy-mm-dd HH:MM:SS,FFF');
            
            % search between "bus_voltage': " and " 'lc"
            C = cellfun(@(x)regexp(x,'(?<=bus_voltage'':\s).*(?=,\s''lc_)','match'),bLines);
            bus_voltage = str2double(C);
            
            % lc_software_state': '        ', 'nfu_ms_per_CMDDOM
            C = cellfun(@(x)regexp(x,'(?<=lc_software_state'':\s'').*(?='',\s''nfu_ms_per_CMDDOM)','match'),bLines);
            lc_software_state = unique(C);
            
            C = cellfun(@(x)regexp(x,'(?<=nfu_ms_per_CMDDOM'':\s).*(?=,\s''nfu_state)','match'),bLines);
            nfu_ms_per_CMDDOM = str2double(C);
            
            C = cellfun(@(x)regexp(x,'(?<=nfu_state'':\s'').*(?='',\s''nfu_ms_per_ACTUATEMPL)','match'),bLines);
            nfu_state = unique(C);
            
            C = cellfun(@(x)regexp(x,'(?<=nfu_ms_per_ACTUATEMPL'':\s).*(?=,\s''lmc_software_state)','match'),bLines);
            nfu_ms_per_ACTUATEMPL = str2double(C);
            
            %% Plot command rate by day
            clf
            days = unique(round(time_stamp));
            for i = 1:length(days)
                subplot(length(days),1,i)
                hold on
                id = round(time_stamp - (-0.4)) == days(i);
                plot(time_stamp(id),nfu_ms_per_CMDDOM(id),'-')
                plot(time_stamp(id),nfu_ms_per_ACTUATEMPL(id),'-')
                datetick('x','mmm/dd HH:MMPM','keepticks')
                %set(gca,'XTick',linspace(d2(1),d2(end),20))
                xtickangle(25)
                %ylim([18 26])
                h = legend('nfu_ms_per_CMDDOM','nfu_ms_per_ACTUATEMPL');
                set(h,'Interpreter','None')
            end
            
            %% Plot by day
            clf
            days = unique(round(time_stamp));
            for i = 1:length(days)
                subplot(length(days),1,i)
                id = round(time_stamp - (-0.4)) == days(i);
                plot(time_stamp(id),bus_voltage(id),'-')
                datetick('x','mmm/dd HH:MMPM','keepticks')
                %set(gca,'XTick',linspace(d2(1),d2(end),20))
                xtickangle(25)
                %ylim([18 26])
                ylabel('Volts')
            end
            
            
            
            
            %% Get Battery Info:
            
            
            
            
            
            
        end
        
        function newArray = removeNullCharacters(cellArray)
            % Function to remove null character
            
            % Handle strings
            if ischar(cellArray)
                cellArray = {cellArray};
            end
            
            % TODO: add logic to keep number strings
            func = @(x) x(x~=char(0));
            
            newArray = cellfun(func, cellArray, 'UniformOutput', 0);
            
        end
        
        function data = get_myo_emg_raw(file)
            % DataAnalysis.ParsePythonData.get_myo_emg_raw
            % parse the raw myo emg log file
            %%
            if nargin < 1
                %%
                file = 'EMG_MAC_F01CCDA72C85_PORT_15001.log';
                file = 'EMG_MAC_C30AEA1414D9_PORT_15002.log';
            end
            
            %%
            % read entire file as a character array
            filetext = fileread(file);
            
            % Cast file into string and split lines (one line per cell)
            lines = splitlines(filetext);
            fprintf('Found %d lines in %s\n',length(lines),file)
            
            %% Parse Line types
            % 1491529009.595366 MAC: F0:1C:CD:A7:2C:85 is handle 1025
            idxHandle = contains(lines,'handle');
            lines(idxHandle)
            
            % 1491554022.125678 MAC: C3:0A:EA:14:14:D9 Port: 15002 EMG: 198.8 Hz IMU: 50.0 Hz BattEvts: 1
            idxStatus = contains(lines,'MAC') & ~idxHandle;
            
            % 1491554022.143426 IMU: ae04230910e4a838ec0190fa0f05d9ff55ffc600
            idxIMU = contains(lines,'IMU') & ~idxStatus;
            
            % 1491553915.856260 Battery Level: 81
            idxBatt = contains(lines, 'Battery Level');
            
            % 1491553915.854171 E0: 06092df2e0fb0e09f9f9991f0f11f48e
            % 1491553915.862235 E1: fdeb4aebfdcce30df100f6edd6083504
            % 1491553915.868435 E2: 0e15d93a1efceae900f82ef218fd18fd
            % 1491553915.883724 E3: f1f2d8d3d5135d1bfa0ea02505121ff4
            idxEMG0 = contains(lines,'E0:');
            idxEMG1 = contains(lines,'E1:');
            idxEMG2 = contains(lines,'E2:');
            idxEMG3 = contains(lines,'E3:');
            
            %% Parse Battery Level
            
            % Find Battery lines
            fprintf('Found %d Battery Level lines\n',sum(idxBatt))
            
            % extract date string
            timeBatt = extractBefore(lines(idxBatt),' Battery Level: ');
            dataBatt = extractAfter(lines(idxBatt),' Battery Level: ');
            
            % convert time
            timeBatt = DataAnalysis.ParsePythonData.unix_time_to_matlab(str2double(timeBatt));
            dataBatt = str2double(dataBatt);
            
            %% Parse EMG Blocks
            
            time0 = extractBefore(lines(idxEMG0),' E0: ');
            emg0 = extractAfter(lines(idxEMG0),' E0: ');
            time1 = extractBefore(lines(idxEMG1),' E1: ');
            emg1 = extractAfter(lines(idxEMG1),' E1: ');
            time2 = extractBefore(lines(idxEMG2),' E2: ');
            emg2 = extractAfter(lines(idxEMG2),' E2: ');
            time3 = extractBefore(lines(idxEMG3),' E3: ');
            emg3 = extractAfter(lines(idxEMG3),' E3: ');
            
            tString = cat(1,time0,time1,time2,time3);
            emgString = cat(1,emg0, emg1, emg2, emg3);
            
            % sort by date
            tNum = str2double(tString);
            [tSorted, idxSorted] = sort(tNum);
            emgString = emgString(idxSorted);
            
            % check all the 
            isValid = strlength(emgString) == 32;            
            fprintf('Omitting %d bad EMG lines (of %d)\n',sum(~isValid),length(isValid))
            
            emgString = emgString(isValid);
            tSorted  = tSorted(isValid);
            
            % note each converted data line has 2 samples
            dataEMG = reshape(typecast(uint8(hex2dec(reshape([emgString{:}],2,[])')),'int8'),16,[])';
            dataEMG = reshape(dataEMG',8,[])';
            % double the time vector to reflect two samples per message
            tDoubled = [tSorted(:) tSorted(:) + 0.005]';
            tDoubled = tDoubled(:);

            timeEMG = DataAnalysis.ParsePythonData.unix_time_to_matlab(tDoubled);
            
            % resort interleaved samples
%             [tSorted, idxSorted] = sort(timeEMG);
%             timeEMG = tSorted;
%             dataEMG = dataEMG(idxSorted,:);

            
            %% Parse IMU Blocks
            
            timeIMU = extractBefore(lines(idxIMU),' IMU: ');
            dataIMU = extractAfter(lines(idxIMU),' IMU: ');
            
            isValid = strlength(dataIMU) == 40;            
            fprintf('Omitting %d bad IMU lines\n',sum(~isValid))
            dataIMU = dataIMU(isValid);
            timeIMU  = timeIMU(isValid);

            timeIMU = DataAnalysis.ParsePythonData.unix_time_to_matlab(str2double(timeIMU));
            
            imu = reshape(typecast(uint8(hex2dec(reshape([dataIMU{:}],2,[])')),'int16'),10,[])';
            
            % Scaling constants for MYO IMU Data
            MYOHW_ORIENTATION_SCALE = 16384.0;
            MYOHW_ACCELEROMETER_SCALE = 2048.0;
            MYOHW_GYROSCOPE_SCALE = 16.0;
            
            imu = double(imu);
            orientation = imu(:,1:4) ./ MYOHW_ORIENTATION_SCALE;
            accelerometer = imu(:,5:7) ./ MYOHW_ACCELEROMETER_SCALE;
            gyroscope = imu(:,8:10) ./ MYOHW_GYROSCOPE_SCALE;
            
            % get orientation as [3x3] rotation matrix.  Convert native
            % quaterion to matrix, but then do post processing to ensure it
            % is orthogonal.
            % 
            % If a second myo is attached then the second output argument
            % can be used to query the [3x3] rotation matirx of that device
            
            R = LinAlg.quaternionToRMatrix(orientation');
            for i = 1:size(R,3)
                [U, ~, V] = svd(R(:,:,i));
                R(:,:,i) = U*V'; % Square up the rotaiton matrix
            end

            Rxyz = LinAlg.decompose_R(R)';
            
            %% Parse Status
            timeStatus = extractBefore(lines(idxStatus),' MAC: ');
            timeStatus = DataAnalysis.ParsePythonData.unix_time_to_matlab(str2double(timeStatus));
            
            rateEMG = str2double(extractBetween(lines(idxStatus),' EMG: ', ' Hz IMU'));
            rateIMU = str2double(extractBetween(lines(idxStatus),' IMU: ', ' Hz Batt'));
            
            %%
            data.timeEMG = timeEMG;
            data.dataEMG = dataEMG;

            data.timeIMU = timeIMU;
            data.Rxyz = Rxyz;
            
            data.timeBatt = timeBatt;
            data.dataBatt = dataBatt;

            data.rateEMG = rateEMG;
            data.rateIMU = rateIMU;
            data.timeStatus = timeStatus;
            
            %%
            if nargout < 1
            close all
            figure
            DataAnalysis.ParsePythonData.plot_myo_data(timeEMG, dataEMG, 'RAW EMG')
            figure
            DataAnalysis.ParsePythonData.plot_myo_data(timeIMU, Rxyz, 'Rxyz')
            figure
            DataAnalysis.ParsePythonData.plot_myo_data(timeBatt, dataBatt, 'Myo Batt %')
            figure
            DataAnalysis.ParsePythonData.plot_myo_data(timeStatus, [rateEMG rateIMU], 'Stream Rate')
            end
        end
        
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
        function matlab_time = unix_time_to_matlab(unix_time)
            % Convert unix time (epoc 1970) to matlab time
            zone = -4*60*60;
            matlab_time = datetime(unix_time+zone,'ConvertFrom','posixtime');
        end
        
    end
    
end

