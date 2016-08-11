classdef PostProcessing
    methods (Static = true)
        function hData = processEmgBatch(dataPath,subjectId,doFilter)
            % Show all training data EMG reports
            %
            % Inputs:
            %   dataPath - Full path to directory containing *.trainingData files
            %   subjectId - Short Identifier for subject
            %
            % Usage:
            %   DataAnalysis.PostProcessing.processEmgBatch('c:\data\Myo_01\','MYO_01')
            
            % subjectId = 'MYO_01';
            
            if nargin < 3
                doFilter = false;
            end
            
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_EmgData.pptx']);
            
            if ischar(dataPath)
                % treat input as a path and load the data
                hData = TrainingDataAnalysis.batchLoadTrainingData(dataPath);
            else
                % treat input as data
                hData = dataPath;
            end
            
            hPpt = PptMaker;
            hPpt.Title = 'EMG Signal History';
            hPpt.Author = 'RSA';
            hPpt.SubTitle = {subjectId; datestr(now)};
            hPpt.OutputFile = outputFile;
            hPpt.initialize();
            
            f = figure(255);
            f.Position = [50 50 1600 900];
            
            for i = 1:length(hData)
                % setup figure named with filename
                [pname,fname,~] = fileparts(hData(i).fullFileName);
                [~,lastFolder,~] = fileparts(pname);
                
                f.Name = fullfile(lastFolder,fname);
                
                if hData(i).SampleCount > 0
                    [~] = hData(i).plot_emg_with_breaks(doFilter); % output arg disables image export
                end
                
                drawnow
                
                hPpt.addslide(f);
                
            end
            
            hPpt.close();
            
        end
        function hData = processPcaBatch(dataPath,subjectId)
            % Plot Principal Components
            %
            % Inputs:
            %   dataPath - Full path to directory containing *.trainingData files
            %   subjectId - Short Identifier for subject
            %
            % Usage:
            %   DataAnalysis.PostProcessing.processPcaBatch('c:\data\Myo_01\','MYO_01')
            
            % subjectId = 'MYO_01';
            
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_Pca.pptx']);
            
            if ischar(dataPath)
                % treat input as a path and load the data
                hData = TrainingDataAnalysis.batchLoadTrainingData(dataPath);
            else
                % treat input as data
                hData = dataPath;
            end
            
            hPpt = PptMaker;
            hPpt.Title = 'PCA Analysis';
            hPpt.Author = 'RSA';
            hPpt.SubTitle = {subjectId; datestr(now)};
            hPpt.OutputFile = outputFile;
            hPpt.initialize();
            
            f = figure(255);
            f.Position = [50 50 1600 900];
            
            for i = 1:length(hData)
                % setup figure named with filename
                [~,fname,~] = fileparts(hData(i).fullFileName);
                f.Name = fname ;
                
                if hData(i).SampleCount > 0
                    hAxes = GUIs.guiPlotPca(hData(i),f);
                end
                
                titleTxt = sprintf('%s Total=%d Active=%d',f.Name,...
                    length(hData(i).getClassLabels),length(hData(i).getAllClassLabels));
                title(hAxes(1),titleTxt,'Interpreter','None');
                
                drawnow
                
                hPpt.addslide(f);
                
            end
            
            hPpt.close();
            
        end
        function hData = processDataConfusionBatch(dataPath,subjectId)
            
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_DataConfusion.pptx']);
            
            if ischar(dataPath)
                % treat input as a path and load the data
                hData = TrainingDataAnalysis.batchLoadTrainingData(dataPath);
            else
                % treat input as data
                hData = dataPath;
            end
            
            hPpt = PptMaker;
            hPpt.Title = 'Confusion Matrices';
            hPpt.Author = 'RSA';
            hPpt.SubTitle = {subjectId; datestr(now)};
            hPpt.OutputFile = outputFile;
            hPpt.initialize();
            
            f = figure(255);
            f.Position = [50 50 1600 900];
            
            for i = 1:length(hData)
                % setup figure named with filename
                [~,fname,~] = fileparts(hData(i).fullFileName);
                f.Name = fname;
                
                if hData(i).SampleCount == 0
                    continue
                end
                
                % Process goes here
                hClassifier = SignalAnalysis.Lda;
                hClassifier.initialize(hData(i));
                output = hClassifier.train;
                if isempty(output)
                    continue
                end
                
                clf(f)
                hAxes = axes('Parent',f);
                
                hClassifier.plotConfusion(hAxes);
                msgAccuracy = sprintf('Actual versus predicted class, Avg = %4.1f %%',100*hClassifier.computeError);
                msgSamples = sprintf('Total=%d Active=%d',length(hData(i).getClassLabels),length(hData(i).getAllClassLabels));
                
                t = { msgAccuracy, msgSamples };
                title(t,'Parent',hAxes,'Interpreter','None');
                drawnow
                
                drawnow
                
                hPpt.addslide(f);
                
            end
            
            hPpt.close();
            
        end
        function structData = processMotionTesterBatch(dataPath,subjectId)
            
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_MotionTester.pptx']);
            
            if ischar(dataPath)
                % treat input as a path and load the data
                s = rdir(fullfile(dataPath,'*.assessmentLog'));
                
                % sort by date
                [~,idx] = sort([s.datenum]);
                s = s(idx);
                
                for i = 1:length(s)
                    structData(i) = load(s(i).name,'-mat');  %#ok<AGROW>
                end
                
            else
                error('Expected a data path to *.assessmentLog files');
            end
            
            hPpt = PptMaker;
            hPpt.Title = 'Motion Tester Confusion Matrices';
            hPpt.Author = 'RSA';
            hPpt.SubTitle = {subjectId; datestr(now)};
            hPpt.OutputFile = outputFile;
            hPpt.initialize();
            
            f = figure(255);
            f.Position = [50 50 1600 900];
            
            for i = 1:length(structData)
                % setup figure named with filename
                [~,fname,~] = fileparts(s(i).name);
                f.Name = fname;
                
                % Process goes here
                clf(f)
                hAxes = axes('Parent',f);
                
                [completionPct, motionPct] = DataAnalysis.Assessments.MotionTesterConfusionPlot(structData(i).structTrialLog,hAxes);
                
                t = { fname, sprintf('Completion Accuracy = %4.1f %%; Motion Accuracy = %4.1f %%',completionPct,motionPct)};
                title(t,'Parent',hAxes,'Interpreter','None');
                
                drawnow
                
                hPpt.addslide(f);
                
            end
            
            hPpt.close();
            
        end
        function fileData = processTac1Batch(dataPath,subjectId)
            
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_Tac1.pptx']);
            
            if ischar(dataPath)
                % treat input as a path and load the data
                s = rdir(fullfile(dataPath,'*.tacAssessment'));
                
                if isempty(s)
                    error('No files found: %s\n',fullfile(dataPath,'*.tacAssessment'))
                end
                
                % sort by date
                [~,idx] = sort([s.datenum]);
                s = s(idx);
                
                for i = 1:length(s)
                    try
                        newData = load(s(i).name,'-mat');
                    catch loadError
                        newData = [];
                        warning(loadError.message);
                    end
                    
                    % Load whatever is in the file
                    fileData{i} = newData; %#ok<AGROW>
                end
                
            else
                error('Expected a data path to *.tacAssessment files');
            end
            
            hPpt = PptMaker;
            hPpt.Title = 'TAC Results';
            hPpt.Author = 'RSA';
            hPpt.SubTitle = {subjectId; datestr(now)};
            hPpt.OutputFile = outputFile;
            hPpt.initialize();
            
            for i = 1:length(fileData)
                [pname,fname,~] = fileparts(s(i).name);
                [~,basedir,~] = fileparts(pname);
                
                fname = fullfile(basedir,fname);
                
                thisAssessment = fileData{i};
                
                % handle case where loaded file is empty (corrupt?)
                if isempty(thisAssessment)
                    continue
                end
                
                if isfield(thisAssessment.structTrialLog(1),'targetClass') && isnumeric(fileData{i}.structTrialLog(1).targetClass)
                    fprintf(' %s is a TAC-3\n',s(i).name);
                    continue
                else
                    fprintf(' %s is a TAC-1\n',s(i).name);
                end
                
                [completionPct, cellSummary, cellHistory, pathEfficiency] = DataAnalysis.Assessments.parseTac1(fileData{i}.structTrialLog);
                
                % convert precision
                for iCell = 1:numel(cellSummary)
                    cellVal = cellSummary{iCell};
                    if isnumeric(cellVal) && ~isempty(strfind(num2str(cellVal),'.'))
                        cellSummary{iCell} = num2str(cellVal,'%4.1f');
                    end
                end
                
                % convert precision
                for iCell = 1:numel(cellHistory)
                    cellVal = cellHistory{iCell};
                    if isnumeric(cellVal) && ~isempty(strfind(num2str(cellVal),'.'))
                        cellHistory{iCell} = num2str(cellVal,'%4.1f');
                    end
                end
                
                overall = {'Completion Pct',num2str(completionPct,'%4.1f'); ...
                    'Path Efficiency',num2str(pathEfficiency,'%4.1f');...
                    'Num Classes',size(cellSummary,1)-1};
                
                % Add content
                hPpt.SlideNames = cat(1,hPpt.SlideNames,fname);
                exportToPPTX('addslide');
                exportToPPTX('addtext',fname); %,'Position','Title 1');
                
                exportToPPTX('addtable',cellHistory,...
                    'Position',[0.05 0.5 4.95 size(cellHistory,1) * 0.10 ],...
                    'FontSize',10)
                exportToPPTX('addtable',overall,...
                    'Position',[6.05 0.5 3 0.25 ],...
                    'FontSize',10)
                exportToPPTX('addtable',cellSummary,...
                    'Position',[5.05 1.5 4.9 size(cellSummary,1) * 0.25 ],...
                    'FontSize',10)
            end
            
            hPpt.close();
            
        end
    end
end
