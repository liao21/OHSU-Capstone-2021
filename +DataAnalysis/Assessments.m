classdef Assessments
    methods (Static = true)
        function hAxes = MotionTesterConfusionPlot(structTrialLog)
            % Post-process a MotionTester trial log structure and plot a
            % confusion matrix
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
            
            
        end
    end
end