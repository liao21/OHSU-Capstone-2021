classdef Assessments
    methods (Static = true)
        function [completionAccuracy, motionAccuracy, hAxes] = MotionTesterConfusionPlot(structTrialLog, hAxes)
            % Assessments.MotionTesterConfusionPlot
            % Post-process a MotionTester trial log structure and plot a
            % confusion matrix

            if nargin < 2
                % create figure
                p = get(0,'DefaultFigurePosition');
                p = [p(1) p(2)/2 800 600];
                f = figure('Units','pixels','ToolBar','figure','Position',p);
                hAxes = axes('Parent',f);
            end
            sLog = structTrialLog;
            
            if ~isfield(sLog,'AllClassNames')
                % old file format.  abort process
                [completionAccuracy, motionAccuracy] = deal(nan);
                hAxes = [];
                return
            end
            numClasses = length(sLog.AllClassNames);
            
            testedClasses = sLog.AllClassNames(sLog.ClassIdToTest);
            
            confuseMat = zeros(numClasses);
            for iClass = 1:length(sLog.Data)
                testClassId = sLog.ClassIdToTest(iClass);
                row = accumarray(sLog.Data(iClass).classDecision(:),1,[numClasses 1])';
                confuseMat(testClassId,:) = row;
            end
            
            reducedMat = confuseMat(sLog.ClassIdToTest,sLog.ClassIdToTest);
            
            % compute confusion as percentage
            % Compute the total number of examples
            classSum = sum(reducedMat,2);
            % Normalize based on the number of examples
            normMat = reducedMat ./ repmat(classSum,1,size(reducedMat,1));
            % should not occur, but if divided by zero, set to zero
            normMat(isnan(normMat)) = 0;

            % plot
            PlotUtils.confusionMatrix(reducedMat,testedClasses,hAxes)
            
            completed = diag(reducedMat) == 10;
            completionAccuracy = sum(completed) ./ length(completed) .* 100;
            motionAccuracy = mean(diag(normMat)) .* 100;
            
        end
        function [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = parseTac1(structTrialLog)
            % [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = DataAnalysis.Assessments.parseTac1(structTrialLog)
            % Parse the TAC 1 trial data.  return the scalar accuracy of
            % number of successful trials, as well as cell array tables of
            % the summary statistics and tiral history

            % get the number of completions over the total trials
            completed = [structTrialLog.moveComplete];
            completionAccuracy = sum(completed) ./ length(completed) .* 100;
                        
            % Compute path efficiency for each trial
            nTrials = length(structTrialLog);            
            pathEfficiency = nan(1,nTrials);
            for i = 1:nTrials
                t = structTrialLog(i);
                
                if ~isfield(t,'targetAngle')
                    % Some legacy tests c 2014 may omit this
                    cellSummary = {};
                    cellHistory = {};
                    meanEfficiency = [];
                    return
                end
                
                
                % perfect path efficiency is each incremental motion (diff)
                % sums to exactly the angle difference.  deviations from
                % path will add to the user length
                angDiff = t.targetAngle - t.startAngle;
                idJoint = find(angDiff ~= 0);
                assert(length(idJoint) == 1,'Expected only one angle change during trial for TAC-1');
                
                jointAng = t.angleTimeHistory(:,idJoint+1); % add 1 since first col is time
                
                if jointAng(1) ~= t.startAngle(idJoint)
                    warning('Expected Start angle of %f, got %f',...
                        t.startAngle(idJoint),jointAng(1));
                    minDist = abs(jointAng(1) - t.targetAngle(idJoint));
                else
                    minDist = abs(angDiff(idJoint));
                end
                
                % user dist only calculated if move was completed
                userDist = sum(abs(diff(jointAng))) * t.moveComplete;
                pathEfficiency(i) = minDist / userDist * 100;
            end

            % zero score for incomplete moves
            pathEfficiency(isinf(pathEfficiency)) = 0;
            
            % it is possible for user path efficiency to be greater that
            % 100% since with the error bands on the target the trial can
            % complete without fully making it to the final value
            pathEfficiency(pathEfficiency > 100) = 100;            
            
            % Compute summary stats by grouping classes
            allTrials = {structTrialLog.targetClass};
            testedClasses = unique(allTrials);
            nUnique = length(testedClasses);
            motionTrials = nan(1,nUnique);
            motionCompleted = nan(1,nUnique);
            motionEfficiency = nan(1,nUnique);
            for i = 1:nUnique
                thisClass = strcmp(testedClasses(i),allTrials);
                motionCompleted(i) = sum(thisClass & completed);
                motionTrials(i) = sum(thisClass);
                motionEfficiency(i) = mean(pathEfficiency(thisClass));
            end
            motionAccuracy = motionCompleted ./ motionTrials * 100;
            
            % print by trial
            cellHistory = [{'Class Name' 'Elapsed Time' 'Completed' 'Path Efficiency'}; ...
                {structTrialLog.targetClass}' num2cell([structTrialLog.tElapsed]') num2cell([structTrialLog.moveComplete]') num2cell(pathEfficiency')];
            
            % print summary
            cellSummary = [{'Class Name' 'Num Trials' 'Num Completed' 'Mean Completion' 'Mean Efficiency'}; ...
                [testedClasses' num2cell(motionTrials') num2cell(motionCompleted') num2cell(motionAccuracy') num2cell(motionEfficiency')]];

            meanEfficiency = mean(pathEfficiency);
        end
    end
end