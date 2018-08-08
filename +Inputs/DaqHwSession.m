classdef DaqHwSession < Inputs.SignalInput
    % Class for interfacing data acquisition hardware via the matlab data
    % acquisition toolbox with new session based interface
    % Sample Usage:
    %     hSignalSource = Inputs.DaqHwDevice('mcc','0');
    %     hSignalSource.addfilter(Inputs.HighPass());
    %     hSignalSource.addfilter(Inputs.LowPass());
    %     hSignalSource.addfilter(Inputs.Notch());
    %     hSignalSource.NumSamples = 2000;
    %     hSignalSource.initialize();
    %     hSignalSource.preview(1:4)    
    %
    % 26-Feb-2016 Armiger: Created

    % Example Session:
    % chIds = [0:7];
    % nChannels = length(chIds);
    % dev = daq.getDevices
    % vendors = daq.getVendors
    % s = daq.createSession(vendors.ID)
    % s.addAnalogInputChannel(dev.ID,chIds,'Voltage')
    % for i = 1:length(chIds)
    %     s.Channels(i).InputType = 'SingleEnded';
    % end
    % %s.addlistener
    % s.IsContinuous = 1;
    % s.Rate = 1000;
    % % s.DurationInSeconds = 0.2
    % lh = addlistener(s,'DataAvailable', @(src,event)plot(event.TimeStamps, event.Data)); 
    % 
    % startBackground(s)
    
    properties
        DaqDeviceName = 'mcc';  % Default is Measurement Computing
        DaqDeviceId = '0';
        ChannelInputRange = [-10 10]; % Volts
    end
    properties (SetAccess = private)
        AnalogInput = [];
        AnalogInputName = '';
        Buffer
        IsInitialized = false;
    end
    methods
        function obj = DaqHwSession(deviceName,deviceId,channelIds)
            % DaqHwSession(deviceName,deviceId,channelIds)
            % Constructor
            %
            % Inputs:
            %   deviceName  - vendor of daq device. e.g. 'ni'
            %   deviceId    - device identifier.  e.g. 'Dev1'
            %   channelIds  - list of zero based channel ids e.g. 0:7
            %
            % Returns handle to object
            if nargin > 0
                obj.DaqDeviceName = deviceName;
            end
            if nargin > 1
                obj.DaqDeviceId = deviceId;
            end
            if nargin > 2
                obj.ChannelIds = channelIds;
            else
                obj.ChannelIds = 0:7;
            end
            
        end
        function initialize(obj)
            % obj.initialize()
            % Setup the daq with the requisite channels. This sets the
            % channels to single ended, specifies the range, and starts the
            % background session (which updates an internal buffer with new
            % data)
            
            if obj.IsInitialized
                disp('Device already initialized. Use close() first')
                return
            end

            % Check properties
            assert(ischar(obj.DaqDeviceName),'Expected "DaqDeviceName" to be a character array');
            assert(ischar(obj.DaqDeviceId),'Expected "DaqDeviceId" to be a character array');

            % Init rolling buffer
            obj.Buffer = Common.DataBuffer(5000,obj.NumChannels);
            
            if obj.Verbose
                fprintf('[%s] Setting up hardware "%s"...',mfilename,obj.DaqDeviceName);
            end

            % verify that adaptor family is installed
            vendors = daq.getVendors;
            vendorList = {vendors(:).ID};
            assert(ismember(obj.DaqDeviceName,vendorList),'Vendor %s is not found',obj.DaqDeviceName);

            dev = daq.getDevices;
            devList = {dev(:).ID};
            assert(ismember(obj.DaqDeviceId,devList),'Device %s is not found',obj.DaqDeviceId);

            s = daq.createSession(obj.DaqDeviceName);

            % Create analog input voltage channels
            nChannels = length(obj.ChannelIds);
            for i = 1:nChannels
                ch = s.addAnalogInputChannel(obj.DaqDeviceId,obj.ChannelIds(i),'Voltage');
                %ch.InputType = 'SingleEnded';
                ch.Range = obj.ChannelInputRange;
                ch.TerminalConfig = 'SingleEnded';
            end
            s.IsContinuous = 1;
            s.Rate = 1000;
            
            % New data will be added to rolling buffer
            addlistener(s,'DataAvailable', ...
                @(src,event)obj.Buffer.addData(event.Data,1:nChannels));

            obj.AnalogInput = s;
            startBackground(s)

            if obj.Verbose
                fprintf('Done\n');
            end
            
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
            %
            %
            % This function will always return the correct size for data
            % (based on the number of samples) however results will be
            % padded with zeros.  User should check obj.AnalogInput.SamplesAvailable
            % for a deterministic result
            
            if nargin < 3
                idxChannel = 1:obj.NumChannels;
            end
            
            if nargin < 2
                numSamples = obj.NumSamples;
            end
            
            if isempty(obj.AnalogInput)
                error('DAQ Object "%s" Not Initialized\n',obj.AnalogInputName);
            end
            
            data = obj.Buffer.getData(numSamples,idxChannel);

        end
        function isReady = isReady(obj,varargin)
            % ensure daq device is ready with the right number of samples
            obj.startBackground(s);
            
            isReady = 1;
        end
        function start(obj)
            % start running device data refresh in background
            startBackground(obj.AnalogInput)
        end
        function stop(obj)
            % halt background data refresh 
            stop(obj.AnalogInput);
        end
        function close(obj)
            % cleanup
            stop(obj);
            delete(obj.AnalogInput);
            obj.AnalogInput = [];
            obj.IsInitialized = 0;

        end
    end
end


