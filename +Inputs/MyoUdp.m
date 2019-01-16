classdef MyoUdp < Inputs.SignalInput
    % Class for interfacing Thalmic Labs Myo Armband via pnet udp.  
    %
    % There are currently two UDP streaming protocols compatible with the
    % MiniVIE.  The first is the MyoUdp.exe executable which runs under
    % windows and allows streaming of only a single armband at 200Hz. In
    % order to have a second streaming armband, a virtual machine can be
    % used, mapping a second armband and dongle to the virtual environment,
    % and streaming to the host PC.
    % 
    % The second streaming interface uses the bluetooth low energy
    % streaming protocol released by Thalmic Labs.  Within the python
    % subfolder are tools to connect and stream multiple Myo armbands to
    % UDP using the device MAC address.  This can achieve 300Hz raw EMG
    % streaming rates
    %
    % Each streaming protocol streams the EMG, orientation, accelerometer,
    % and gyroscope data 
    %
    % On the matlab side, the getData command reads buffered UDP packets,
    % interpolated the EMG data up to the expected 1kHz and returns the
    % data.  The orientation, accelerometer, and gyroscope data are
    % currently returned as property values.  Future versions may make
    % these available as seperate channel data for pattern classification.
    %
    % MyoUdp.exe Data packet information:
    % Data packet size is 48 bytes.
    %     uchar values encoding:
    %     Bytes 0-7: int8 [8] emgSamples
    %     Bytes 8-23: float [4]  quaternion (rotation)
    %     Bytes 24-35: float [3] accelerometer data, in units of g
    %     Bytes 36-47: float [3] gyroscope data, in units of deg / s
    %
    % MyoUdp.py Data packet information:
    % Data packet size either 16 or 20 bytes.
    %     case 16
    %         % EMG Samples (8 channels 2 samples per packet)
    %         d = double(typecast(bytes,'int8'));
    %         emgData = reshape(d,8,2);
    %     case 20
    %         % IMU sample
    %         MYOHW_ORIENTATION_SCALE = 16384.0;
    %         MYOHW_ACCELEROMETER_SCALE = 2048.0;
    %         MYOHW_GYROSCOPE_SCALE = 16.0;
    %         dataInt16 = double(typecast(bytes,'int16'));
    %         orientation = dataInt16(1:4) ./ MYOHW_ORIENTATION_SCALE;
    %         accelerometer = dataInt16(5:7) ./ MYOHW_ACCELEROMETER_SCALE;
    %         gyroscope = dataInt16(8:10) ./ MYOHW_GYROSCOPE_SCALE;
    %
    % Known Limitations:
    % As stated above, the maximum data rate is 200-300Hz for the armband and
    % the data resolution is only 8-bits.  Also, the myo is set to timeout
    % after 30 seconds of no motion to conserve battery, this has been
    % disabled in the python version. Shaking the device will wake it and
    % resume streaming.  Currently only one myo can stream at a time,
    % unless using a virtual machine as described above.
    %
    % MiniVIE software
    %
    %     % Test usage:
    %     MiniVIE.configurePath
    %     obj = Inputs.MyoUdp.getInstance;
    %     obj.initialize();
    %     hViewer = GUIs.guiSignalViewer(obj);
    %
    % Installation Notes
    %
    % The MyoUdp class will launch a helper program MyoUdp.exe based on the
    % Myo Armband SDK for streaming EMG data.  This executable requires the
    % Microsoft Visual Studio 2013 Redistributable Package.  If it is not
    % installed, you may get an error about missing DLL files.
    % http://www.microsoft.com/en-us/download/confirmation.aspx?id=40784
    %
    %
    % Revisions:
    %   1/27/2015 Armiger: Initial revision for streaming EMG
    %   2/24/2015 Armiger: Updated .exe to include orientation data
    %   7/01/2015 Armiger: Added support for dual streaming armbands (2
    %                      computers)
    %   5/09/2016 Armiger: Updated documentation
    properties
        
        EMG_GAIN = 0.01;  %Scaling from int8 to voltage
        
        InputFrequency; % Hz
    end
    properties (SetAccess = private)
        IsInitialized = 0;
        UdpSocket8;
        UdpSocket16;

        % Note the streaming ports are read in the user_config.xml file on
        % initialize
        UdpPortNum8 = 10001;     % stream port for channels 1-8
        UdpPortNum16 = 10002;    % stream port for channels 9-16
        
        Buffer
        numPacketsReceived = 0;
        numValidPackets = 0;
        
        Orientation = [1 0 0 0];    % Unit Quaternion [1 x 4]
        Accelerometer = [0 0 0];    % X,Y,Z Acceleration, (g) [1 x 3]
        Gyroscope = [0 0 0];        % X,Y,Z Angular Rate, (deg/s) [1 x 3]
        
        SecondMyo           % property for second myo motion data
    end
    methods (Access = private)
        function obj = MyoUdp
            obj.Verbose = 0;
        end
    end
    methods
        %initialize(obj);
        function [ status ] = initialize(obj)
            % Initialize network interface to NFU.
            % [ status ] = initialize(obj)
            %
            % status = 0: no error
            % status < 0: Failed
            
            % Note, true sample rate is 200 Hz, but this is upsampled to
            % 100Hz for compatability
            obj.SampleFrequency = 1000; % Hz
            obj.InputFrequency = str2double(UserConfig.getUserConfigVar('myoUdpRate','200'));
            obj.ChannelIds = 1:16;
            
            status = 0;
            
            if obj.IsInitialized
                fprintf('[%s] UDP Comms already initialized\n',mfilename);
                return
            end
            
            % Open a udp port to receive streaming data on
            obj.UdpPortNum8 = str2double(UserConfig.getUserConfigVar('myoUdpPort1',num2str(obj.UdpPortNum8)));
            obj.UdpPortNum16 = str2double(UserConfig.getUserConfigVar('myoUdpPort2',num2str(obj.UdpPortNum16)));
            obj.UdpSocket8 = PnetClass(obj.UdpPortNum8);
            obj.UdpSocket16 = PnetClass(obj.UdpPortNum16);
            if ~obj.UdpSocket8.initialize()
                fprintf(2,'[%s] Failed to initialize udp socket\n',mfilename);
                status = -1;
                obj.IsInitialized = false;
                return
            elseif (obj.UdpSocket8.hSocket ~= 0)
                fprintf(2,'[%s] Expected receive socket id == 0, got socket id == %d\n',mfilename,obj.UdpSocket8.hSocket);
            end
            if ~obj.UdpSocket16.initialize()
                fprintf(2,'[%s] Failed to initialize udp socket\n',mfilename);
                status = -1;
                obj.IsInitialized = false;
                return
            end
            
            % check for data:
            [~, numReads] = obj.UdpSocket8.getAllData(1e6);
            if numReads > 0
                fprintf('[%s] UDP Data Stream 1-8 Detected\n', mfilename);
            else
                fprintf('[%s] UDP Data Stream 1-8 NOT Detected\n', mfilename);
                
                % f = fullfile(fileparts(which('MiniVIE')),'+Inputs','MyoUdp.exe');
                % fprintf('[%s] UDP Data Stream NOT Detected\n', mfilename);
                % 
                % reply = questdlg({'UDP Data not detected.' ...
                %     'Launch MyoUdp.exe to begin streaming?'...
                %     '(Ensure that Myo Armband is connected before proceeding)'},...
                %     'Launch MyoUdp.exe','OK','Cancel','OK');
                % if strcmp(reply,'OK')
                %     fprintf('[%s] Launching %s\n', mfilename, f);
                %     system(strcat(f,' &'));
                % end
            end
            [~, numReads] = obj.UdpSocket16.getAllData(1e6);
            if numReads > 0
                fprintf('[%s] UDP Data Stream 9-16 Detected\n', mfilename);
            else
                fprintf('[%s] UDP Data Stream 9-16 NOT Detected\n', mfilename);
            end
            
            % data is [numSamples x numChannels]
            obj.Buffer = Common.DataBuffer(5000,obj.NumChannels);
            
            obj.IsInitialized = true;
            
        end
        function data = getData(obj,numSamples,idxChannel)
            %data = getData(obj,numSamples,idxChannel)
            % get data from buffer.  most recent sample will be at (end)
            % position.
            % dataBuffer = [NumSamples by NumChannels];
            %
            % optional arguments:
            %   numSamples, the number of samples requested from getData
            %   idxChannel, an index into the desired channels.  E.g. get the
            %   first four channels with iChannel = 1:4
            
            if nargin < 2
                numSamples = obj.NumSamples;
            end
            
            if nargin < 3
                idxChannel = 1:obj.NumChannels;
            end

            if isempty(obj.Buffer)
                obj.IsInitialized = false;
                error('Signal Buffer is not initialized')
            end

            obj.update();
            
            
            if obj.UdpPortNum8 == 15001 || obj.UdpPortNum8 == 15002 || ...
                    obj.UdpPortNum8 == 15003 || obj.UdpPortNum8 == 15004
                % get upsampled data
                desiredRate = 1000;
                %actualRate = 200;
                actualRate = obj.InputFrequency;
                %TODO: evaluate actual frequency with tic/toc and round to nearest 50
                upsampleFactor = desiredRate/actualRate;
                samples = round(numSamples/upsampleFactor);
                buffData = obj.Buffer.getData(samples,idxChannel);
                data = interp1(buffData,linspace(1,samples,numSamples));
            else
                % get data directly
                data = obj.Buffer.getData(numSamples,idxChannel);
            end
        end
        function update(obj)
            if obj.UdpPortNum8 == 15001 || obj.UdpPortNum8 == 15002 || ...
                    obj.UdpPortNum8 == 15003 || obj.UdpPortNum8 == 15004
                [cellDataBytes, numReads] = obj.UdpSocket8.getAllData(100);
                for i = 1:numReads
                    bytes = cellDataBytes{i};
                    switch length(bytes)
                        case 1
                            fprintf('[%s] %s Port 15001 Battery Value: %d\n',mfilename,datestr(now),bytes)
                        case 16
                            % EMG Samples (2 per packet)
                            d = double(typecast(bytes,'int8'));
                            emgData = reshape(d,8,2);
                            obj.Buffer.addData(obj.EMG_GAIN .* emgData',1:8);
                            obj.numPacketsReceived = obj.numPacketsReceived + 1;
                        case 20
                            % IMU sample
                            MYOHW_ORIENTATION_SCALE = 16384.0;
                            MYOHW_ACCELEROMETER_SCALE = 2048.0;
                            MYOHW_GYROSCOPE_SCALE = 16.0;
                            dataInt16 = double(typecast(bytes,'int16'));
                            
                            orientation = dataInt16(1:4) ./ MYOHW_ORIENTATION_SCALE;
                            accelerometer = dataInt16(5:7) ./ MYOHW_ACCELEROMETER_SCALE;
                            gyroscope = dataInt16(8:10) ./ MYOHW_GYROSCOPE_SCALE;
                            
                            % Ensure output is in row vectors, type double
                            obj.Orientation = orientation(:)';
                            obj.Accelerometer = accelerometer(:)';
                            obj.Gyroscope = gyroscope(:)';
                            
                        otherwise
                            warning('Unknown packet received')
                    end
                end
                [cellDataBytes, numReads] = obj.UdpSocket16.getAllData(100);
                for i = 1:numReads
                    bytes = cellDataBytes{i};
                    switch length(bytes)
                        case 1
                            fprintf('[%s] %s Port 15002 Battery Value: %d\n',mfilename,datestr(now),bytes)
                        case 16
                            % EMG Samples (2 per packet)
                            d = double(typecast(bytes,'int8'));
                            emgData = reshape(d,8,2);
                            obj.Buffer.addData(obj.EMG_GAIN .* emgData',9:16);
                        case 20
                            % IMU sample
                            MYOHW_ORIENTATION_SCALE = 16384.0;
                            MYOHW_ACCELEROMETER_SCALE = 2048.0;
                            MYOHW_GYROSCOPE_SCALE = 16.0;
                            dataInt16 = double(typecast(bytes,'int16'));
                            
                            orientation = dataInt16(1:4) ./ MYOHW_ORIENTATION_SCALE;
                            accelerometer = dataInt16(5:7) ./ MYOHW_ACCELEROMETER_SCALE;
                            gyroscope = dataInt16(8:10) ./ MYOHW_GYROSCOPE_SCALE;
                            
                            % Ensure output is in row vectors, type double
                            obj.SecondMyo.Orientation = orientation(:)';
                            obj.SecondMyo.Accelerometer = accelerometer(:)';
                            obj.SecondMyo.Gyroscope = gyroscope(:)';
                            
                        otherwise
                            warning('Unknown packet received')
                    end
                end
                
                return
            end
            
            % Update function reads any buffered udp packets and stores
            % them for later use.
            
            maxRead = 1e6; % max number of buffered UDP packets to read
            
            % read udp for channels 1-8
            [cellDataBytes, numReads] = obj.UdpSocket8.getAllData(maxRead);
            if numReads > 0
                % convert data bytes
                [emgData,angle,accel,gyro,quat,nValidPackets] = obj.convertPackets(cellDataBytes);
                if nValidPackets == 0
                    disp('Invalid Packets for channels 1-8');
                    return
                end
                
                % Display Output
                if obj.Verbose > 0
                    fprintf('angle: [%6.1f %6.1f %6.1f]; accel: [%6.2f %6.2f %6.2f]; gyro: [%8.1f %8.1f %8.1f] \n',...
                        angle(1,end),angle(2,end),angle(3,end),...
                        accel(1,end),accel(2,end),accel(3,end),...
                        gyro(1,end),gyro(2,end),gyro(3,end) );
                end
                
                % update object
                obj.Orientation = quat(:,end);
                obj.Accelerometer = accel(:,end);
                obj.Gyroscope = gyro(:,end);
                
                % Ensure output is in row vectors, type double
                obj.Orientation = double(obj.Orientation(:)');
                obj.Accelerometer = double(obj.Accelerometer(:)');
                obj.Gyroscope = double(obj.Gyroscope(:)');
                
                obj.Buffer.addData(obj.EMG_GAIN .* emgData,1:8);
            end
            
            
            % read udp for channels 9-16
            [cellDataBytes, numReads] = obj.UdpSocket16.getAllData(maxRead);
            if numReads > 0
                % convert data bytes
                [emgData,angle,accel,gyro,quat,nValidPackets] = obj.convertPackets(cellDataBytes);
                if nValidPackets == 0
                    disp('Invalid Packets for channels 9-16');
                    return
                end
                
                % gather second myo motion data
                
                % update object
                obj.SecondMyo.Orientation = quat(:,end);
                obj.SecondMyo.Accelerometer = accel(:,end);
                obj.SecondMyo.Gyroscope = gyro(:,end);
                
                % Ensure output is in row vectors, type double
                obj.SecondMyo.Orientation = double(obj.SecondMyo.Orientation(:)');
                obj.SecondMyo.Accelerometer = double(obj.SecondMyo.Accelerometer(:)');
                obj.SecondMyo.Gyroscope = double(obj.SecondMyo.Gyroscope(:)');
                
                obj.Buffer.addData(obj.EMG_GAIN .* emgData,9:16);
            end
        end
        function Rxyz = getEulerAngles(obj)
            Rxyz = LinAlg.decompose_R(getRotationMatrix(obj));
        end
        function [R, R2] = getRotationMatrix(obj)
            % get orientation as [3x3] rotation matrix.  Convert native
            % quaterion to matrix, but then do post processing to ensure it
            % is orthogonal.
            % 
            % If a second myo is attached then the second output argument
            % can be used to query the [3x3] rotation matirx of that device
            
            q = obj.Orientation;
            R = LinAlg.quaternionToRMatrix(q(:));
            [U, ~, V] = svd(R);
            R = U*V'; % Square up the rotation matrix
            
            if nargout > 1
                % get matrix for second myo
                q2 = obj.SecondMyo.Orientation;
                R2 = LinAlg.quaternionToRMatrix(q2(:));
                [U2, ~, V2] = svd(R2);
                R2 = U2*V2'; % Square up the rotaiton matrix
            end
        end
        function isReady = isReady(obj,numSamples) % Consider removing extra arg
            isReady = 1;
        end
        function start(obj)
        end
        function stop(obj)
        end
        function close(obj)
            Inputs.MyoUdp.getInstance(-1);
        end
        
    end
    methods (Static)
        function a = TestDongleless
            %%
            a = Inputs.MyoUdp.getInstance()
            a.UdpPortNum8 = 15001;
            a.UdpPortNum16 = 15002;
            a.initialize
            %%
            a.getData
            %%
            
            GUIs.guiSignalViewer(a)
            
            
        end
        function obj = MeasureRate(obj)
            % check the rate at which streaming EMG data is received
            
            if nargin < 1
                obj = Inputs.MyoUdp.getInstance();
            end
            %%
            tLast = clock;
            pLast = 0;
            StartStopForm([])
            while StartStopForm
                drawnow
                obj.update();
                
                tNow = clock;
                tElapsed = etime(tNow,tLast);
                if tElapsed > 2
                    pCount = obj.numPacketsReceived;
                    disp((pCount - pLast)/tElapsed)
                    tLast = tNow;
                    pLast = pCount;
                end
            end
            
            
        end
        
        function obj = DebugLatency(obj)
            % check the rate at which streaming EMG data is received
            
            pnet('closeall')
            h1 = PnetClass(15001);
            h2 = PnetClass(15002);
            h1.initialize()
            h2.initialize()
            
            %%
            StartStopForm([])
            while StartStopForm
                drawnow
                pause(0.1)
                [cellDataBytes, numReads] = h2.getAllData(5000);
                id = cellfun(@length,cellDataBytes) == 16;
                d = double(typecast([cellDataBytes{id}],'int8'));
                emgData1 = reshape(d,8,[]);
                [cellDataBytes, numReads] = h1.getAllData(5000);
                id = cellfun(@length,cellDataBytes) == 16;
                d = double(typecast([cellDataBytes{id}],'int8'));
                emgData2 = reshape(d,8,[]);
                subplot(2,1,1)
                plot(emgData1')
                ylim([-127 127])
                subplot(2,1,2)
                plot(emgData2')
                ylim([-127 127])
            end
            
            
        end
        
        function [obj, hViewer] = Default
            % [obj hViewer] = Default
            % Test usage:
            obj = Inputs.MyoUdp.getInstance;
            obj.UdpPortNum8 = 15001
            obj.UdpPortNum16 = 15002
            obj.initialize();
            hViewer = GUIs.guiSignalViewer(obj);
        end
        function Simulator
            % Demo the compact version of pnet wrapped into a class.  This can be run
            % across two matlab sessions or within it's own session
            pnet('closeall')
            
            %% Setup Sender (Session 2)
            hUdpHostSend = PnetClass(4096,10001,'127.0.0.1');
            [success, msg] = hUdpHostSend.initialize();
            
            %% Send (Session 2)
            i = 1;
            while StartStopForm
                i = mod(i+1,255);
                %hUdpHostSend.putData(char(rand(1,12)*255));
                hUdpHostSend.putData(char(i*ones(1,12)));
                pause(eps)
            end
        end
        function [emgData, xyz, accel, gyro, quat, nValidPackets] = convertPackets(cellDataBytes)
            % Read buffered udp packets and return results
            
            % default outputs
            [emgData, xyz, accel, gyro, quat] = deal([]);
            
            % compute number of valid packets
            packetSize = 48;
            %cellDataBytes
            isCorrectSize = cellfun(@length,cellDataBytes) == packetSize;
            nValidPackets = sum(isCorrectSize);
            
            if nValidPackets == 0
                % no new data, nothing to do
                return
            end
            
            % convert 2d array: [newPackets by numElements]
            orderedBytes = reshape([cellDataBytes{isCorrectSize}],packetSize,[]);
            
            nValidPackets = size(orderedBytes,2);
            
            % convert EMG samples first (bytes 0..7)
            emgBytes = orderedBytes(1:8,:);
            
            % convert uchar to int8 to double
            emgSamples = double(emgBytes);
            emgSamples(emgSamples > 127) = emgSamples(emgSamples > 127) - 255;
            
            if isempty(emgSamples) && sum(~isCorrectSize) > 0
                fprintf('[%s] Unexpected Packet Size Received\n',mfilename);
            end
            
            % perform upsample
            upsampleFactor = 5;
            
            %interp sampled
            if nValidPackets > 1
                emgData = interp1(emgSamples',linspace(1,nValidPackets,nValidPackets*upsampleFactor-upsampleFactor+1));
            else
                % can't interpolate
                emgData = repmat(emgSamples,[1 5])';
                %disp('Cannot Interpolate')
            end
            
            try
                % convert Orientation data (bytes 9..48)
                motionBytes = orderedBytes(9:48,:);  % single bytes
                singleData = reshape( typecast(motionBytes(:),'single'), 10, []);
                
                % onOrientationData provides its current orientation, which is
                % represented as a unit quaternion.
                quat = singleData(1:4,:);
                % onAccelerometerDataprovides the accelerometer data of myo, in
                % units of g.
                accel = singleData(5:7,:);
                % onGyroscopeData provides the gyroscope data of myo, in units
                % of deg / s.
                gyro = singleData(8:10,:);
                
                % Convert quaternion to rotation matrix
                % This could fail if all zeros are sent as quaternion
                % data
                R = repmat(eye(3),[1 1 nValidPackets]);
                for i = 1:nValidPackets
                    try
                        % renormalize quaternion in case of rounding errors
                        normQ = quat(:,i) ./ norm(quat(:,i));
                        % convert to rotation matrix
                        R(:,:,i) = LinAlg.quaternionToRMatrix(normQ);
                    catch ME
                        warning(ME.message);
                    end
                end
                % Convert to Euler angles
                xyz = LinAlg.decompose_R(R);
                
            catch ME
                disp(mfilename);
                disp('Caught an error');
                disp(ME.message)
                keyboard
            end
            
        end
        function singleObj = getInstance(cmd)
            persistent localObj
            if nargin < 1
                cmd = 0;
            end
            
            if cmd < 0
                fprintf('[%s] Deleting Udp comms object\n',mfilename);
                try
                    localObj.UdpSocket8.close();
                end
                try
                    localObj.UdpSocket16.close();
                end
                %IsInitialized
                localObj = [];
                return
            end
            
            if isempty(localObj) || ~isvalid(localObj)
                fprintf('[%s] Calling constructor\n',mfilename);
                localObj = Inputs.MyoUdp;
            else
                fprintf('[%s] Returning existing object\n',mfilename);
            end
            singleObj = localObj;
        end
    end
end









% %%%%%%%%%%%%%%%
% % Myo Udp Connection Debug Notes
% %%%%%%%%%%%%%%%
% % The commands below show the basic process of opening, running, and
% % closing the udp based commands at 3 levels of abstraction:
% % first is the device level: a Myo Udp receiver
% % Next is at the Pnet Class level
% % finally at the pnet direct interface level
% 
% %% Test Device Level
% obj = Inputs.MyoUdp.getInstance();
% status = obj.initialize();
% if status < 0
%     error('pnet setup failed')
% end
% 
% obj.getData();
% 
% %%
% 
% obj.preview()
% 
% %%
% 
% obj.close()
% 
% Inputs.MyoUdp.getInstance(-1)
% 
% 
% 
% %% Test PnetClass
% obj = PnetClass(15001);
% obj.initialize()
% obj.getData()
% pause(0.1)
% obj.getData()
% 
% %%
% obj.close()
% 
% 
% 
% %%%%%%%%%%%%
% %% Test Single pnet Socket
% fprintf('\n\n\n\n\n\n')
% hSocket = pnet('udpsocket',15001)
% pnet(hSocket, 'setreadtimeout',0)
% status = pnet(hSocket,'status')
% len = pnet(hSocket,'readpacket','noblock')
% pause(0.1)
% count = -1;
% len = 1;
% while (len > 0)
%     len = pnet(hSocket,'readpacket','noblock');
%     count = count + 1;
% end
% count
% pnet(hSocket,'close')
% 
% 
% 
% %% Test Multiple pnet sockets
% fprintf('\n\n\n\n\n\n')
% hSocket2 = pnet('udpsocket',15002)
% hSocket3 = pnet('udpsocket',15003)
% hSocket = pnet('udpsocket',15001)
% pnet(hSocket, 'setreadtimeout',0)
% status = pnet(hSocket,'status')
% len = pnet(hSocket,'readpacket','noblock')
% pause(0.1)
% count = -1;
% len = 1;
% while (len > 0)
%     len = pnet(hSocket,'readpacket','noblock');
%     count = count + 1;
% end
% count
% pnet(hSocket,'close')
% 
