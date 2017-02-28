classdef ParsePythonData
    %PARSEPYTHONDATA Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
    end
    
    methods (Static = true)
        function data = getTACLog(file)
            
            if nargin < 1
                p = '';
                %f = '2017-02-28_14-50-02_TAC1_LOG.hdf5';
                f = '2017-02-28_14-37-18_TAC3_LOG.hdf5';
                file = fullfile(p,f);
            end
            
            % Get file info
            info = h5info(file);
            trialNames = {info.Groups.Groups(:).Name};
            
            % Initialize data storage struct
            data = struct(...
                          'completion_time', {},...
                          'intent_time_history', {}, ...
                          'position_time_history', {}, ...
                          'target_error', {}, ...
                          'target_joint', {}, ...
                          'target_position', {},...
                          'time_history', {}...
                          );
            
            % Loop through trials and pull data       
            for iTrial = 1:length(trialNames)
                data(iTrial) = struct(...
                              'completion_time', {h5read(file, [trialNames{iTrial}, '/completion_time'])},...
                              'intent_time_history', {h5read(file, [trialNames{iTrial}, '/intent_time_history'])}, ...
                              'position_time_history', {h5read(file, [trialNames{iTrial}, '/position_time_history'])}, ...
                              'target_error', {h5read(file, [trialNames{iTrial}, '/target_error'])}, ...
                              'target_joint', {h5read(file, [trialNames{iTrial}, '/target_joint'])}, ...
                              'target_position', {h5read(file, [trialNames{iTrial}, '/target_position'])},...
                              'time_history', {h5read(file, [trialNames{iTrial}, '/time_history'])}...
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

