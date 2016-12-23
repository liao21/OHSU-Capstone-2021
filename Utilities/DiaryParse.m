classdef DiaryParse
    methods (Static = true)
        function T = getTorque(p)
            % DiaryParse.getTorque
            
            if nargin < 1
                p = 'C:\tmp';
            end
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
                
                % remove outliers
                id = dataVals > 200;
                dataVals(id) = [];
                fprintf('Removed %d outliers\n',length(id));
                
                T = cat(1,T,dataVals);
            end
            t = (1:length(T))*0.05/60;
            Tconv = T*0.112984829; % N-m
            maxTconv = max(Tconv);
            minTconv = min(Tconv);
            avgTconv = mean(abs(Tconv));
            f = figure;
            hold on
            plot(t,Tconv);
            plot([0 max(t)],[maxTconv maxTconv],'k--');
            plot([0 max(t)],[minTconv minTconv],'k--');
            plot([0 max(t)],[avgTconv avgTconv],'k--');
            title(sprintf('Max=%6.2f N-m; Min=%6.2f N-m; AvgMag=%6.2f N-m', maxTconv, minTconv, avgTconv) )
            xlabel('Duration, minutes')
            ylabel('Torque, Nm')
            f.Name = p;
            f.Position = [50 50 800 450];
            drawnow

            
        end
    end
end