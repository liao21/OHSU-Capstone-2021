classdef ParsePythonData
    %PARSEPYTHONDATA Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
    end
    
    methods
        function get_hci_log(file)
            % ParsePythonData.get_hci_log('hci0_myo.log')
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

