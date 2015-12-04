classdef ExportConfusionMatrix
    methods
        function obj = ExportConfusionMatrix
            % run training accuracy and confusion analysis
            %
            % 1) finds trainingData files in all subdirectories
            % 2) loads each set, computes training parameters, and check
            
            UserConfig.getInstance('MPL_04_user_config.xml');
            p = UserConfig.getUserConfigVar('userBasePath','');
            d = rdir(fullfile(p,'\MPL_04 session 1\*.trainingData'));
            outputFile = 'c:\tmp\test.xlsx';
            
            %%
            for i = 1:length(d);
                hTraining = TrainingDataAnalysis(d(i).name)
                
                [pathstr,name,ext] = fileparts(d(i).name);
                l = name;
                
                hClassifier = SignalAnalysis.Lda
                hClassifier.initialize(hTraining)
                hClassifier.train
                hClassifier.computeError
                [confusionMat, normalizedMat] = hClassifier.computeConfusion;
                classNames = hClassifier.getClassNames;
                trainedClassId = unique(hTraining.getEnabledClassLabels);
                numClasses = length(trainedClassId);
                
                cellTable = cell(numClasses+1)
                cellTable(2:end,1) = classNames(trainedClassId)
                cellTable(1,2:end) = classNames(trainedClassId)
                cellTable(2:end,2:end) = num2cell(confusionMat(trainedClassId,trainedClassId))
                
                xlStart = 'A1';
                xlStop = sprintf('%c%d', uint8('A')+numClasses, 1+numClasses);
                xlRange = sprintf('%s:%s',xlStart,xlStop);
                xlswrite(outputFile,cellTable,l,xlRange);
                %
                
                cellTable(2:end,2:end) = num2cell(normalizedMat(trainedClassId,trainedClassId)*100)
                
                xlStart = sprintf('A%d',3+numClasses);
                xlStop = sprintf('%c%d', uint8('A')+numClasses, 2*(numClasses+1)+1);
                xlRange = sprintf('%s:%s',xlStart,xlStop);
                xlswrite(outputFile,cellTable,l,xlRange);
                
                %
                xlRange = sprintf('A%d:B%d',2*(numClasses+1)+3,2*(numClasses+1)+3);
                xlswrite(outputFile,{'Percent correctly classified:' hClassifier.computeError*100},l,xlRange);
                
                obj = [];
            end
        end
    end
    methods (Static)
        function MotionTesterConfusion
            % DataAnalysis.ExportConfusionMatrix.MotionTesterConfusion
            %
            % Goal is to create a confusion matrix from a Motion TEster
            % assessment Log.  Step 1 will be to load the structTrialLog,
            % filter on the tested classes and computer the number of
            % incorrect classess among the target class.  Note there may be
            % some versioning issues to work out with older files

            UserConfig.getInstance('JHMI_TH01_L_user_config.xml');

            % Subject Id
            subjectId = UserConfig.getUserConfigVar('userFilePrefix','');
            subjectId = subjectId(1:end-1);
            
            % Source files (*.assessmentLog)
            p = UserConfig.getUserConfigVar('userBasePath','');
            s = rdir(fullfile(p,'*.assessmentLog'));

            % Output file (PPTX)
            outputFile = fullfile('c:\tmp',[subjectId '_MotionTesterConfusion.pptx']);

            
            if isempty(s)
                error('No files found in: %s',fullfile(p,'*.assessmentLog'));
            end
            
            for iFile = 1:length(s)
                load(s(iFile).name,'-mat');
                sLog = structTrialLog;
                
                numClasses = length(sLog.AllClassNames);
                
                testedClasses = sLog.AllClassNames(sLog.ClassIdToTest);
                
                confuseMat = zeros(numClasses);
                for iClass = 1:length(sLog.Data)
                    testClassId = sLog.ClassIdToTest(iClass);
                    row = accumarray(sLog.Data(iClass).classDecision(:),1,[numClasses 1])';
                    confuseMat(testClassId,:) = row;
                end
                
                %PlotUtils.confusionMatrix(confuseMat,sLog.AllClassNames)
                reducedMat = confuseMat(sLog.ClassIdToTest,sLog.ClassIdToTest);
                
                % create figure
                p = get(0,'DefaultFigurePosition');
                p = [p(1) p(2)/2 800 600];
                f = figure('Units','pixels','ToolBar','figure','Position',p);
                hAxes = axes('Parent',f);
                
                % plot
                PlotUtils.confusionMatrix(reducedMat,testedClasses,hAxes)
                
                % update title
                [~,fname,~] = fileparts(s(iFile).name);
                hAxes.Title.String = { fname hAxes.Title.String };
                hAxes.Title.Interpreter = 'None';
                drawnow
                
            end %iFiles
            
            titleInfo.Title = 'Confusion Matrices - Motion Tester';
            titleInfo.Author = 'RSA';
            titleInfo.SubTitle = {subjectId; datestr(now)};
            
            PlotUtils.copyFiguresToPowerpoint(outputFile, titleInfo)
            
            
        end %ExportMotionTester
        
    end %methods
end %classdef
