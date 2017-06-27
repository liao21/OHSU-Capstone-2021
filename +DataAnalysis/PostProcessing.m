classdef PostProcessing
    methods (Static = true)
        function hData = processFeaturesBatch(dataPath,subjectId)
            % Show all training data EMG FEATURE reports
            %
            % Inputs:
            %   dataPath - Full path to directory containing *.trainingData files
            %   subjectId - Short Identifier for subject
            %
            % Usage:
            %   DataAnalysis.PostProcessing.processEmgBatch('c:\data\Myo_01\','MYO_01')
            
            % subjectId = 'MYO_01';
                        
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_FeatureData.pptx']);
            
            if isempty(dataPath)
                hData = [];
                return
            elseif ischar(dataPath)
                % treat input as a path and load the data
                hData = TrainingDataAnalysis.batchLoadTrainingData(dataPath);
            else
                % treat input as data
                hData = dataPath;
            end
            
            hPpt = PptMaker;
            hPpt.Title = 'EMG Features';
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
                    [~] = hData(i).plot_features_sorted_class(); % output arg disables image export
                end
                
                drawnow
                
                hPpt.addslide(f);
                
            end
            
            hPpt.close();
            
        end
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
            
            if isempty(dataPath)
                hData = [];
                return
            elseif ischar(dataPath)
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
            
            if isempty(dataPath)
                hData = [];
                return
            elseif ischar(dataPath)
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
                
                if ~(hData(i).SampleCount > 0)
                    continue
                end
                hAxes = GUIs.guiPlotPca(hData(i),f);
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
            
            if isempty(dataPath)
                hData = [];
                return
            elseif ischar(dataPath)
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
                
                if isempty(hData(i).getEnabledClassLabels)
                    continue
                end
                
                % Process goes here
                hClassifier = SignalAnalysis.Lda;
                hClassifier.initialize(hData(i));
                if isempty(hClassifier.getActiveChannels)
                    continue
                end
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
                s = [rdir(fullfile(dataPath,'*.assessmentLog')); rdir(fullfile(dataPath,'*MOTION_TESTER_LOG.hdf5'))];
                
                % sort by date
                [~,idx] = sort([s.datenum]);
                s = s(idx);
                
                for i = 1:length(s)
                    if any(strfind(s(i).name, '.assessmentLog'))
                        structData(i) = load(s(i).name,'-mat');  %#ok<AGROW>
                    elseif any(strfind(s(i).name, '.hdf5'))
                        structData(i).structTrialLog = DataAnalysis.ParsePythonData.getMotionTesterLog(s(i).name);  %#ok<AGROW>
                    end
                end
                
            else
                error('Expected a data path to *.assessmentLog or *.hdf5 files');
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
        function fileData = processTacBatch(dataPath,subjectId)
            
            % Output file (PPTX)
            outDir = pwd;
            outputFile = fullfile(outDir,[subjectId '_TAC.pptx']);
            
            if ischar(dataPath)
                % treat input as a path and load the data
                s = [rdir(fullfile(dataPath,'*.tacAssessment')); rdir(fullfile(dataPath,'*TAC*LOG*.hdf5'))];
                
                if isempty(s)
                    error('No files found: %s\n',fullfile(dataPath,'*.tacAssessment'))
                end
                
                % sort by date
                [~,idx] = sort([s.datenum]);
                s = s(idx);
                
                for i = 1:length(s)
                    if any(strfind(s(i).name, '.tacAssessment'))
                        newData = load(s(i).name,'-mat');
                        fileData{i} = newData; %#ok<AGROW>
                    elseif any(strfind(s(i).name, '.hdf5'))
                        newData = DataAnalysis.ParsePythonData.getTACLog(s(i).name);
                        fileData{i}.structTrialLog = newData; %#ok<AGROW>
                    end        
                end
                
            else
                error('Expected a data path to *.tacAssessment or *.hdf5 files');
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
                
                if isfield(fileData{i}.structTrialLog, 'is_python_data')  % Python data
                    nJoints = length(fileData{i}.structTrialLog(1).target_joint);
                else
                    nJoints  = 1;  % TODO: Update this logic
                end
                
                switch nJoints
                    case 3
                        fprintf(' %s is a TAC-3\n',s(i).name);
                    case 1
                        fprintf(' %s is a TAC-1\n',s(i).name);
                end
                
                [completionPct, cellSummary, cellHistory, pathEfficiency, nUniqueClasses, nUniqueDOF] = DataAnalysis.Assessments.parseTac(fileData{i}.structTrialLog);
                
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
                
                switch nJoints
                    case 1
                        overall = {'Completion Pct',num2str(completionPct,'%4.1f'); ...
                            'Path Efficiency',num2str(pathEfficiency,'%4.1f');...
                            'Num Classes', nUniqueClasses};
                    case 3
                        overall = {'Completion Pct',num2str(completionPct,'%4.1f'); ...
                            'Path Efficiency (Joint1)',num2str(pathEfficiency(1),'%4.1f');...
                            'Path Efficiency (Joint2)',num2str(pathEfficiency(2),'%4.1f');...
                            'Path Efficiency (Joint3)',num2str(pathEfficiency(3),'%4.1f');...
                            'Num Classes', nUniqueClasses};
                end
                
                % Add new Num DOF for Python
                if isfield(fileData{i}.structTrialLog, 'is_python_data')
                    overall = [overall;...
                        {'Num DOF', nUniqueDOF}];
                end
                
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
                    'Position',[5.05 2.0 4.9 size(cellSummary,1) * 0.25 ],...
                    'FontSize',10)
                
            end
            
            hPpt.close();
            
        end
        
    end
end
