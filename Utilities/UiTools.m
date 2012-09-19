classdef UiTools
    % Class with static methods for common ui tasks
    methods (Static = true)
        function hTimer = create_timer(timerName,TimerFcn)
            % Create a named timer which will search for previous versions
            % and delete them prior to creation.  Also includes gerneric
            % start and stop callbacks
            %
            % Typical Usage:
            % hTimer = UiTools.create_timer(mfilename,@(src,evt)my_timer_callback);
            % hTimer.Period = 0.05;
            
            hExisting = timerfindall('Name',timerName);
            if ~isempty(hExisting)
                stop(hExisting);
                delete(hExisting);
            end
            
            t = timer;
            t.Name = timerName;
            t.ExecutionMode = 'fixedRate';
            t.TimerFcn = TimerFcn;
            t.StartFcn = @(src,evt)fprintf('Started Timer: %s\tPeriod: %f\n',timerName,t.Period);
            t.StopFcn = @(src,evt)fprintf('Stopped Timer: %s\tPeriod: %f\tAveragePeriod: %f\n',timerName,t.Period,t.AveragePeriod);
            
            hTimer = t;
        end
        function hFigure = create_figure(figureName,figureTag)
            % Usage: hFigure = UiTools.create_figure(figureName,figureTag)
            
            if nargin < 2
                figureTag = strrep(figureName,' ','_');
            end
            
            % Consts
            figureColor = get(0,'defaultUicontrolBackgroundColor');
            
            % Startup
            %Search if the figure exists
            existingFigs = findall(0,'tag',figureTag);
            
            if ~isempty(existingFigs)
                %Figure exists so bring Figure to the focus
                delete(existingFigs)
            end
            
            % Figure Setup
            hFigure = figure(...
                'Units','pixels',...
                'Color',figureColor,...
                'HandleVisibility','callback',...
                'Renderer','OpenGL',...
                'Resize','off',...
                'Menubar','none',...
                'Toolbar','none',...
                'NumberTitle','off',...
                'IntegerHandle','off',...
                'Tag',figureTag,...
                'Name',figureName);
        end
        function save_temp_file(defaultFile,storedVariable)
            % Create a temp file that will be stored in the tempdir
            % directory (e.g. C:\Users\armigrs1\AppData\Local\Temp\)
            %
            % The input "defaultFile" is used as the filename
            
            fullFile = fullfile(tempdir,defaultFile);
                        
            try
                fprintf('[%s] Saving temp file "%s"\n',mfilename,fullFile);
                save(fullFile,'storedVariable','-mat');
            catch ME
                msg = { 'Error creating default file', fullFile , ...
                    'Error was: ' ME.message};
                errordlg(msg,'Error setting defaults');
                disp('FAILED');
                disp(storedVariable);
                return
            end
        end
        function storedVariable = load_temp_file(defaultFile)
            % Load temp file from the tempdir
            % directory (e.g. C:\Users\armigrs1\AppData\Local\Temp\)
            %
            % The input "defaultFile" is used as the filename

            % Load a mat file in the temp directory
            
            storedVariable = [];
            
            fullFile = fullfile(tempdir,defaultFile);
            if ~exist(fullFile,'file')
                return
            end
            
            try
                S = load(fullFile,'-mat');
            catch ME
                msg = { 'Error reading default file', fullFile , ...
                    'Error was: ' ME.message};
                errordlg(msg,'Error setting defaults');
                return
            end
            
            if isfield(S,'storedVariable')
                storedVariable = S.storedVariable;
            end
        end
        function fullFilename = ui_select_data_file(extension)
            % Provides a save dialog with the default file set as the
            % current date and time with extention reflecting contents
            % extension = '.assessmentLog'
            
            filePrefix = 'JH_TH01_';  %TODO, abstract this
            filePrefix = 'AGH_';  %TODO, abstract this
            
            FilterSpec = ['*' extension];
            DialogTitle = 'Select File to Write';
            DefaultName = [filePrefix datestr(now,'yyyymmdd_HHMMSS') extension];            
            [FileName,PathName,FilterIndex] = uiputfile(FilterSpec,DialogTitle,DefaultName);
            
            if FilterIndex == 0
                fullFilename = [];
            else
                fullFilename = fullfile(PathName,FileName);
            end
        end
    end
end
