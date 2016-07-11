classdef MiniVIE < Common.MiniVieObj
    % Sample user interface demonstrating the MiniVIE API functionality.
    % The basic user interface allows selecting an input source, selecting
    % a classifier, and a presentiaton which displays limb commands in some
    % way.  Optional modules are the training interface and the plant
    % module which control data training interfaces and limb dynamics
    % respectively
    %
    % % First time setup creates a set of buttons on the shortcut menu
    % MiniVIE.createShortcuts()
    %
    % % Session startup (or use the shortcut button: "MiniVIE"
    % MiniVIE.configurePath()
    %
    % % Launch the UI:
    % obj = MiniVIE
    %
    
    properties
        SignalSource
        SignalClassifier
        TrainingInterface
        TrainingData
        Presentation
        
        FilePrefix
        
        hg;  % handle graphics
        
        Verbose = 1;
    end
    properties (Access = private)
        SignalViewer = [];
        
        TabTitleInput       = '   Input Source   ';
        TabTitleAnalysis    = '   Signal Analysis   ';
        TabTitleTrainer     = '   Training   ';
        TabTitleOutput      = '   Output Device   ';
    end
    methods
        function obj = MiniVIE
            % Creator
            % Sets up the environment and runs the MiniVIE default display
            obj.configurePath;
            obj.FilePrefix = UserConfig.getUserConfigVar('userFilePrefix','NEW_USER_');
            
            obj.initialize();
            
            % set figure name
            guiName = strcat(obj.FilePrefix,'MiniVIE');
            set(obj.hg.Figure,'Name',guiName);
            
        end
        function initialize(obj)
            setupFigure(obj);
            
            % Set valid input options
            set(obj.hg.popupInput,'String',{'None','Signal Simulator','EMG Simulator','DaqHwSession','DaqHwDevice','CpchSerial','NfuInput','UdpDevice','IntanDevBoard','OpenBCI','ThalmicLabs MyoUdp'});
            set(obj.hg.popupInput,'Value',1);
            set(obj.hg.popupAnalysis,'String',{'None','LDA Classifier','DiscriminantAnalysis','SupportVectorMachine','SvmStatTlbx'});
            set(obj.hg.popupAnalysis,'Value',1);
            set(obj.hg.popupTrainer,'String',{'None','Online Trainer','Simple Trainer','Mini Guitar Hero','Bar Trainer','Motion Trainer','vMPL Trainer'});
            set(obj.hg.popupTrainer,'Value',1);
            set(obj.hg.popupOutput,'String',{'None','MiniV','Breakout','AGH','MplVulcanX','MplNfu','MplUnity','MSMS_ADL','MSMS Tasks','Online Retraining Demo','Endpoint Controller'});
            set(obj.hg.popupOutput,'Value',1);
        end
        function setupFigure(obj)
            %%
            obj.hg.Figure = UiTools.create_figure('MiniVIE Configuration Utility','MiniVIE');
            set(obj.hg.Figure,'CloseRequestFcn',@(src,evnt)cbCloseFig(obj));
            
            obj.hg.Figure.Position = [1 1 1200 800];
            % change position
            movegui(obj.hg.Figure,'center');
            %movegui(obj.hg.Figure,'northeast');
            
            % Setup File Menu
            obj.hg.MenuFile = uimenu(obj.hg.Figure,...
                'Label','File');
            obj.hg.MenuFilePrefix = uimenu(obj.hg.MenuFile,...
                'Label','Set Filename Prefix...',...
                'Callback',@(src,evt)obj.setFilePrefix());
            obj.hg.MenuFileLoad = uimenu(obj.hg.MenuFile,...
                'Label','Load Training Data...',...
                'Callback',@(src,evt)obj.loadData());
            obj.hg.MenuFileSave = uimenu(obj.hg.MenuFile,...
                'Label','Save Training Data...',...
                'Callback',@(src,evt)obj.saveTrainingData());
            obj.hg.MenuTools = uimenu(obj.hg.Figure,...
                'Label','Tools');
            obj.hg.MenuToolsRocEdit = uimenu(obj.hg.MenuTools,...
                'Label','ROC Editor...',...
                'Callback', @(src,evt) cbRocEditor(obj) );
            obj.hg.MenuToolsMpl = uimenu(obj.hg.MenuTools,...
                'Label','MPL');
            obj.hg.MenuToolsMplImpedance = uimenu(obj.hg.MenuToolsMpl,...
                'Label','Enable Dynamic Impedance',...
                'Callback', @(src,evt) cbImpedance(obj) );
            obj.hg.MenuFileExportLdaParams = uimenu(obj.hg.MenuFile,...
                'Label','Save LDA Wg, Cg, and Classes to TextFile',...
                'Callback', @(src,evt)obj.saveTxt());
            obj.hg.MenuHelp = uimenu(obj.hg.Figure,...
                'Label','Help');
            obj.hg.MenuAbout = uimenu(obj.hg.MenuHelp,...
                'Label','About', ...
                'Callback', @(src,evt)obj.cbAbout());
            
            % add tabs
            obj.hg.TabGroup = uitabgroup('Parent', obj.hg.Figure);
            obj.hg.TabInput = uitab('Parent', obj.hg.TabGroup, 'Title', obj.TabTitleInput);
            obj.hg.TabAnalysis = uitab('Parent', obj.hg.TabGroup, 'Title', obj.TabTitleAnalysis);
            obj.hg.TabTrainer = uitab('Parent', obj.hg.TabGroup, 'Title', obj.TabTitleTrainer);
            obj.hg.TabOutput = uitab('Parent', obj.hg.TabGroup, 'Title', obj.TabTitleOutput);
            obj.hg.TabGroup.SelectionChangedFcn = @(src,evt)cbTabChanged(obj,src,evt);
            
            % Draw the body of the figure.
            
            % popup - Input Select
            obj.hg.TabInput.Units = 'pixels';
            p = obj.hg.TabInput.Position;
            obj.hg.popupInput = uicontrol(obj.hg.TabInput,...
                'Position',[20 p(4)-70 200 20],...
                'Style','popupmenu',...
                'String','None',...
                'FontSize',14,...
                'Callback',@(src,evt)setSignalSource(obj,src),...
                'Background','White');
            
            % draw input viewer panel
            pad = 20;
            obj.hg.SignalPanel = uipanel(obj.hg.TabInput,'Title','Signal Viewer','FontSize',12,...
                'Units','pixels',...
                'Position',[pad pad p(3)-pad-pad p(4)-pad-pad-70]);
            
            % popup - Signal Analysis Select
            obj.hg.TabAnalysis.Units = 'pixels';
            p = obj.hg.TabAnalysis.Position;
            obj.hg.popupAnalysis = uicontrol(obj.hg.TabAnalysis,...
                'Position',[20 p(4)-70 200 20],...
                'Style','popupmenu',...
                'String','None',...
                'FontSize',14,...
                'Callback',@(src,evt)setSignalAnalysis(obj,src),...
                'Background','White');
            
            % popup - Training Select
            obj.hg.TabTrainer.Units = 'pixels';
            p = obj.hg.TabTrainer.Position;
            obj.hg.popupTrainer = uicontrol(obj.hg.TabTrainer,...
                'Position',[20 p(4)-70 200 20],...
                'Style','popupmenu',...
                'String','None',...
                'FontSize',14,...
                'Callback',@(src,evt)setTrainer(obj,src),...
                'Background','White');
            
            % popup - Output Select
            obj.hg.TabOutput.Units = 'pixels';
            p = obj.hg.TabOutput.Position;
            obj.hg.popupOutput = uicontrol(obj.hg.TabOutput,...
                'Position',[20 p(4)-70 200 20],...
                'Style','popupmenu',...
                'String','None',...
                'FontSize',14,...
                'Callback',@(src,evt)setPresentation(obj,src),...
                'Background','White');
            
            % Create some pushbuttons for configuring each VIE object:
            
            % SignalAnalysisButtons
            obj.hg.SignalAnalysisButtons(1) = uicontrol(obj.hg.TabAnalysis,...
                'Position',pos('cntrl',1,3,1,1),...
                'Style','pushbutton',...
                'String','Select Classes',...
                'Enable','off',...
                'Callback',@(src,evt)obj.SignalClassifier.uiEnterClassNames);
            obj.hg.SignalAnalysisButtons(2) = uicontrol(obj.hg.TabAnalysis,...
                'Position',pos('cntrl',1,4,1,1),...
                'Style','pushbutton',...
                'String','Classifier Parameters',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbClassifierProperties);
            obj.hg.SignalAnalysisButtons(3) = uicontrol(obj.hg.TabAnalysis,...
                'Position',pos('cntrl',1,5,1,1),...
                'Style','pushbutton',...
                'String','Clear Training Data',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbTrainClear());
            obj.hg.SignalAnalysisButtons(4) = uicontrol(obj.hg.TabAnalysis,...
                'Position',pos('cntrl',1,6,1,1),...
                'Style','pushbutton',...
                'String','Train',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbTrain());
            obj.hg.SignalAnalysisButtons(5) = uicontrol(obj.hg.TabAnalysis,...
                'Position',pos('cntrl',1,7,1,1),...
                'Style','pushbutton',...
                'String','Plot PCA',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbPlotPca());
            obj.hg.SignalAnalysisButtons(6) = uicontrol(obj.hg.TabAnalysis,...
                'Position',pos('cntrl',1,8,1,1),...
                'Style','pushbutton',...
                'String','Plot Confusion Matrix',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbPlotConfusion());
            
            % TrainingButtons
            obj.hg.TrainingButtons(1) = uicontrol(obj.hg.TabTrainer,...
                'Position',pos('cntrl',1,3,1,1),...
                'Style','pushbutton',...
                'String','Begin Training',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbBeginTraining());
            
            % PresentationButtons
            obj.hg.PresentationButtons(1) = uicontrol(obj.hg.TabOutput,...
                'Position',pos('cntrl',1,3,1,1),...
                'Style','pushbutton',...
                'String','Adjust Gains',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbAdjustGains());
            obj.hg.PresentationButtons(2) = uicontrol(obj.hg.TabOutput,...
                'Position',pos('cntrl',1,4,1,1),...
                'Style','pushbutton',...
                'String','Adjust Limits',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbAdjustLimits());
            obj.hg.PresentationButtons(3) = uicontrol(obj.hg.TabOutput,...
                'Position',pos('cntrl',1,5,1,1),...
                'Style','pushbutton',...
                'String','Start',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbPresentationStart());
            obj.hg.PresentationButtons(4) = uicontrol(obj.hg.TabOutput,...
                'Position',pos('cntrl',1,6,1,1),...
                'Style','pushbutton',...
                'String','Stop',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbPresentationStop());
            obj.hg.PresentationButtons(5) = uicontrol(obj.hg.TabOutput,...
                'Position',pos('cntrl',1,7,1,1),...
                'Style','pushbutton',...
                'String','Assessment',...
                'Enable','off',...
                'Callback',@(src,evt)obj.pbAssessment());
            
            obj.hg.PlantButtons(1) = uicontrol(obj.hg.TabOutput,...
                'Position',pos('cntrl',1,8,1,1),...
                'Style','pushbutton',...
                'String','Complex Mode',...
                'Enable','on',...
                'Callback',@(src,evt)obj.pbSimpleMode());
            
        end
        function setFilePrefix(obj)
            
            filePrefix = obj.FilePrefix;
            
            % Use these defaults
            prompt={
                'Enter file prefix ( e.g. VIE_03_ ):',...
                };
            name='File Parameters';
            numlines=1;
            defaultanswer={filePrefix};
            answer = inputdlg(prompt,name,numlines,defaultanswer);
            
            if isempty(answer)
                return
            end
            
            assert(length(answer) == 1,'Expected 1 output');
            
            filePrefix = answer{1};
            
            obj.FilePrefix = filePrefix;
            
            guiName = strcat(obj.FilePrefix,'MiniVIE');
            set(obj.hg.Figure,'Name',guiName);
        end
        function loadData(obj)
            if isempty(obj.SignalSource)
                errordlg('Select an Input Source');
                return;
            elseif isempty(obj.SignalClassifier)
                errordlg('Select a Classifier');
                return;
            end
            
            assert(~isempty(obj.TrainingData),'Training Data module does not exist');
            
            success = obj.TrainingData.loadTrainingData;
            if ~success
                return
            end
            
            % TODO: restore majority votes and other classifier settings?
            %obj.SignalClassifier.NumMajorityVotes = 7;
            %obj.SignalClassifier.ActiveChannels = [1 2 3 4 5 6 7 8];
            
            %obj.SignalClassifier.TrainingData = obj.TrainingInterface.getFeatureData;
            %obj.SignalClassifier.TrainingDataLabels = obj.TrainingInterface.getClassLabels;
            %obj.SignalClassifier.TrainingEmg = obj.TrainingInterface.getEmgData;
            obj.SignalClassifier.train();
            obj.SignalClassifier.computeError();
            obj.SignalClassifier.computeGains();
            
        end
        function saveTrainingData(obj)
            % save the training data object.  should not require input
            % source
            
            % if isempty(obj.SignalSource)
            %     errordlg('Select an Input Source');
            %     return;
            % elseif isempty(obj.SignalClassifier)
            %     errordlg('Select a Classifier');
            %     return;
            % end
            
            assert(~isempty(obj.TrainingData),'Training Data module does not exist');
            
            % Get filename
            
            fullFilename = obj.ui_select_data_file('.trainingData');
            if ~isempty(fullFilename)
                obj.TrainingData.saveTrainingData(fullFilename);
            end
            
        end
        function saveTxt(obj)
            % save the LDA weights, centers, thresholds and TrainingData class names to text files
            
            assert(~isempty(obj.SignalClassifier),'Signal Classifier module does not exist');
            assert(~isempty(obj.TrainingData),'Training Data module does not exist');
            
            %strPythonDir = 'c:\git\MiniVIE\python';
            strPythonDir = fullfile(fileparts(which('MiniVIE')),'python');
            if obj.SignalClassifier.savePythonClassifierData(strPythonDir)
                fprintf('Classifier parameters saved to text files in directory: [');
                fprintf(' %s',strPythonDir);
                fprintf(' ]\n');
            else
                fprintf('There was a problem saving one or many python txt file(s).\n');
            end
        end
        
        function close(obj)
            
            try obj.SignalSource.close();end
            try obj.SignalClassifier.close();end
            try obj.TrainingInterface.close();end
            try obj.Presentation.close();end
            
        end
        function setSignalSource(obj,src)
            % Callback for selecting an input
            
            % Hold the last value in case of error, restore
            persistent lastValue
            if isempty(lastValue)
                lastValue = 1;
            end
            
            % Get callback properties
            string = get(src,'String');
            value = get(src,'Value');
            
            try
                % get existing source
                h = obj.SignalSource;
                % in there's an old one, try to close it
                if ~isempty(h)
                    try %#ok<TRYNC>
                        close(h);
                    end
                end
                
                % match the newly selected input
                switch string{value}
                    case 'Signal Simulator'
                        h = Inputs.SignalSimulator();
                        %Fs = h.SampleFrequency;
                        %h.addfilter(Inputs.Notch([60 120],4,8,Fs));
                        %h.addfilter(Inputs.HighPass(15,3,Fs));
                        %h.addfilter(Inputs.LowPass(400,8,Fs));
                        
                        % Always need the highpass for the 1.2 V offset
                        Fs = h.SampleFrequency;
                        h.addfilter(Inputs.HighPass(20,3,Fs));
                        
                    case 'EMG Simulator'
                        [FileName,PathName,FilterIndex] = uigetfile('emgPatternData.mat');
                        if FilterIndex == 0
                            % User Cancelled
                            fname = 'emgPatternData.mat';
                        else
                            fname = fullfile(PathName,FileName);
                        end
                        h = Inputs.EmgSimulator(fname);
                    case 'DaqHwSession'
                        h = loadDaqHwDevice('Session');
                        % Ref Hargove 2014 comparison of real-time controlability
                        Fs = h.SampleFrequency;                     % 1000 Hz
                        h.addfilter(Inputs.HighPass(20,3,Fs));      % 20Hz 3rd order butter
                        h.addfilter(Inputs.MinLimitFilter(0.2));    % min limit
                        h.addfilter(Inputs.ConstraintFilter(-5,5)); % range limit
                    case 'DaqHwDevice'
                        h = loadDaqHwDevice('Legacy');
                        % Ref Hargove 2014 comparison of real-time controlability
                        Fs = h.SampleFrequency;                     % 1000 Hz
                        h.addfilter(Inputs.HighPass(20,3,Fs));      % 20Hz 3rd order butter
                        h.addfilter(Inputs.MinLimitFilter(0.2));    % min limit
                        h.addfilter(Inputs.ConstraintFilter(-5,5)); % range limit
                    case 'UdpDevice'
                        h = Inputs.UdpDevice();
                    case 'CpchSerial'
                        h = loadCpchSerial();
                        % Ref Hargove 2014 comparison of real-time controlability
                        Fs = h.SampleFrequency;                     % 1000 Hz
                        h.addfilter(Inputs.HighPass(20,3,Fs));      % 20Hz 3rd order butter
                        h.addfilter(Inputs.MinLimitFilter(0.2));    % min limit
                        h.addfilter(Inputs.ConstraintFilter(-5,5)); % range limit
                    case 'NfuInput'
                        h = Inputs.NfuInput();
                        % Ref Hargove 2014 comparison of real-time controlability
                        Fs = h.SampleFrequency;                     % 1000 Hz
                        h.addfilter(Inputs.HighPass(20,3,Fs));      % 20Hz 3rd order butter
                        h.addfilter(Inputs.MinLimitFilter(0.2));    % min limit
                        h.addfilter(Inputs.ConstraintFilter(-5,5)); % range limit
                    case 'IntanDevBoard'
                        h = Inputs.IntanUdp.getInstance;
                        h.addfilter(Inputs.Notch([120 180 240 300 360],64,1,1000));
                        Fs = h.SampleFrequency;
                        %h.addfilter(Inputs.HighPass(10,8,Fs));
                        h.addfilter(Inputs.LowPass(400,8,Fs));
                    case 'OpenBCI'
                        h = Inputs.OpenBciChipKit('COM3');
                    case 'ThalmicLabs MyoUdp'
                        h = Inputs.MyoUdp.getInstance();
                    otherwise
                        % None
                        h = [];
                end
                
                if isempty(h)
                    % Disable viewer
                    obj.SignalSource = h;
                    
                    if ~isempty(obj.SignalViewer)
                        obj.SignalViewer.close()
                        obj.SignalViewer = [];
                    end
                    delete(obj.hg.SignalPanel.Children)
                    
                else
                    % Enable buttons
                    h.NumSamples = 2000;
                    h.initialize();
                    obj.SignalSource = h;
                    
                    pbSignalView(obj);
                end
                
            catch ME
                errordlg({'Error Initializing Input Device.',ME.message});
                set(src,'Value',lastValue);
                return
            end
            
            lastValue = value;
            
        end
        function setSignalAnalysis(obj,src)
            persistent lastValue
            if isempty(lastValue)
                lastValue = 1;
            end
            
            string = get(src,'String');
            value = get(src,'Value');
            
            try
                h = obj.SignalClassifier;
                
                if ~isempty(h)
                    try
                        close(h);
                    end
                end
                
                if isempty(obj.SignalSource)
                    errordlg('Select an Input Source');
                    set(src,'Value',lastValue);
                    return;
                end
                
                switch string{value}
                    case 'LDA Classifier'
                        h = SignalAnalysis.Lda();
                    case 'DiscriminantAnalysis'
                        h = SignalAnalysis.DiscriminantAnalysis();
                    case 'SupportVectorMachine'
                        h = SignalAnalysis.Svm();
                    case 'SvmStatTlbx'
                        h = SignalAnalysis.SvmStatTlbx();
                    otherwise
                        % None
                        h = [];
                end
                
                if isempty(h)
                    set(obj.hg.SignalAnalysisButtons(:),'Enable','off');
                else
                    set(obj.hg.SignalAnalysisButtons(:),'Enable','on');
                    
                    h.NumMajorityVotes = 0;
                    
                    NumSamplesPerWindow = 250;
                    fprintf('Setting Window Size to: %d\n',NumSamplesPerWindow);
                    h.NumSamplesPerWindow = NumSamplesPerWindow;
                    
                    if isempty(obj.TrainingData)
                        %obj.TrainingData = PatternRecognition.TrainingData();
                        obj.TrainingData = TrainingDataAnalysis();
                        obj.TrainingData.initialize(...
                            obj.SignalSource.NumChannels,...
                            h.NumSamplesPerWindow);
                    end
                    
                    h.initialize(obj.TrainingData);
                    
                    % TODO: Note signals only updated on classifier
                    % creation
                    defaultChannels = GUIs.guiChannelSelect.getLastChannels();
                    if isempty(defaultChannels)
                        msg = 'No channels are active.  Enable channels in Signal Viewer';
                        %errordlg(msg);
                        error(msg);
                    end
                    fprintf('Setting Active Channels to: [');
                    fprintf(' %d',defaultChannels);
                    fprintf(' ]\n');
                    h.setActiveChannels(defaultChannels);
                    
                    classNames = GUIs.guiClassifierChannels.getSavedDefaults();
                    if (isempty(classNames))
                        classNames = GUIs.guiClassifierChannels.getDefaultNames;
                    end
                    h.setClassNames(classNames);
                    
                    
                end
                
                obj.SignalClassifier = h;
                
            catch ME
                errordlg({'Error Initializing Signal Analysis.',ME.message});
                set(src,'Value',lastValue);
                rethrow(ME);
                return
            end
            
            obj.SignalClassifier = h;
            lastValue = value;
            
        end
        function setTrainer(obj,src)
            persistent lastValue
            if isempty(lastValue)
                lastValue = 1;
            end
            
            % Get callback properties
            string = get(src,'String');
            value = get(src,'Value');
            
            try
                h = obj.TrainingInterface;
                
                if ~isempty(h)
                    try
                        close(h);
                    end
                end
                
                switch string{value}
                    case 'Online Trainer'
                        hManager = PatternRecognition.TrainingManager(obj.SignalSource,obj,SignalAnalysis,obj.TrainingData);
                        
                        hInterface = PatternRecognition.JoystickTrainer();
                        hManager.attachInterface(hInterface);
                        hInterface.initialize(hManager);
                        
                        hInterface = PatternRecognition.GuiTrainer();
                        hManager.attachInterface(hInterface);
                        hInterface.initialize(hManager);

                        h = hManager;
                        
                    case 'Simple Trainer'
                        h = PatternRecognition.SimpleTrainer();
                        
                        QA = {
                            'Number of Repetitions:'          '2'
                            'Contraction Length (sec):'       '4'
                            'Delay Length (sec):'             '3'
                            'Startup Wait Time (sec)'         '5'
                            'Show images (y/n)?'              'Y'
                            };
                        name='Input for Training Interface';
                        numLines = 1;
                        numOutputs = size(QA,1);
                        prompt = QA(:,1);
                        defaultanswer = QA(:,2);
                        answer = inputdlg(prompt,name,numLines,defaultanswer);
                        if isempty(answer)
                            % User Cancelled
                        end
                        
                        assert(length(answer) == numOutputs,'Expected %d outputs',numOutputs);
                        vals = str2double(answer);
                        assert(~any(isnan(vals(1:4))),'Expected 4 numeric values');
                        
                        h.NumRepetitions = vals(1);
                        h.ContractionLengthSeconds = vals(2);
                        h.DelayLengthSeconds = vals(3);
                        h.StartupWaitTimeSeconds = vals(4);
                        h.EnablePictures = strcmpi(answer{5},'y');
                        
                    case 'Bar Trainer'
                        h = PatternRecognition.BarTrainer();
                    case 'Mini Guitar Hero'
                        h = PatternRecognition.MiniGuitarHero();
                    case 'Motion Trainer'
                        h = PatternRecognition.MotionTrainer();
                    case 'vMPL Trainer'
                        h = PatternRecognition.VMplTrainer();
                        QA = {
                            'Number of Repetitions:'          '3'
                            'Contraction Length (sec):'       '5'
                            'Rest Length (sec):'              '5'
                            };
                        name='Input for Training Interface';
                        numLines = 1;
                        numOutputs = size(QA,1);
                        prompt = QA(:,1);
                        defaultanswer = QA(:,2);
                        answer = inputdlg(prompt,name,numLines,defaultanswer);
                        if isempty(answer)
                            % User Cancelled
                        end
                        
                        assert(length(answer) == numOutputs,'Expected %d outputs',numOutputs);
                        vals = str2double(answer);
                        assert(~any(isnan(vals)),'Expected 3 numeric values');
                        
                        h.NumRepetitions = vals(1);
                        h.ContractionLengthSeconds = vals(2);
                        h.DelayLengthSeconds = vals(3);
                    otherwise
                        % None
                        h = [];
                end
                
                if isempty(h)
                    % Disable buttons
                    set(obj.hg.TrainingButtons(:),'Enable','off');
                else
                    % Enable buttons
                    set(obj.hg.TrainingButtons(:),'Enable','on');
                    if isempty(obj.SignalSource)
                        errordlg('Select an Input Source');
                        return;
                    elseif isempty(obj.SignalClassifier)
                        errordlg('Select a Classifier');
                        return;
                    end
                    
                    h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                end
                
            catch ME
                errordlg({'Error Initializing Training Interface.',ME.message});
                set(src,'Value',lastValue);
                return
            end
            
            obj.TrainingInterface = h;
            lastValue = value;
            
        end
        function setPresentation(obj,src)
            string = src.String;
            value = src.Value;
            try
                h = obj.Presentation;
                if ~isempty(h)
                    try
                        close(h);
                    end
                end
                
                switch string{value}
                    case 'MiniV'
                        obj.println('Setting up presentation...',1);
                        h = Scenarios.MiniVDisplayScenario;
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.update();
                        h.Verbose = 1;
                        obj.println('Presentation setup complete',1);
                    case 'MplNfu'
                        QA = {
                            'Enable Tactors (y/n)'                  'y'
                            'Tactor Ids ([5 6 7]):'                 '[3 4]'
                            };
                        name = 'MPL Control Interface';
                        numlines = 1;
                        prompt = QA(:,1);
                        defaultanswer = QA(:,2);
                        answer = inputdlg(prompt,name,numlines,defaultanswer);
                        if isempty(answer)
                            % User Cancelled
                            return
                        else
                            assert(length(answer) == 2,'Expected 2 outputs');
                        end
                        
                        obj.println('Setting up presentation...',1);
                        h = MPL.MplNfuScenario;
                        % get starting impedance state from GUI
                        h.EnableImpedance = strcmp(get(obj.hg.MenuToolsMpl,'Checked'),'on');
                        h.EnableFeedback = strncmpi(answer{1},'y',1);
                        h.TactorIds = str2num(answer{2}); % TODO: Validate
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.update();
                        h.Verbose = 0;
                        
                        obj.println('Presentation setup complete',1);
                    case 'MplVulcanX'
                        obj.println('Setting up presentation...',1);
                        h = MPL.MplVulcanX;
                        h.hSink.MplAddress = UserConfig.getUserConfigVar('mplVulcanXIpAddress','127.0.0.1');
                        h.hSink.MplCmdPort = str2double(UserConfig.getUserConfigVar('mplVulcanXCommandPort','9027'));
                        h.hSink.MplLocalPort = str2double(UserConfig.getUserConfigVar('mplVulcanXSensoryPort','9029'));
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.Verbose = 0;
                        obj.println('Presentation setup complete',1);
                    case 'MplUnity'
                        obj.println('Setting up presentation...',1);
                        h = MPL.MplUnity;
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.update();
                        h.Verbose = 0;
                        
                        obj.println('Presentation setup complete',1);
                    case 'Endpoint Controller'
                        obj.println('Setting up presentation...',1);
                        h = MPL.EndpointController;
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.update();
                        h.Verbose = 0;
                        
                        obj.println('Presentation setup complete',1);
                    case 'Breakout'
                        h = Presentation.MiniBreakout(obj.SignalSource,obj.SignalClassifier);
                    case 'AGH'
                        QA = {
                            'Output Device (mcc, nidaq, COM4):' 'mcc'
                            };
                        name = 'Air Guitar Hero';
                        numlines = 1;
                        prompt = QA(:,1);
                        defaultanswer = QA(:,2);
                        answer = inputdlg(prompt,name,numlines,defaultanswer);
                        if isempty(answer)
                            % User Cancelled
                            return
                        end
                        
                        obj.println('Setting up presentation...',1);
                        h = Presentation.AirGuitarHero.AirGuitarHeroEmg(obj.SignalSource,obj.SignalClassifier);
                        
                        h.initialize(answer{1});
                        
                    case 'MSMS_ADL'
                        h = Scenarios.MSMS_ADL.MsmsDisplayScenario(obj.SignalSource,obj.SignalClassifier);
                        
                        response = questdlg('Which Side?','Select Side','Left','Right','Left');
                        
                        switch response
                            case 'Left'
                                h.isLeftSide = 1;
                            case 'Right'
                                h.isLeftSide = 0;
                            otherwise
                                % User Cancelled
                                return
                        end
                        %isLeftSide = 1;   % <---- Use this parameter to select Left=1/Right=0
                        h.initialize();
                        
                    case 'MSMS Tasks'
                        h = Scenarios.MsmsTasks;
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.update();
                        h.Verbose = 0;
                    case 'Online Retraining Demo'
                        h = Scenarios.OnlineRetrainer;
                        h.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
                        h.update();
                        h.Verbose = 1;
                    otherwise
                        % None
                        h = [];
                end
                
                if isempty(h)
                    % Disable buttons
                    set(obj.hg.PresentationButtons(:),'Enable','off');
                else
                    % Enable buttons
                    set(obj.hg.PresentationButtons(:),'Enable','on');
                end
                
                if isa(h,'Scenarios.ScenarioBase')
                    % set simple mode where arm returns to home
                    simpleMode = get(obj.hg.PlantButtons(1),'Value');
                    h.ArmStateModel.ApplyReturnToHome = simpleMode;
                end
                
                obj.Presentation = h;
                
                drawnow
                
                if ~isempty(obj.Presentation)
                    obj.Presentation.start();
                end
                
            catch ME
                errordlg(ME.message);
                rethrow(ME);
            end
        end
        
        function println(obj,str,verboseLevel)
            if obj.Verbose >= verboseLevel
                fprintf('%s\n',str);
            end
        end
        function hViewer = getSignalViewer(obj)
            if isempty(obj.SignalViewer) || ~isvalid(obj.SignalViewer)
                obj.SignalViewer = [];
            end
            
            hViewer = obj.SignalViewer;
            
        end
        function fullFilename = ui_select_data_file(obj,extension)
            % Provides a save dialog with the default file set as the
            % current date and time with extention reflecting contents
            % extension = '.assessmentLog'
            
            % get save file from xml instead of object
            filePrefix = obj.FilePrefix;
            
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
    methods (Access = private)
        function pbSignalView(obj)
            
            obj.SignalViewer = GUIs.guiSignalViewer(obj.SignalSource,obj.hg.SignalPanel);
            
            % link the viewer with a classifier if it exists
            
            addlistener(obj.SignalViewer.hChannelSelect,'ValueChange',@(src,evt)update_channels);
            
            function update_channels
                % Propogate channel changes to the classifier
                if ~isempty(obj.SignalClassifier)
                    ch = obj.SignalViewer.hChannelSelect.SelectedChannels;
                    obj.SignalClassifier.setActiveChannels(ch);
                end
                
            end
            
        end
        function pbSignalAudio(obj)
            obj.SignalSource.audiopreview(1,1,200);
        end
        function pbBeginTraining(obj)
            
            if isempty(obj.SignalSource)
                errordlg('Select an Input Source');
                return;
            elseif isempty(obj.SignalClassifier)
                errordlg('Select a Classifier');
                return;
            elseif isempty(obj.TrainingInterface)
                errordlg('Select a Training Interface');
                return;
            end
            
            obj.TrainingInterface.collectdata();
            
            try
                while ~obj.TrainingInterface.IsComplete
                    % wait for training timer to complete
                    drawnow
                end
            end
            
            
            if isa(obj.TrainingInterface,'PatternRecognition.AdaptiveTrainingInterface')
                % If adaptive, no need to retrain
            else
                % else we need to train the classifier with the collected
                % data
                obj.SignalClassifier.train();
                obj.SignalClassifier.computeError();
                obj.SignalClassifier.computeConfusion();
                obj.SignalClassifier.computeGains();
            end
        end
        function pbClassifierProperties(obj)
            
            % Use these defaults
            prompt = {
                'Enter Majority Votes (e.g. 7):'
                };
            name = 'Classifier Parameters';
            numlines = 1;
            defaultanswer = {'7'};
            answer = inputdlg(prompt,name,numlines,defaultanswer);
            
            if isempty(answer)
                % user cancelled
                return
            end
            
            assert(length(answer) == 1,'Expected 1 output');
            convertedVal = str2double(answer{1});
            assert(~isnan(convertedVal),'Expected a number');
            
            obj.SignalClassifier.NumMajorityVotes = convertedVal;
            
        end
        function pbTrainClear(obj)
            obj.TrainingData.clearData();
        end
        function pbTrain(obj)
            if ~any(obj.TrainingData.getClassLabelCount)
                return
            end
            
            obj.SignalClassifier.train();
            obj.SignalClassifier.computeError();
            obj.SignalClassifier.computeConfusion();
            obj.SignalClassifier.computeGains();
        end
        function pbPlotPca(obj)
            % plot the principle components of the current training data
            GUIs.guiPlotPca(obj.TrainingData);
        end
        function pbPlotConfusion(obj)
            % plot confusion matrix
            obj.SignalClassifier.plotConfusion();
        end
        function pbAdjustGains(obj)
            % Launch the gain adjust GUI.  Stop refresh during figure
            % creation
            obj.Presentation.stop;
            GUIs.guiGainAdjust(obj.SignalClassifier)
            obj.Presentation.start;
        end
        function pbAdjustLimits(obj)
            h = GUIs.guiLimitsAdjust();
            h.attachModel( obj.Presentation.ArmStateModel );
            h.setupFigure();
        end
        function pbPresentationStart(obj)
            if ~isempty(obj.Presentation)
                start(obj.Presentation);
            end
        end
        function pbPresentationStop(obj)
            if ~isempty(obj.Presentation)
                stop(obj.Presentation);
            end
        end
        function pbSimpleMode(obj)
            h = obj.Presentation;
            if isa(h,'Scenarios.ScenarioBase')
                
                if h.ArmStateModel.ApplyReturnToHome
                    % In simple mode, change to complex
                    set(obj.hg.PlantButtons(1),'String','Complex Mode');
                    h.ArmStateModel.ApplyReturnToHome = 0;
                else
                    set(obj.hg.PlantButtons(1),'String','Simple Mode');
                    h.ArmStateModel.ApplyReturnToHome = 1;
                end
                
            end
        end
        function pbAssessment(obj)
            % Select which type of user assessment is to be performed
            q = questdlg('Select Assessment:','Assessment','TAC-1','TAC-3','MotionTester','TAC-1');
            switch q
                case 'TAC-1'
                    GUIs.guiTargetAchievementControl(obj.SignalSource,obj.SignalClassifier,...
                        obj.TrainingData,obj.FilePrefix);
                case 'TAC-3'
                    GUIs.guiTargetAchievementControlMulti(obj.SignalSource,obj.SignalClassifier,...
                        obj.TrainingData,obj.FilePrefix);
                case 'MotionTester'
                    guiClassifierAssessment(obj.SignalSource,obj.SignalClassifier,...
                        obj.TrainingData,obj.FilePrefix);
                otherwise
                    return
            end
        end
        % Callback (cb) functions
        function cbTabChanged(obj, ~, eventdata)
            
            if obj.Verbose
                fprintf('[%s.m] Disable %s\n', mfilename, eventdata.OldValue.Title)
                fprintf('[%s.m] Enable %s\n\n', mfilename, eventdata.NewValue.Title)
            end
            
            % If 'Signal Input' was the previous tab, disable refresh
            if strcmp(eventdata.OldValue.Title, obj.TabTitleInput) && ~isempty(obj.SignalViewer);
                stop(obj.SignalViewer.hTimer);
            end
            % If 'Signal Input' was the previous tab, disable refresh
            if strcmp(eventdata.NewValue.Title, obj.TabTitleInput) && ~isempty(obj.SignalViewer)
                start(obj.SignalViewer.hTimer);
            end
            
        end
        
        function cbRocEditor(obj)
            % Launch the ROC Editor.
            
            % Ensure that if a scenario exists that it is not running
            drawnow
            if ~isempty(obj.Presentation)
                obj.Presentation.stop();
                drawnow
            end
            
            % Open GUI
            rocTable = UserConfig.getUserConfigVar('rocTable','WrRocDefaults.xml');
            GUIs.guiRocEditor(rocTable);
        end
        function cbImpedance(obj)
            % Toggle the impedance property for the MPL/NFU
            
            % Toggle state
            oldState = strcmp(get(obj.hg.MenuToolsMplImpedance,'Checked'),'on');
            newState = ~oldState;
            
            if newState
                % Enable
                set(obj.hg.MenuToolsMplImpedance,'Checked','on');
            else
                % Disable
                set(obj.hg.MenuToolsMplImpedance,'Checked','off');
            end
            
            if isa(obj.Presentation,'MPL.MplNfuScenario')
                obj.Presentation.EnableImpedance = newState;
            end
            
        end
        function cbCloseFig(obj)
            try
                close(obj);
            catch ME
                fprintf(2,'Error closing objects:\n"%s"\n',ME.message);
            end
            delete(obj.hg.Figure);
        end
        function cbAbout(obj)
            %% Revision Information
            verMajor = 1;
            verMinor = 95;
            verDate = '10-JUL-2016';
            
            cellMsg = {
                'MiniVIE'
                'Mini Virtual Integration Environment'
                '    for prosthetic control'
                sprintf('Version %d.%d %s',verMajor,verMinor,verDate)
                };
            
            if obj.Verbose
                % print to console
                for i = 1:length(cellMsg)
                    fprintf('[%s.m] %s\n',mfilename,cellMsg{i});
                end
            end
            
            h = msgbox(cellMsg,'MiniVIE','modal');
            uiwait(h);
        end
        
    end
    methods (Static = true)
        function createShortcuts(suffix)
            % Create MiniVIE shortcuts
            % This function adds shortcuts for useful tools in working with
            % the VIE.  The includes going the desired path, running the GUI
            % and cleaning up the workspace
            
            if nargin < 1
                suffix = '';
            end
            
            MiniVIE.configurePath();
            
            iconDir = fullfile( ...
                matlabroot, ...
                'toolbox', ...
                'shared', ...
                'dastudio', ...
                'resources');
            
            shortcutUtils = com.mathworks.mlwidgets.shortcuts.ShortcutUtils;
            
            % shortcutUtils.addShortcutToBottom(label, callback, icon, ...
            %    category, editable);
            
            % goto MiniVIE
            % cd('C:\svn\myopen\MiniVIE');
            % MiniVIE.configurePath;
            cb = sprintf('cd(''%s'') \nMiniVIE.configurePath();',...
                fileparts(which('MiniVIE')));
            shortcutUtils.addShortcutToBottom(strcat('goto MiniVIE',suffix),cb,'','Shortcuts', 'true');
            
            % MiniVIE
            % cd('C:\git\MiniVIE');
            % MiniVIE.configurePath;
            % obj = MiniVIE;
            cb = sprintf('cd(''%s'') \nMiniVIE.configurePath \nobj = MiniVIE;',...
                fileparts(which('MiniVIE')));
            iconPath = fullfile(fileparts(which('MiniVIE')),'Deploy','MiniVIE_resources','MiniVIE Icon 24.jpg');
            shortcutUtils.addShortcutToBottom(strcat('MiniVIE',suffix),cb,iconPath,'Shortcuts', 'true');
            
            %cleanup
            % run('C:\svn\myopen\MiniVIE\Utilities\cleanup.m')
            cb = sprintf('run(''%s'');',which('cleanup'));
            iconPath = fullfile(iconDir,'TTE_delete.gif');
            shortcutUtils.addShortcutToBottom(strcat('cleanup',suffix),cb,iconPath,'Shortcuts', 'true');
            
            %mpltest
            % mpltest();
            cb = 'mpltest()';
            shortcutUtils.addShortcutToBottom(strcat('mpltest',suffix),cb,'','Shortcuts', 'true');
            
            %RunMpl
            % RunMpl();
            cb = 'obj = RunMpl()';
            shortcutUtils.addShortcutToBottom(strcat('RunMpl',suffix),cb,'','Shortcuts', 'true');
            
            %RunTakeHome
            % cd('C:\svn\myopen\MiniVIE');
            % MiniVIE.configurePath;
            % obj = RunTakeHome();
            
            %cb = sprintf('cd(''%s'');\nMiniVIE.configurePath();\nobj = RunTakeHome();',...
            %    fileparts(which('MiniVIE')));
            %shortcutUtils.addShortcutToBottom(strcat('RunTakeHome',suffix),cb,'','Shortcuts', 'true');
            
        end
        function configurePath
            pathName = fileparts(which('MiniVIE'));
            
            addpath(pathName);
            addpath([pathName filesep 'Utilities']);
            %addpath(fullfile(pathName,'GUIDE_GUIs'));
            
            % add folder and sub-directories:
            addpath(genpath(fullfile(pathName,'ThirdParty')));
            
            fprintf('[%s.m] Configured MiniVIE path at: %s\n', mfilename, pathName)
        end
        function obj = Default(dataFile)
            if nargin < 1
                dataFile = 'C:\MiniVIE_Users\RSA_Sandbox\myo_udp_debug\Sim_2_ROCs.trainingData';
            end
            
            MiniVIE.configurePath
            
            obj.SignalSource = Inputs.SignalSimulator();
            obj.SignalSource.addfilter(Inputs.HighPass(20,3,1000));
            %obj.SignalSource.addfilter(Inputs.LowPass());
            %obj.SignalSource.addfilter();
            obj.SignalSource.NumSamples = 2000;
            obj.SignalSource.initialize();
            
            obj.TrainingData = PatternRecognition.TrainingData;
            obj.TrainingData.loadTrainingData(dataFile);
            
            obj.SignalClassifier = SignalAnalysis.Lda();
            obj.SignalClassifier.initialize(obj.TrainingData);
            
            classNames = obj.TrainingData.ClassNames;
            if isempty(classNames)
                classNames = GUIs.guiClassifierChannels.getDefaultNames;
            end
            obj.SignalClassifier.setClassNames(classNames);
            
            defaultChannels = GUIs.guiChannelSelect.getLastChannels();
            fprintf('Setting Active Channels to: [');
            fprintf(' %d',defaultChannels);
            fprintf(' ]\n');
            obj.SignalClassifier.setActiveChannels(defaultChannels);
            
            obj.SignalClassifier.NumMajorityVotes = 0;
            
            NumSamplesPerWindow = 250;
            fprintf('Setting Window Size to: %d\n',NumSamplesPerWindow);
            obj.SignalClassifier.NumSamplesPerWindow = NumSamplesPerWindow;
            
            obj.SignalClassifier.train();
            
            obj.TrainingInterface = PatternRecognition.SimpleTrainer();
            obj.TrainingInterface.NumRepetitions = 3;
            obj.TrainingInterface.ContractionLengthSeconds = 2;
            obj.TrainingInterface.DelayLengthSeconds = 1;
            obj.TrainingInterface.initialize(...
                obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
            
            obj.Presentation = MPL.MplUnity;
            %obj.Presentation = Scenarios.OnlineRetrainer;
            obj.Presentation.initialize(obj.SignalSource,obj.SignalClassifier,obj.TrainingData);
        end
        function obj = go
            % Start the MINIVIE
            obj = MiniVIE;
        end
    end
end

function h = loadCpchSerial()
% Load a CpchSerial with default prompts

tempFileName = 'defaultCpchSerial';
cpchParams = UiTools.load_temp_file(tempFileName);
if isempty(cpchParams)
    defaultanswer={'COM14','FFFF','FFFF'};
else
    defaultanswer={
        cpchParams.SerialPort
        dec2hex(cpchParams.BioampMask)
        dec2hex(cpchParams.GPIMask)};
end
% Use these defaults
prompt={
    'Enter Serial Port Name (e.g. COM1):',...
    'Enter BioAmplifier Channel Mask (e.g. FFFF):',...
    'Enter GPIO Channel Mask (e.g. 0000):',...
    };
name='CPCH Parameters';
numlines=1;
%defaultanswer={'COM14','FFFF','FFFF'};
answer=inputdlg(prompt,name,numlines,defaultanswer);
assert(length(answer) == 3,'Expected 3 outputs');

cpchParams.SerialPort = answer{1};
cpchParams.BioampMask = uint16(hex2dec(answer{2}));
cpchParams.GPIMask = uint16(hex2dec(answer{3}));

h = Inputs.CpchSerial(cpchParams.SerialPort,cpchParams.BioampMask,cpchParams.GPIMask);

try
    h.initialize();
catch ME
    % clearing defaults
    UiTools.delete_temp_file(tempFileName);
    rethrow(ME);
end
UiTools.save_temp_file(tempFileName,cpchParams);

end

function h = loadDaqHwDevice(version)
% Load a dawHwDevice with default prompts

if nargin < 1
    version = 'Session';
end

tempFileName = 'defaultDaqHwDevice';
daqParams = UiTools.load_temp_file(tempFileName);
if isempty(daqParams)
    defaultanswer = {'mcc','0','0:15'};
else
    defaultanswer = {daqParams.Name,daqParams.Id,num2str(daqParams.channelIds)};
end

% Use these defaults
prompt={
    'Enter DAQ Board Name (e.g. mcc, ni):',...
    'Enter DAQ Board Id (e.g. 0, Dev1):',...
    'Enter DAQ Board Channel Ids (e.g. 0:7):',...
    };
name='DAQ Parameters';
numlines=1;
answer=inputdlg(prompt,name,numlines,defaultanswer);
assert(length(answer) == 3,'Expected 3 outputs');

daqParams.Name = answer{1};
daqParams.Id = answer{2};
daqParams.channelIds = str2num(answer{3}); %#ok<ST2NM>

if strcmp(version,'Legacy')
    h = Inputs.DaqHwDevice(daqParams.Name,daqParams.Id,daqParams.channelIds);
else
    h = Inputs.DaqHwSession(daqParams.Name,daqParams.Id,daqParams.channelIds);
end
try
    h.initialize();
catch ME
    % clearing defaults
    UiTools.delete_temp_file(tempFileName);
    rethrow(ME);
end

UiTools.save_temp_file(tempFileName,daqParams);

end

