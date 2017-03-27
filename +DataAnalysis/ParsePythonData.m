classdef ParsePythonData
    %PARSEPYTHONDATA Summary of this class goes here
    %   Detailed explanation goes here
    
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
                    data(iTrial).move_complete = 1; % Will only get set if completion_time is set
                catch
                    continue
                end
            end
        end
        
        function data = getMotionTesterLog(file)
            
            % Get file info
            info = h5info(file);
            
            % Get first level data
            allClassNames = h5read(file, '/TrialLog/AllClassNames');
            classIdToTest = h5read(file, '/TrialLog/ClassIdToTest');
            
             % Initialize data storage struct
             trial_data = struct(...
                          'classDecision', {},...
                          'targetClass', {} ...
                          );
             
            data = struct(...
                          'AllClassNames', {allClassNames'},...
                          'ClassIdToTest', {classIdToTest'}, ...
                          'Data', trial_data ...
                          );   
            
            trialNames = {info.Groups.Groups.Groups(:).Name};
            
            % Loop through trials and pull data       
            for iTrial = 1:length(trialNames)
                classDecision = h5read(file, [trialNames{iTrial}, '/classDecision']);
                classDecision = double(classDecision);
                targetClass = h5read(file, [trialNames{iTrial}, '/targetClass']);
                targetClass = targetClass{1};
                data.Data(iTrial) = struct(...
                              'classDecision', {classDecision},...
                              'targetClass', {targetClass} ...
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
            end
            
            %%
            p = 'C:\tmp\';
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
        
        
    end
    
end

