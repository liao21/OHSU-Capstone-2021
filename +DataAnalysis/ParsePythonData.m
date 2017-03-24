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
                              'intent_time_history', {h5read(file, [trialNames{iTrial}, '/intent_time_history'])}, ...
                              'position_time_history', {h5read(file, [trialNames{iTrial}, '/position_time_history'])}, ...
                              'target_error', {h5read(file, [trialNames{iTrial}, '/target_error'])}, ...
                              'target_joint', {h5read(file, [trialNames{iTrial}, '/target_joint'])}, ...
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
                classDecision = h5read(file, [trialNames{iTrial}, '/classDecision'])
                classDecision = double(classDecision);
                targetClass = h5read(file, [trialNames{iTrial}, '/targetClass']);
                targetClass = targetClass{1};
                data.Data(iTrial) = struct(...
                              'classDecision', {classDecision},...
                              'targetClass', {targetClass} ...
                              );
            end
        end
        
        function C = get_hci_log(file)
            % DataAnalysis.ParsePythonData.get_hci_log('hci0_myo.log')
            if nargin < 1
                p = '';
                f = 'hci0_myo.log';
                %f = 'MPL_WWW_1999-12-31_19-00-25.log';
                file = fullfile(p,f);
            end
            %%
            filetext = fileread(file);
            
            %%
            C = str2double(regexp(filetext,'(?<=Battery Level: )[0-9]+','match'))
            
            
            %%
            
            
            
            
        end
        
        
        
    end
    
end

