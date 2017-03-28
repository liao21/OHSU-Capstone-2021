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
            
            if isfield(structTrialLog,'AllClassNames')
                % new version
                sLog = structTrialLog;
            else
                
                % % old file format.  abort process
                % [completionAccuracy, motionAccuracy] = deal(nan);
                % hAxes = [];
                % return
                
                % try to work similar data from old file types
                classIdToTest = 1:length(structTrialLog);
                classNames = {structTrialLog(:).targetClass};
                if all(cellfun(@isempty,strfind(classNames,'No Movement')))
                    % Append No Movement if it's not there
                    classNames{end+1} = 'No Movement';
                end
                version = 'V1';
                
                sLog.AllClassNames = classNames;
                sLog.ClassIdToTest = classIdToTest;
                sLog.Data = structTrialLog;
                
            end
            
            numClasses = length(sLog.AllClassNames);
            testedClasses = sLog.AllClassNames(unique(sLog.ClassIdToTest));
            
            % Updated to account for repeat tests. Confusion matrix should
            % be based on all repeats, but success rate must be calculated
            % on a per-repeat basis.
            
            confuseMatOverall = zeros(numClasses);
            completed = zeros(length(sLog.Data), 1);
            for iClass = 1:length(sLog.Data)
                testClassId = sLog.ClassIdToTest(iClass);
                row = accumarray(sLog.Data(iClass).classDecision(:),1,[numClasses 1])';
                confuseMatOverall(testClassId,:) = confuseMatOverall(testClassId,:) + row;
                % Now need to calculate completionAccuracy on a per trial basis
                if isfield(sLog, 'MaxCorrect') % Newer versions
                    if row(testClassId) == sLog.MaxCorrect
                       completed(iClass) = 1; 
                    end
                    
                else 
                    if row(testClassId) == 10
                       completed(iClass) = 1; 
                    end
                end
            end
            
            reducedMatOverall = confuseMatOverall(unique(sLog.ClassIdToTest), unique(sLog.ClassIdToTest));
            
            % plot
            PlotUtils.confusionMatrix(reducedMatOverall,testedClasses,hAxes)
            
            % compute confusion as percentage
            % Compute the total number of examples
            classSum = sum(reducedMatOverall,2);
            % Normalize based on the number of examples
            normMat = reducedMatOverall ./ repmat(classSum,1,size(reducedMatOverall,1));
            % should not occur, but if divided by zero, set to zero
            normMat(isnan(normMat)) = 0;
            motionAccuracy = mean(diag(normMat)) .* 100;

            completionAccuracy = sum(completed) ./ length(completed) .* 100;

            
        end
        function [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = parseTac(structTrialLog)
            % [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = DataAnalysis.Assessments.parseTac1(structTrialLog)
            % Parse the TAC 1 trial data.  return the scalar accuracy of
            % number of successful trials, as well as cell array tables of
            % the summary statistics and tiral history
            
            % Catch for python TAC struct or hdf5 file
            if ischar(structTrialLog)
                if any(strfind(structTrialLog, 'hdf5'))
                    [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = DataAnalysis.Assessments.parseTacPython(structTrialLog);
                    return
                end
            end
            if isfield(structTrialLog, 'completion_time')
                [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = DataAnalysis.Assessments.parseTacPython(structTrialLog);
                return
            end
            
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
        function [completionAccuracy, cellSummary, cellHistory, meanEfficiency] = parseTacPython(hdf5)
            % Parse the TAC 1 trial data.  return the scalar accuracy of
            % number of successful trials, as well as cell array tables of
            % the summary statistics and tiral history
            if ischar(hdf5)
               structTrialLog = DataAnalysis.ParsePythonData.getTACLog(hdf5);
            elseif isstruct(hdf5)
                structTrialLog = hdf5;
            else
                error('hdf5 input should either be hdf5 file or struct log generated by Assessments.ParsePythonData.getTACLog()');
            end

            % get the number of completions over the total trials
            moveComplete = [structTrialLog.move_complete];  % Empty ones will not show up in completion time
            completionAccuracy = sum(moveComplete) ./ length(moveComplete) .* 100;
                        
            % Compute path efficiency for each trial
            nTrials = length(structTrialLog); 
            nJoints = length(structTrialLog(1).target_joint);
            pathEfficiency = nan(nTrials,nJoints); % Uncomment for separate efficiencies for each joint in TAC3
            %pathEfficiency = nan(nTrials,1);
            
            % Early versions had time on second axis instead of first, so
            % handle that
            [lenDim1, lenDim2] = size(structTrialLog(1).time_history);
            if lenDim1 == 1
                transposeFlag = 1;
            else
                transposeFlag = 0;
            end
            
            for i = 1:nTrials
                t = structTrialLog(i);

                % perfect path efficiency is each incremental motion (diff)
                % sums to exactly the angle difference.  deviations from
                % path will add to the user length
                if transposeFlag
                    posDiff = t.target_position - t.position_time_history(:,1);
                    idJoint = find(posDiff ~= 0);
                    posHist = t.position_time_history(idJoint,:);
                    posDiff = posDiff';
                    posHist = posHist';
                else
                    posDiff = t.target_position - t.position_time_history(1,:);
                    idJoint = find(posDiff ~= 0);
                    posHist = t.position_time_history(:,idJoint);
                end
                
                minDist = abs(posDiff(idJoint));
                
                % user dist only calculated if move was completed
                userDist = sum(abs(diff(posHist)), 1) .* t.move_complete;
                pathEfficiency(i,:) = minDist ./ userDist * 100; % Uncomment for separate efficiencies for each joint in TAC3
                %pathEfficiency(i) = mean(minDist ./ userDist * 100);
            end

            % zero score for incomplete moves
            pathEfficiency(isinf(pathEfficiency)) = 0;
            
            % it is possible for user path efficiency to be greater that
            % 100% since with the error bands on the target the trial can
            % complete without fully making it to the final value
            pathEfficiency(pathEfficiency > 100) = 100;            
            
            % Compute summary stats by grouping classes
            allTrials = cell(1, nTrials);
            for i = 1:nTrials
               %allTrials{i}(isletter(allTrials{i})==0) = [];
               allTrials{i} = strjoin(structTrialLog(i).target_joint, '-'); 
            end
            testedClasses = unique(allTrials);
            nUnique = length(testedClasses);
            motionTrials = nan(1,nUnique);
            motionCompleted = nan(1,nUnique);
            motionEfficiency = nan(nJoints,nUnique);  % Uncomment for separate efficiencies
            %motionEfficiency = nan(1,nUnique);
            for i = 1:nUnique
                thisClass = strcmp(testedClasses(i),allTrials);
                motionCompleted(i) = sum(thisClass & moveComplete);
                motionTrials(i) = sum(thisClass);
                motionEfficiency(:,i) = mean(pathEfficiency(thisClass, :), 1);  % Uncomment for separate efficiencies
                %motionEfficiency(i) = mean(pathEfficiency(thisClass));
            end
            motionAccuracy = motionCompleted ./ motionTrials * 100;
            
            % Compute elapsed time
            elapsedTime = nan(nTrials,1);
            for i = 1:nTrials
               elapsedTime(i) = structTrialLog(i).time_history(end); 
            end
            
            % print by trial
            switch nJoints
                case 1  % TAC1
                    cellHistory = [{'Class Name' 'Elapsed Time' 'Completed' 'Path Efficiency'}; ...
                        allTrials' num2cell(elapsedTime) num2cell([structTrialLog.move_complete]') num2cell(pathEfficiency)];

                    % print summary
                    cellSummary = [{'Class Name' 'Num Trials' 'Num Completed' 'Mean Completion' 'Mean Efficiency'}; ...
                        [testedClasses' num2cell(motionTrials') num2cell(motionCompleted') num2cell(motionAccuracy') num2cell(motionEfficiency')]];

                    meanEfficiency = mean(pathEfficiency);
                case 3 % TAC3
                    cellHistory = [{'Class Name' 'Elapsed Time' 'Completed' 'Path Efficiency (Joint 1)' 'Path Efficiency (Joint 2)' 'Path Efficiency (Joint 3)'}; ...
                        allTrials' num2cell(elapsedTime) num2cell([structTrialLog.move_complete]') num2cell(pathEfficiency)];

                    % print summary
                    cellSummary = [{'Class Name' 'Num Trials' 'Num Completed' 'Mean Completion' 'Mean Efficiency (Joint 1)' 'Mean Efficiency (Joint 2)' 'Mean Efficiency (Joint 3)'}; ...
                        [testedClasses' num2cell(motionTrials') num2cell(motionCompleted') num2cell(motionAccuracy') num2cell(motionEfficiency')]];

                    meanEfficiency = mean(pathEfficiency, 1);
            end
        end
    end
end