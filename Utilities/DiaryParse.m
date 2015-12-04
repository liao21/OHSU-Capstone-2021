classdef DiaryParse
    methods (Static = true)
        function T = getTorque
            % DiaryParse.getTorque
            
            p = 'C:\tmp';
            s = dir(fullfile(p,'*diary.txt'));
            T = [];
            for i = 1:length(s)
                %Sensor Data--HR:    3.318 inch-lbs
                fp = fopen(fullfile(p,s(i).name),'r');
                fprintf('Parsing %d of %d: %s\n',i,length(s),s(i).name);
                C = textscan(fp,'%s','Delimiter',sprintf('\n'));
                
                tag = 'Sensor Data--HR:';
                dataLines = C{1}(strncmp(tag,C{1},length(tag)));
                dataVals = cellfun(@(s)str2double(s(17:26)),dataLines);
                T = cat(1,T,dataVals);
            end
            
            plot(T);
        end
    end
end