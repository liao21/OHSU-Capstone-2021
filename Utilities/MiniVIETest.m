classdef MiniVIETest < matlab.unittest.TestCase
    % Test Harness for MiniVIE
    % Usage:
    %     testCase = MiniVIETest;
    %     res = run(testCase)
    %
    % Revisions:
    % 20Apr2016 Armiger: Created
    methods (Test)
        function testSetup(testCase)
            UserConfig.getInstance('user_config.xml')
            obj = MiniVIE;
            set(obj.hg.Figure,'Name','MiniVIE-Test');
            obj.FilePrefix = UserConfig.getUserConfigVar('userFilePrefix','NEW_USER_');
            UiTools.save_temp_file('defaultFilePrefix',obj.FilePrefix)
            
            % Inputs
            obj.SignalSource = eval(UserConfig.getUserConfigVar('SignalSource','Inputs.SignalSimulator()'));
            obj.SignalSource.NumSamples = 4000;
            obj.SignalSource.initialize();
            
            % Enable buttons
            set(obj.hg.SignalSourceButtons(:),'Enable','on');
            % TODO lookup correct input number
            %set(obj.hg.popups(1),'Value',10);    % select the NFU input source
            set(obj.hg.popups(1),'Value',6);    % select the NFU input source
            
            % Setup filters and remaining properties
            cellFilterCreators = eval(UserConfig.getUserConfigVar('SignalFilters','{}'));
            for i = 1:length(cellFilterCreators)
                obj.println(sprintf('Creating Filter: %s',cellFilterCreators{i}),1);
                hFilter = eval(cellFilterCreators{i});
                obj.SignalSource.addfilter(hFilter);
            end
            
            % % h.addfilter(Inputs.Notch([120 240 360],5,1,Fs));
            % % h.addfilter(Inputs.Notch([120 240 360],64,1,1000));
            
            % f = GUIs.guiSignalViewer(h);
            % uiwait(f.hg.Figure);
            
            %% Signal Analysis
            obj.SignalClassifier = SignalAnalysis.Lda();
            
            % Enable Buttons
            set(obj.hg.SignalAnalysisButtons(:),'Enable','on');
            set(obj.hg.popups(2),'Value',2);
            
            obj.SignalClassifier.NumMajorityVotes = 3;
            
            NumSamplesPerWindow = 150;
            fprintf('Setting Window Size to: %d\n',NumSamplesPerWindow);
            obj.SignalClassifier.NumSamplesPerWindow = NumSamplesPerWindow;
            
            %obj.TrainingData = PatternRecognition.TrainingData();
            obj.TrainingData = TrainingDataAnalysis();
            %if ~obj.TrainingData.loadTrainingData([])
                % Initialize with defaults
                obj.TrainingData.initialize(obj.SignalSource.NumChannels,NumSamplesPerWindow);
            %end
            
            set(obj.hg.TrainingButtons(:),'Enable','on');
            
            % Initialize Classifier with data object
            obj.SignalClassifier.initialize(obj.TrainingData);
            
            % TODO: Note signals only updated on classifier
            % creation
            defaultChannels = 1:16;
            % defaultChannels = GUIs.guiChannelSelect.getLastChannels();
            if isempty(defaultChannels)
                msg = 'No channels are active.  Enable channels in Signal Viewer';
                errordlg(msg);
                error(msg);
            end
            obj.SignalClassifier.setActiveChannels(defaultChannels);
            
            classNames = GUIs.guiClassifierChannels.getSavedDefaults();
            if (isempty(classNames))
                classNames = GUIs.guiClassifierChannels.getDefaultNames;
            end
            obj.SignalClassifier.setClassNames(classNames);
            
            obj.SignalClassifier.train();
            obj.SignalClassifier.computeError();
            obj.SignalClassifier.computeGains();
            
            %% Setup Presentation
            obj.Presentation = eval(UserConfig.getUserConfigVar('Scenario','Scenarios.OnlineRetrainer'));
            obj.Presentation.JoystickId = 0;
            
            % Haptics need to be configured here, and in
            %obj.Presentation.EnableFeedback = 0;
            %obj.Presentation.EnableImpedance = 0;
            %obj.Presentation.TactorIds = [3 4];
            
            obj.Presentation.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
            obj.Presentation.Verbose = 0;
            obj.Presentation.update();
            obj.Presentation.update();
            
            obj.println('Presentation setup complete',1);
            
            % Enable buttons
            set(obj.hg.PresentationButtons(:),'Enable','on');
            set(obj.hg.popups(5),'Value',6);

            drawnow
            
            
            obj.Presentation.hGui.close()
%             obj.Presentation.close();
%             obj.Presentation.close();
%             obj.SignalSource.close();
            obj.close();
            delete(obj.hg.Figure)
        end
    end
end
