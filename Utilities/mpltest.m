function mpltest
% Test Script to test MPL functions with NFU

AA = -0.3;
EL = 0;
armTestStart = [[0 AA 0] EL 0 0 0];

fprintf('\n\n\n\n\n');
fprintf('******************************\n');
fprintf('********MiniVIE Tests*********\n');
fprintf('******************************\n');
fprintf('Which Test?\n');

% cellTests = { function callback, test description }
cellTests = {
    @Ping,         'Ping: Limb system and router using OS'
    @NfuStream01,  'NFU: Streaming [Inputs.NfuInput]'
    @MplWrist01,   'MPL Wrist: Range of motion [MPL.NfuUdp.getInstance MPL.MudCommandEncoder]'
    @MplHand,      'MPL Hand: ROC grasps [MPL.NfuUdp.getInstance MPL.MudCommandEncoder]'
    @Haptics01,    'Tactor: Manual control'
    @Haptics02,    'HapticAlgorithm: Runs HapticAlgorithm within  MPL.MplNfuScenario < Scenarios.ScenarioBase'
    @Joystick01,   'Joystick: Runs JoyMexClass preview for 15 seconds'
    @MplThumb,     'Test MPL Thumb'
    @Edit01,       'Edit: mpltest.m'
    };

% display options
nTests = size(cellTests,1);
testDescriptions = cellTests(:,2);
str = [ cellstr(num2str((1:nTests)')) testDescriptions]';
fprintf('[%s] %s\n',str{:})
fprintf('[0] Exit\n');

% get response
response = str2double(input('Select Test: ','s'));

if isnan(response) || (response == 0)
    % Exit
    return
end

% call function
testFunction = cellTests{response,1};
testFunction();

return

    function Ping
        MPL.MplUtils.wait_for_ping_response();
    end

    function NfuStream01
        h = Inputs.NfuInput();
        
        fprintf('Adding Filters\n');
        h.addfilter(Inputs.HighPass());
        h.addfilter(Inputs.Notch());
        h.NumSamples = 2000;
        s = h.initialize();
        assert(s >= 0,'NFU Init failed');
        
        GUIs.guiSignalViewer(h);
        
    end
    function MplWrist01
        %test mpl wrist ROM
        hNfu = MPL.NfuUdp.getInstance;
        s = hNfu.initialize();
        if s < 0
            error('NFU Init failed');
        end
        hNfu.ping(1);
        hNfu.sendAllJoints([ [0 AA 0] EL -0.7 -0.5 -0.5]);
        pause(1.0)
        AA = -0.25;
        hNfu.sendAllJoints([ [0 AA 0] EL+0.05 -0.7 -0.5 -0.5]);
        pause(1.0)
        hNfu.sendAllJoints([ [0 AA 0] EL 0.7 0.5 0.5]);
        pause(1.0)
        hNfu.sendAllJoints(armTestStart);
    end
    function MplWrist02
        %test mpl wrist ROM
        hNfu = MPL.NfuUdp.getInstance;
        s = hNfu.initialize();
        if s < 0
            error('NFU Init failed');
        end
        
        tic;
        while StartStopForm
            drawnow
            val = sin(toc);
            fprintf('Wrist Angle: %f\n',val);
            hNfu.sendAllJoints([zeros(1,4) val val val]);
            pause(0.02);
        end
    end
    function MplWrist03
        % this test runs the wrist doms through a 1 Hz sine wave.
        % It also activates the tactors on/off at 1 Hz
        
        %test mpl wrist ROM
        hNfu = MPL.NfuUdp.getInstance;
        assert(hNfu.initialize() >=0 ,'NFU Init Failed');
        
        tic;
        while StartStopForm
            drawnow
            
            % Wrist
            val = sin(toc);
            hNfu.sendAllJoints(armTestStart);
            
            % Tactors
            isOdd = @(x)rem(x,2);
            if isOdd(round(toc))
                tVal = 100;
            else
                tVal = 0;
            end
            
            tactorId = 3;
            hNfu.tactorControl(tactorId, 100, tVal, 100, 100, 0);
            tactorId = 4;
            hNfu.tactorControl(tactorId, 100, 100-tVal, 100, 100, 0);
            
            fprintf('Wrist Angle: %6.2f\t Tactor: %d\n',val,tVal);
            
            pause(0.02);  % control rate here
        end
        tactorId = 3;
        hNfu.tactorControl(tactorId, 100, 0, 100, 100, 0);
        tactorId = 4;
        hNfu.tactorControl(tactorId, 100, 0, 100, 100, 0);
        
    end
    function MplHand
        %test mpl hand Roc
        hNfu = MPL.NfuUdp.getInstance;
        hNfu.initialize();
        
        t = UserConfig.getUserConfigVar('rocTable','WrRocDefaults.xml');
        structRoc = MPL.RocTable.readRocTable(t);
        
        StartStopForm([]);
        while StartStopForm
            for iRoc = [3 5 6 8 16]%1:length(roc)
                RocId = structRoc(iRoc).id;
                RocName = structRoc(iRoc).name;
                
                numOpenSteps = 30;
                numWaitSteps = 10;
                numCloseSteps = 30;
                
                mplAngles = zeros(1,27);
                mplAngles(2) = -0.3;
                mplAngles(4) = EL+0.05; %Elbow
                
                graspVal = [linspace(0,1,numOpenSteps) ones(1,numWaitSteps) linspace(1,0,numCloseSteps)];
                for i = 1:length(graspVal)
                    fprintf('Entry #%d, RocId=%d, %14s %6.2f Pct\n',...
                        iRoc,RocId,RocName,graspVal(i)*100);
                    
                    % perform local interpolation
                    mplAngles(structRoc(iRoc).joints) = interp1(structRoc(iRoc).waypoint,structRoc(iRoc).angles,graspVal(i));
                    
                    hNfu.sendAllJoints(mplAngles);
                    pause(0.02);
                end
                disp('Wait...');pause(1);
            end
        end
        hNfu.sendAllJoints(armTestStart);
    end
    function Haptics01
        % Test tactors manually
        test_tactor_nfu();
        return
    end
    function Haptics02
        % HapticAlgorithm: Runs HapticAlgorithm within  MPL.MplScenarioMud < Scenarios.ScenarioBase
        tData = PatternRecognition.TrainingData;
        
        h = MPL.MplNfuScenario;
        h.initialize([],[],tData);
        h.Verbose = 0;
        h.EnableFeedback = 1;
        start(h.Timer);
        
        fprintf('Feedback Algorithm is running\n');
        
        return
    end
    function Joystick01
        obj = JoyMexClass;
        obj.preview;
    end
    function Edit01
        edit(mfilename);
        return
    end
    function Pnet01
        pnet('closeall');
        pause(0.1);
        p = pnet('tcpsocket',6200);
        pnet(p,'setreadtimeout',1);
        t = pnet(p,'tcplisten');
        if t < 0
            error('tcplisten failed: %d\n',t);
        else
            fprintf('tcplisten success: %d\n',t);
            pnet(t,'close');
            pnet(p,'close');
        end
    end
    function MplThumb
        hNfu = MPL.NfuUdp.getInstance;
        hNfu.initialize();
        
        id = MPL.EnumArm;
        armAngles = zeros(1,27);
        
        N = 10;
        maxVal = 0.9;
        StartStopForm([]);
        while StartStopForm
            for i = 27:-1:24
                for j = [linspace(0,maxVal,N) linspace(maxVal,0,N)]
                    armAngles(i) = j;
                    armAngles(id.INDEX_AB_AD) = -armAngles(id.INDEX_AB_AD);
                    fingerPositions(id.THUMB_CMC_AD_AB) = 2*fingerPositions(id.THUMB_CMC_AD_AB);
                    hNfu.sendAllJoints(armAngles);
                    pause(0.02)
                end
            end
        end
    end
end
