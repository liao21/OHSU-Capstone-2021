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
                %%
                
                cellTable(2:end,2:end) = num2cell(normalizedMat(trainedClassId,trainedClassId)*100)
                
                xlStart = sprintf('A%d',3+numClasses);
                xlStop = sprintf('%c%d', uint8('A')+numClasses, 2*(numClasses+1)+1);
                xlRange = sprintf('%s:%s',xlStart,xlStop);
                xlswrite(outputFile,cellTable,l,xlRange);
                
                %%
                xlRange = sprintf('A%d:B%d',2*(numClasses+1)+3,2*(numClasses+1)+3);
                xlswrite(outputFile,{'Percent correctly classified:' hClassifier.computeError*100},l,xlRange);
                
                obj = [];
            end
        end
    end
end
