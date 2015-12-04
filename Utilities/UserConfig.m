classdef UserConfig < handle
    % Class to hold user config variables.  This is setup to prompt the
    % user the first time it is accessed, and then rely on that file for
    % the remaining parameter calls
    %
    % Example: obj = UserConfig.getInstance(userConfigFile)
    %
    % Arguments: userConfigFile - full path to user config .xml
    % file
    % Revisions
    % 23APR2015 Armiger: Created
    properties (SetAccess = 'private')
        userConfigFile = 'user_config.xml';
        userRocFile = '';
        domNode  % Stores the Document Object Model node fro parsing
    end
    methods (Access = private)
        function obj = UserConfig
            % Creator is private to force singleton
        end
    end
    
    methods (Static)
        function singleObj = getInstance(userConfigFile)
            % Static creator method.  this will provide a singleton handle
            % to the class file
            %
            % Usage: obj = getInstance(userConfigFile)
            %
            % Reset: UserConfig.getInstance('')
            %
            % Arguments: userConfigFile - full path to user config .xml
            % file
            persistent localObj
            
            if nargin > 0 && isempty(userConfigFile)
                localObj = [];
                fprintf('Resetting Object\n');
                return
            end
            
            if isempty(localObj) || ~isvalid(localObj)
                if nargin < 1
                    %userConfigFile = 'user_config.xml';
                    
                    [FileName,PathName,FilterIndex] = uigetfile('user_config.xml');
                    if FilterIndex == 0
                        % User Cancelled
                        userConfigFile = '';
                    else
                        userConfigFile = fullfile(PathName,FileName);
                    end
                end
                
                % ensure full path is resolved
                userConfigFile = which(userConfigFile);
                fprintf('[%s] Calling constructor with config file %s\n',mfilename,userConfigFile);
                
                localObj = UserConfig;
                localObj.userConfigFile = userConfigFile;
                
                % read the file
                if ~isempty(userConfigFile)
                    localObj.domNode = xmlread(userConfigFile);
                end
                
            else
                %fprintf('[%s] Returning existing object\n',mfilename);
            end
            singleObj = localObj;
            
            % read the roc table on startup to store path
            %UserConfig.getUserConfigVar('rocTable','WrRocDefaults.xml');
        end
        function success = reload
            % Reload the specified xml file
            obj = UserConfig.getInstance;
            userFile = obj.userConfigFile;
            
            % read the file
            obj.domNode = xmlread(userFile);
            
            success = true;
        end
        
        
        function result = getUserConfigVar(tagName,defaultValue)
            %charResult = UserConfig.getUserConfigVar(tagName,defaultValue)
            % Read tag from user config xml file
            %
            
            obj = UserConfig.getInstance;
            userFile = obj.userConfigFile;
            
            % default output
            result = defaultValue;
            
            a = obj.domNode;
            
            if isempty(a)
                fprintf('[%s] No file %s found\n',mfilename,userFile);
                return
            end
            
            try
                
                isFound = false;
                v = a.getElementsByTagName('add');
                for i = 1:v.getLength
                    t = v.item(i-1);
                    key = char(t.getAttribute('key'));
                    if strcmp(key,tagName)
                        result = char(t.getAttribute('value'));
                        isFound = true;
                        break;
                    end
                end
                
                if isFound
                    fprintf('[%s] %s=%s\n',mfilename,tagName,result);
                else
                    fprintf('[%s] %s not found. Default=%s\n',mfilename,tagName,result);
                end
                
                % convert value to the class of the default parameter.
                if ~ischar(defaultValue)
                    % example '[1 3]'  --> 1 3
                    [x, status] = str2num(result); %#ok<ST2NM>
                    if status
                        result = x;
                    else
                        warning('Failed to cast xml key-value');
                    end
                end
                
            catch ME
                warning(ME.message)
                fprintf('[%s.m] Failed to parse tag "%s" entry in file "%s"\n',mfilename,tagName,userFile);
                result = defaultValue;
            end
            
            
            % Add a check for file references to add the full path if
            % omitted.  THis is a special case for roc tables
            
            switch tagName
                case 'rocTable'
                    
                    % check if the rocTable has path info
                    missingPath = isempty(fileparts(result));
                    noStoredPath = isempty(obj.userRocFile);
                    
                    if missingPath && noStoredPath
                        % store the table with path
                        obj.userRocFile = which(result);
                        result = obj.userRocFile;
                        fprintf('[%s.m] Storing full path tag "%s": "%s"\n',mfilename,tagName,result);
                    elseif missingPath && ~noStoredPath
                        % use the stored path and file
                        result = obj.userRocFile;
                    else
                        % Path exists in xml so use it
                    end
                    
                    assert(exist(result,'file') > 0,'XML Roc file %s not found %s',result);
                    
            end
            
            
            
            
            
        end
    end
end
