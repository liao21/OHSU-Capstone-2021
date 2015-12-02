classdef (Sealed) NfuUdp < handle
    % Class for interfacing JHU/APL NFU via pnet.
    % Note instances are limited so use NfuUdp.getInstance
    %
    % This handles streaming of all data types (cpch, percepts, etc.)
    %
    % Usage:
    % hNfu = MPL.NfuUdp.getInstance;
    % hNfu.initialize();
    %
    % hNfu.setParam(NFU_run_algorithm,0)  %% 0 implies algorithm runs on laptop
    % hNfu.setParam(NFU_output_to_MPL,2)  %% 2 = NFU CAN to limb
    %
    % Note data streams start in the initialize function
    %
    %
    % NFU Message IDs:
    %   59 - Arm position and hand ROC
    %   60 - Tactor command
    %   61 - All joints position
    %   62 - All joints impedance
    %
    % Note: cellData = get_buffer(obj,id) currently uses two methods for
    % percepts and for EMG data.  one with flipud and one without.  Needs
    % to be investigated further
    properties
        
        % /fs/etfs/telem_port defaults to 9027
        % /fs/etfs/cmd_port defaults to 6200
        % /fs/etfs/cmd_udp_port defaults to 6201
        
        Hostname % info pulled from xml config file.  See .getInstance method
        UdpStreamReceivePortNumLocal% = 9027
        TcpPortNum% = 6200;
        UdpCommandPortNumLocal% = 52000;  % This is where udp commands originate locally
        UdpCommandPortNumRemote% = 6201;  % This is where udp commands are sent to
        
        EnableDataLogging = 0;
        
        CpchDataBuffer
        
        UdpBuffer1
        UdpBuffer2
        UdpBuffer3
        UdpBuffer4
        
        AllowImpedance = 1; % Controls whether commands are sent in impedance or position mode
        
        hLogFile
        
        busVoltageWarn = 22; %V
        
        hideHeartbeat = 0;  % disable echoing hearbeat to console
        
        DefaultStiffnessCmd = [25.0*ones(1,7) 1.5*ones(1,20)]; % 16 Nm/rad Upper Arm  0.1-1 Hand
        
        Verbose = 1;
    end
    properties (SetAccess = private)
        hMud = MPL.MudCommandEncoder();
        IsInitialized = false;
        
        TcpConnection = [];
        TcpSocket = [];
        UdpStreamReceiveSocket = [];
        UdpCommandSocket = [];
        
        LmcPosition = [];
        LmcTorque = [];
        
        BufferSize = 100;
        
        newData1
        newData2
        newData3
        newData4
        
        ptr1
        ptr2
        ptr3
        ptr4
        
        sum1
        sum2
        sum3
        sum4
        
        numPacketsReceived = 0;
        
    end
    properties (Constant = true)
        nfuStates = {
            'SW_STATE_INIT'                     %0
            'SW_STATE_PRG'                      %1
            'SW_STATE_FS'                       %2
            'SW_STATE_NOS_CONTROL_STIMULATION'  %3
            'SW_STATE_NOS_IDLE'                 %4
            'SW_STATE_NOS_SLEEP'                %5
            'SW_STATE_NOS_CONFIGURATION'        %6
            'SW_STATE_NOS_HOMING'               %7
            'SW_STATE_NOS_DATA_ACQUISITION'     %8
            'SW_STATE_NOS_DIAGNOSTICS'          %9
            'SW_STATE_NUM_STATES'               %10
            };
    end
    methods (Access = private)
        function obj = NfuUdp
            % Creator is private to force singleton
            reset_buffers(obj);
        end
    end
    methods
        function [ status ] = initialize(obj)
            % INITIALIZE - Initialize network interface to NFU.
            % [ status ] = initialize(obj)
            %
            % status = 0: no error
            % status < 0: Failed
            
            status = 0;
            
            if obj.IsInitialized
                fprintf('[%s] NFU Comms already initialized\n',mfilename);
                
                % 7/7/2014 RSA: Resend limb and stream enable commands on initialization
                % this is applicable if the limb is reset / power cycled to allow matlab
                % to reestablish communications
                fprintf('[%s] Enabling NFU Percepts Data Stream\n',mfilename);
                obj.enableStreaming(5);
                pause(0.1);
                obj.update();
                pause(0.1);
                obj.enableRunMode;
                
                return
            end
            
            % Open a udp port to receive streaming data on
            obj.UdpStreamReceiveSocket = PnetClass(obj.UdpStreamReceivePortNumLocal);
            if ~obj.UdpStreamReceiveSocket.initialize()
                % Error case
                fprintf(2,'[%s] Failed to initialize udp socket\n',mfilename);
                status = -1;
                return
            elseif (obj.UdpStreamReceiveSocket.hSocket ~= 0)
                % Warning / unexpected case
                fprintf(2,'[%s] Expected receive socket id == 0, got socket id == %d\n',mfilename,obj.UdpStreamReceiveSocket.hSocket);
            end
            
            % Open a udp port to send commands
            obj.UdpCommandSocket = PnetClass(obj.UdpCommandPortNumLocal);
            
            if ~obj.UdpCommandSocket.initialize
                status = -2;
                return
            elseif (obj.UdpCommandSocket.hSocket ~= 1)
                fprintf(2,'[%s] Expected receive socket id == 1, got socket id == %d\n',mfilename,obj.UdpCommandSocket.hSocket);
            end
            
            % StartStreams
            
            % Switch out case for combined EMG + Percept streams (reduces
            % NFU restarts)
            multiStream = 0;
            if multiStream
                % Enable CPCH Data
                fprintf('[%s] Enabling CPCH Data Stream\n',mfilename);
                obj.enableStreaming(1);
                % 1/28/2012 RSA, KDK observed cpc stream did not start without
                % delay between messages
                pause(0.1);
                
                %                 % Enable Percepts
                %                 fprintf('[%s] Enabling Percepts Data Stream\n',mfilename);
                %                 obj.enableStreaming(4);
            else
                % Enable Percepts
                
                % 4/14/2014 RSA, KDK, MSJ observed streaming did not start
                % with 'combined' message (5).  Only streaming with single
                % CPCH message group...
                
                fprintf('[%s] Enabling NFU Percepts Data Stream\n',mfilename);
                obj.enableStreaming(5);
                pause(0.1);
            end
            % Test a few updates since these have been problematic
            obj.update();
            pause(0.1);
            obj.update();
            pause(0.1);
            obj.update();
            pause(0.1);
            
            obj.IsInitialized = true;
            
            obj.enableRunMode;
            
        end
        function [ status, result ] = ping(obj,isBlocking)
            % PING - Check limb system comms using system OS ping command
            %
            % argument "isBlocking", if true, will block until a successful
            % ping is received (default)
            %
            % returns status = 0 and, in result, the ping output string.
            % If "ping" fails or does not exist on your system, system
            % returns a nonzero value in status, and an explanatory message
            % in result.
            %
            % Note, the command status is checked for a valid response
            % string the the system status variable may be 0 (success) even
            % if the destinatino host is unreachable
            %
            % 07AUG2015 Armiger: Created
            
            if nargin < 2
                isBlocking = true; %default
            end
            
            ip = obj.Hostname;
            
            if ispc
                % windows format
                strPing = sprintf('ping %s -n 1',ip);
            else
                % unix (mac) format
                strPing = sprintf('ping %s -c 1',ip);
            end
            
            if obj.Verbose
                fprintf('[%s] Trying to ping %s...\n',mfilename,obj.Hostname);
            end
            
            status = 1;
            while status
                
                % Execute system ping command: status == 0 is good, otherwise 1 if bad
                [~,result] = system(strPing);
                
                % Note this case returns success even though the ping failed
                %
                % Pinging 192.168.1.111 with 32 bytes of data:
                % Reply from 192.168.1.200: Destination host unreachable.
                %
                % Ping statistics for 192.168.1.111:
                %     Packets: Sent = 1, Received = 1, Lost = 0 (0% loss)
                
                % Look for these strings in the response to determine success
                if ispc
                    % windows format
                    strSuccess = sprintf('Reply from %s: bytes=32',ip);
                else
                    % unix format
                    %strSuccess = '1 packets transmitted, 1 received';
                    
                    % TODO: unix / mac response is untested
                    disp(result)
                    error('Untested ping response output');
                end
                
                status = isempty( strfind(result,strSuccess) );
                
                if obj.Verbose
                    if status
                        fprintf('[%s] Ping Failed\n',mfilename);
                    else
                        fprintf('[%s] Ping Success\n',mfilename)
                    end
                end
                
                if ~isBlocking
                    break;
                end
            end % while
            
        end
        function enableRunMode(obj)
            
            % get handle to database
            db = Db.MplDb.getInstance();
            
            %NFU_run_algorithm = evalin('base','NFU_run_algorithm');
            NFU_run_algorithm = db.get_parameter('NFU_run_algorithm');
            obj.setParam(NFU_run_algorithm,0)  %% 0 implies algorithm runs on laptop
            db.set_value('NFU_run_algorithm',single(0))  %% 0 implies algorithm runs on laptop
            
            pause(0.2);
            
            %NFU_output_to_MPL = evalin('base','NFU_output_to_MPL');
            val = 2;
            NFU_output_to_MPL = db.get_parameter('NFU_output_to_MPL');
            obj.setParam(NFU_output_to_MPL,val)  %% 2 = NFU CAN to limb
            db.set_value('NFU_output_to_MPL',single(val))  %% 2 = NFU CAN to limb
            
        end
        function sendAllJoints(obj,jointAngles,stiffnessCmd)
            % SENDALLJOINTS - Generate command for all joints and send UDP
            %
            % Inputs:
            %
            %   jointAngles - 27x1 array of all arm joint angles in radians
            %                 joint angle enumeration given in
            %                 mpl_upper_arm_enum (1-7) Arm
            %                 MudCommandEncoder (1-20) Hand
            %   stiffnessCmd - 27x1 array of arm stiffness commands in
            %                 Nm/rad.  Typical upper arm values are 3-15 Nm/rad
            %                 and Hand stiffnesses are approximately 0.1-1
            %                 Nm/rad
            %
            % Usage:
            %   sendAllJoints(obj,jointAngles) - Send jointAngles using
            %                 default stiffness.  If jointAngles is a 7x1
            %                 array, then commands aply to the upper arm
            %                 only and the hand angles are commanded to 0
            %                 by default.  If jointAngles is a 27x1 then
            %                 all joints are commanded
            %   sendAllJoints(obj,jointAngles,stiffnessCmd) - Send
            %                 jointAngles and stiffness for all joints.  If
            %                 jointAngles is a 7x1
            %                 array, then commands aply to the upper arm
            %                 only and the hand angles are commanded to 0
            %                 by default.  If jointAngles is a 27x1 then
            %                 all joints are commanded
            
            if nargin < 3
                % use default impedance
                stiffnessCmd = obj.DefaultStiffnessCmd;
            end
            
            if isempty(obj.LmcPosition)
                warning('NfuUdp:sendAllJoints','LMC Positions are unknown');
            elseif any(abs(obj.LmcPosition(:) - reshape(jointAngles(1:7),7,1)) > 0.1)
                % h = warndlg({'Limb is about to make a fast move'...
                %     sprintf('%6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f (Start)',obj.LmcPosition(:)),...
                %     sprintf('%6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f (End)',reshape(jointAngles(1:7),7,1))},...
                %     'Fast Move','modal');
                % uiwait(h);
            end
            
            
            % create position array and assign inputs
            p = zeros(27,1);
            if length(jointAngles) == 7
                p(1:7) = jointAngles;
                p(8:27) = 0;
            elseif length(jointAngles) == 27
                p = jointAngles(:);
            else
                error('Wrong size for Joint Angles');
            end
            
            % create MUD command
            msg = obj.hMud.AllJointsPosVelImpCmd(p(1:7),zeros(1,7),p(8:27),zeros(1,20),stiffnessCmd);
            
            % append nfu message ID (for impedance)
            if obj.AllowImpedance
                msg = [uint8(62);msg(:)];
            else
                msg = [uint8(61);msg(:)];
            end
            
            % send the UDP command
            obj.sendUdpCommand(msg);
            
        end
        
        function sendUdpCommand(obj,msg)
            % SENDUDPCOMMAND - All messages send to the NFU via UDP come
            % through this function.
            %
            % Inputs:
            %       msg - encoded bytes for transmission to NFU.  Byte
            %             encoding is based on MUD command encoder, however
            %             an additional NFU message ID byte is required as
            %             the first element
            %
            % Usage:
            %       sendUdpCommand(obj,msg)
            %               send a udp message to the command socket
            %
            % NFU Message IDs:
            %   59 - Arm position and hand ROC
            %   60 - Tactor command
            %   61 - All joints position
            %   62 - All joints impedance
            
            obj.UdpCommandSocket.putData(uint8(msg),...
                obj.Hostname, obj.UdpCommandPortNumRemote);
        end
        function enableStreaming(obj,type)
            if nargin < 2
                type = 1;
            end
            
            % With wireless, multiple streams are ok
            [ msg ] = obj.msg_enable_streaming( type );
            
            sendUdpCommand(obj,msg);
            
        end
        function disableStreaming(obj,type)
            if nargin < 2
                type = 1;
            end
            
            [ msg ] = obj.msg_disable_streaming( type );
            
            sendUdpCommand(obj,msg);
            
        end
        function resetNfu(obj)
            disp('Incomplete');
            return
            %reset NFU message
            reset_Nfu = uint8([70; 9]);
            %write cfg NFU message
            
            write_cfg_Nfu = uint8([ 4, reshape(char(szParam),length(szParam),1), zeros(128-length(szParam),1), 8, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 128, 63]);
            
        end
        function setParam(obj,param,value)
            % Take input parameter and send to NFU.  if value is provided
            % the new value will be updated.  If not provided, the value
            % used from the base workspace parameter will be used
            % if param is a string, it should be the name of a base
            % workspace SimulinkParamter, otherwise, param should be the
            % actual paramter
            
            %             if ischar(param)
            %                 % Input can be either the actual simulink parameter or a
            %                 % string corresponding to the parameter in the base
            %                 % workspace.
            %                 simulinkParam = evalin('base',param);
            %             elseif isa(param,'Simulink.Parameter')
            %                 % input is the actual simulink parameter
            %                 simulinkParam = param;
            %             else
            %                 error('Unknown data type passed into input parameter');
            %             end
            
            % If value not passed, update param with the .Value field
            if nargin > 2
                if ~isequal(size(value),param.Dimensions)
                    error('Bad Value Size');
                end
                
                param.Value = value;
            end
            
            fprintf('[%s] Setting NFU parameter %s to %d\n',mfilename,param.Description,value);
            
            [ msg ] = obj.msg_update_param( param );
            
            sendUdpCommand(obj,msg);
            
        end
        function reset_buffers(obj)
            obj.BufferSize = 100;
            
            obj.UdpBuffer1 = cell(obj.BufferSize,1);
            obj.UdpBuffer2 = cell(obj.BufferSize,1);
            obj.UdpBuffer3 = cell(obj.BufferSize,1);
            obj.UdpBuffer4 = cell(obj.BufferSize,1);
            
            obj.newData1 = false(obj.BufferSize,1);
            obj.newData2 = false(obj.BufferSize,1);
            obj.newData3 = false(obj.BufferSize,1);
            obj.newData4 = false(obj.BufferSize,1);
            
            obj.ptr1 = 1;
            obj.ptr2 = 1;
            obj.ptr3 = 1;
            obj.ptr4 = 1;
            
            obj.sum1 = 0;
            obj.sum2 = 0;
            obj.sum3 = 0;
            obj.sum4 = 0;
            
        end
        function tactorControl(obj, nodeid, period, amplitude, duration, currentLimit, offset )
            % If value not passed, update param with the .Value field
            [ msg ] = obj.msg_tactor_control( nodeid, period, amplitude, duration, currentLimit, offset );
            
            sendUdpCommand(obj,msg);
            
        end
        
        function cellData = get_buffer(obj,id)
            % read unread buffer data and return array of cells
            
            switch id
                case 1
                    %fprintf('[%s] reading %d unread data packets\n',mfilename,sum(obj.newData1));
                    
                    idOfInterest = obj.ptr1:(obj.ptr1+obj.BufferSize-1);
                    idOfInterest = idOfInterest(:) & obj.newData1(:);
                    
                    % wrap indices eg: 99 100 1 2 3
                    idOfInterest(idOfInterest > obj.BufferSize) = idOfInterest(idOfInterest > obj.BufferSize) - obj.BufferSize;
                    
                    % return buffer
                    % 05Feb2013: Verified signal packet ordering is correct
                    % using the nfuSimulator
                    cellData = obj.UdpBuffer1(idOfInterest);
                    
                    % mark all as read
                    obj.newData1(:) = false;
                    
                case 2
                    %fprintf('[%s] reading %d unread data packets\n',mfilename,sum(obj.newData2));
                    
                    idOfInterest = obj.ptr2:(obj.ptr2+obj.BufferSize-1);
                    idOfInterest = idOfInterest(:) & obj.newData2(:);
                    
                    % wrap indices eg: 99 100 1 2 3
                    idOfInterest(idOfInterest > obj.BufferSize) = ...
                        idOfInterest(idOfInterest > obj.BufferSize) - obj.BufferSize;
                    
                    % return buffer
                    cellData = obj.UdpBuffer2(idOfInterest);
                    
                    % mark all as read
                    obj.newData2(:) = false;
                otherwise
                    error('Invalid Buffer');
            end
            
        end
        function numReads = update(obj)
            % Update function reads any buffered udp packets and stores
            % them for later use.  Packets are routed based on size to the
            % appropriate buffer
            
            [cellDataBytes, numReads] = obj.UdpStreamReceiveSocket.getAllData();
            
            if obj.Verbose >= 2
                fprintf('Packets Read:')
                disp(cellDataBytes)
            end
            
            %check how far back we read to get caught up with stream
            if numReads > 20
                numReads
            end
            for i = 1:numReads
                dataBytes = cellDataBytes{i};
                len = length(dataBytes);
                
                if (len == 1882) || (len == 2190)
                    % Store CPC and new percept data with next gen FTSN
                    % also get single ended data
                    
                    % cpch
                    
                    % advance packet counter
                    obj.numPacketsReceived = obj.numPacketsReceived + 1;
                    
                    % compute the number of CPCH bytes
                    numDataBytes = 726+640;  % diffData + seData
                    
                    % read data and mark as new
                    b1 = dataBytes(1:numDataBytes);  %cpch bytes
                    [dataValues, sequenceNumber] = MPL.NfuUdp.cpch_bytes_to_signal(b1);
                    obj.UdpBuffer1{obj.ptr1} = dataValues;
                    obj.newData1(obj.ptr1) = true;
                    
                    % advance ptr
                    obj.ptr1 = obj.ptr1 + 1;
                    if obj.ptr1 > obj.BufferSize
                        obj.ptr1 = 1;
                    end
                    
                    obj.sum1 = obj.sum1 + 1;
                    
                    % percepts
                    
                    b2 = dataBytes(1+numDataBytes:end);  %percept bytes
                    
                    
                    newPercepts = MPL.NfuUdp.decode_percept_msg(b2);
                    obj.UdpBuffer2{obj.ptr2} = newPercepts;
                    obj.newData2(obj.ptr2) = true;
                    
                    % advance ptr
                    obj.ptr2 = obj.ptr2 + 1;
                    if obj.ptr2 > obj.BufferSize
                        obj.ptr2 = 1;
                    end
                    
                    obj.sum2 = obj.sum2 + 1;
                    
                    % Ensure the LmcPosition is updated with the latest
                    % percepts
                    CountsToRadians = 1/650;
                    allJoints = newPercepts.LMC([23 24],:);
                    p = double(typecast(allJoints(:),'int16')) * CountsToRadians;
                    allJoints = newPercepts.LMC([21 22],:);
                    t = double(typecast(allJoints(:),'int16'));

                    obj.LmcPosition = p;
                    obj.LmcTorque = t;
                    
                elseif (len == 36)
                    % Store heartbeat message
                    % typedef struct
                    % {
                    %      System_state_mode_type limb_state_mode; // should be 4 bytes
                    %      Int32u number_of_cpchs_messages;
                    % }Heartbeat_msg;
                    %
                    try
                        newData = dataBytes;
                        % offset zero based state with 1 based
                        SW_STATE = typecast(newData(1:4),'uint32');
                        strState = obj.nfuStates{SW_STATE+1};
                        
                        numMsgs = typecast(newData(5:8),'uint32');
                        nfuStreaming = typecast(newData(9:16),'uint64');
                        lcStreaming = typecast(newData(17:24),'uint64');
                        cpchStreaming = typecast(newData(25:32),'uint64');
                        busVoltageCounts = typecast(newData(33:34),'uint16');
                        busVoltage = double(busVoltageCounts) / 148.95;
                        
                        if obj.hideHeartbeat
                            return
                        end
                        
                        if busVoltage < obj.busVoltageWarn
                            fprintf(2,'[%s.m %s] NFU: V = %6.2f State = "%s", CPC msgs = "%d", Streaming NFU = %d LC = %d CPCH = %d\n',...
                                mfilename,datestr(now),busVoltage,strState,numMsgs,nfuStreaming,lcStreaming,cpchStreaming);
                        else
                            fprintf('[%s.m %s] NFU: V = %6.2f State = "%s", CPC msgs = "%d", Streaming NFU = %d LC = %d CPCH = %d\n',...
                                mfilename,datestr(now),busVoltage,strState,numMsgs,nfuStreaming,lcStreaming,cpchStreaming);
                        end
                    catch ME
                        disp(newData)
                        fprintf('[%s.m %s] Error parsing heartbeat.  Msg: %s \n',mfilename, datestr(now), ME.message);
                    end
                elseif len > 0
                    %len
                    fprintf('[%s] Unexpected Packet Size: %d bytes\n',mfilename,len);
                end
            end
        end
    end
    methods (Static)
        function singleObj = getInstance(cmd)
            % singleObj = MPL.NfuUdp.getInstance
            %
            %   Returns handle to the singleton NfuUdp interface Object.
            %   First call calls object constructor.  Subsequent calls will
            %   return only a handle to the current NFU UDP interface.
            %
            %       % Delete singleton object
            %       singleObj = MPL.NfuUdp.getInstance(-1)
            
            persistent localObj
            
            % Default return argument
            singleObj = [];
            
            if nargin < 1
                cmd = 0;
            end
            
            if cmd < 0
                fprintf('[%s] Deleting NfuUdp comms object\n',mfilename);
                try
                    obj.UdpStreamReceiveSocket.close();
                end
                try
                    obj.UdpCommandSocket.close();
                end
                %IsInitialized
                localObj = [];
                return
            end
            
            if isempty(localObj) || ~isvalid(localObj)
                fprintf('[%s] Calling constructor\n',mfilename);
                localObj = MPL.NfuUdp;
                
                localObj.Hostname = UserConfig.getUserConfigVar('mplNfuIp','192.168.1.111');
                localObj.UdpStreamReceivePortNumLocal = UserConfig.getUserConfigVar('mplNfuUdpStreamPort',9027);
                localObj.TcpPortNum = UserConfig.getUserConfigVar('mplNfuTcpCommandPort',6200);
                localObj.UdpCommandPortNumLocal = UserConfig.getUserConfigVar('mplNfuUdpCommandPortLocal',52000);
                localObj.UdpCommandPortNumRemote = UserConfig.getUserConfigVar('mplNfuUdpCommandPort',6201);
                
            else
                fprintf('[%s] Returning existing object\n',mfilename);
            end
            singleObj = localObj;
        end
        function [ msg ] = msg_enable_streaming( type )
            %enable_streaming Summary of this function goes here
            %   Detailed explanation goes here
            
            if type == 1
                %CPC HS
                enable_stream_Nfu = uint8([ 150, 38, 1, zeros(1,7) ]);
            elseif type == 2
                %VULCANX
                enable_stream_Nfu = uint8([ 150, 9, 8, zeros(1,7) ]);
            elseif type == 3
                %ALGORITHM
                enable_stream_Nfu = uint8([ 150, 9, 4, zeros(1,7) ]);
            elseif type == 4
                %LC PERCEPTS
                enable_stream_Nfu = uint8([ 150, 10, 1, zeros(1,7) ]);
            elseif type == 5
                %NFU PERCEPTS
                enable_stream_Nfu = uint8([ 150, 9, 1, zeros(1,7) ]);
            else
                error('Unmatched Type');
            end
            
            msg = enable_stream_Nfu;
        end
        function [ msg ] = msg_disable_streaming( type )
            %disable_streaming Summary of this function goes here
            %   Detailed explanation goes here
            
            if type == 1
                %CPC HS
                enable_stream_Nfu = uint8([ 150, 38, 0, zeros(1,7) ]);
            elseif type == 2
                %VIE
                enable_stream_Nfu = uint8([ 150, 9, 0, zeros(1,7) ]);
            elseif type == 3
                %ALGORITHM
                enable_stream_Nfu = uint8( [150, 9, 0, zeros(1,7) ]);
            elseif type == 4
                %LC PERCEPTS
                enable_stream_Nfu = uint8( [150, 10, 0, zeros(1,7) ]);
            else
                error('Unmatched Type');
            end
            
            msg = enable_stream_Nfu;
        end
        function [ msg ] = msg_update_param( param )
            %update_param Summary of this function goes here
            %   Detailed explanation goes here
            
            % calculate dimensions
            dim_X = typecast(uint32(param.Dimensions(1)), 'uint8');
            dim_Y = typecast(uint32(param.Dimensions(2)), 'uint8');
            
            % calculate fields
            bval = zeros(4*param.Dimensions(1)*param.Dimensions(2),1,'uint8');
            
            % KDK: 1/30/2012
            % Note: Performing transpose to account for row-major c-code versus column
            % major Matlab parameters
            for i=1:param.Dimensions(1)
                for j=1:param.Dimensions(2)
                    %a = int32(single2int32(param.Value(i,j)));
                    a = typecast(single(param.Value(i,j)),'int32');
                    c = typecast(a, 'uint8');
                    bval((4*(((j-1)*param.Dimensions(1) + i) - 1))+...
                        1:(4*(((j-1)*param.Dimensions(1) + i) - 1))+4) = c;
                    
                end
            end
            
            msgId = 4;
            write_cfg_Nfu = uint8([ ...
                msgId, ...
                uint8(param.Description),...
                zeros(1,128-length(param.Description)),...
                8, 0, 0, 0, ...
                dim_X, ...
                dim_Y, ...
                bval(:)']);
            
            msg = write_cfg_Nfu;
            
        end
        function [ msg ] = msg_tactor_control( nodeid, period, amplitude, duration, currentLimit, offset )
            tactor_node = typecast(int32(nodeid), 'uint8');
            
            per = uint8(period);
            amp = typecast(int16(amplitude), 'uint8');
            dur = typecast(uint16(duration), 'uint8');
            curr = typecast(uint16(currentLimit), 'uint8');
            off = typecast(int16(offset), 'uint8');
            
            
            tactor_control_Nfu = uint8([ 60, tactor_node, per, amp, dur, curr, off]);
            
            msg = tactor_control_Nfu;
            
        end
        
        function tlm = decode_percept_msg(b)
            
            tlm = [];
            
            % tlm =
            %
            %                  Percept: [1x10 struct]
            %        UnactuatedPercept: [1x8 struct]
            %              FtsnPercept: [1x5 struct]
            %     ContactSensorPercept: [1x1 struct]
            
            % mixing matlab indexing 1-based and enum count

            % typedef struct Nfu_telemetry_type {
            % NfuCpcDataPayload_t pkt[ CPC_STREAM_BUFFER_SIZE ];
            % Percept_stream_response_type sync_percepts_copy;
            % LMC_SensorData lmc_se?nsor_data[MAX_LMC_NODES];
            % } __attribute__ ((__packed__)) Nfu_telemetry_type;
            %
            % #define NFU_TELEMETRY_TYPE_MSG_BYTES sizeof(Nfu_telemetry_type)
            %  
            % LMC_SensorData[7] is defined by this struct:
            % (20 bytes plus StatusPollResponse)
            % typedef struct {
            % 
            %   StatusPollResponse status;
            %   int16_T torque;
            %   int16_T motor_position;
            %   int16_T motor_velocity;
            %   int16_T motor_acceleration;
            %   int16_T link_position;
            %   uint8_T temperature;
            %   int16_T motor_current;
            %   uint8_T is_motor_powered;
            %   uint8_T is_motor_running;
            %   uint8_T fault;
            %   int16_T bus_voltage;
            %   int16_T bus_current;
            % } LMC_SensorData;
            % 
            % 
            % typedef struct {
            %   MotorDirection motor_dir;
            %   uint8_T udc_sign;
            %   CurrentLimit is_current_limited;
            %   BIT_States bit_state;
            %   HandStates sw_state;
            % } StatusPollResponse;

            %#ok<*NASGU>
            
            % Enable Flags
            PERCEPT_ENABLE_ACTUATED_PERCEPTS = 1;
            PERCEPT_ENABLE_UNACTUATED_PERCEPTS = 2;
            PERCEPT_ENABLE_INDEX_FTSN = 3; 
            PERCEPT_ENABLE_MIDDLE_FTSN = 4;
            PERCEPT_ENABLE_RING_FTSN = 5;
            PERCEPT_ENABLE_LITTLE_FTSN = 6;
            PERCEPT_ENABLE_THUMB_FTSN = 7;
            PERCEPT_ENABLE_CONTACT = 8;
            PERCEPT_ENABLE_NUM_IDS = 8;
            
            % Actuated
            PERCEPTID_INDEX_AB_AD = 1;
            PERCEPTID_INDEX_MCP = 2;
            PERCEPTID_MIDDLE_MCP = 3;
            PERCEPTID_RING_MCP = 4;
            PERCEPTID_LITTLE_AB_AD = 5;
            PERCEPTID_LITTLE_MCP = 6;
            PERCEPTID_THUMB_CMC_AD_AB = 7;
            PERCEPTID_THUMB_CMC_FE = 8;
            PERCEPTID_THUMB_MCP = 9;
            PERCEPTID_THUMB_DIP = 10;
            PERCEPT_NUM_IDS = 10;
            
            % UnActuated
            PERCEPTID_INDEX_PIP = 1;
            PERCEPTID_INDEX_DIP = 2;
            PERCEPTID_MIDDLE_PIP = 3;
            PERCEPTID_MIDDLE_DIP = 4;
            PERCEPTID_RING_PIP = 5;
            PERCEPTID_RING_DIP = 6;
            PERCEPTID_LITTLE_PIP = 7;
            PERCEPTID_LITTLE_DIP = 8;
            UNACTUATED_PERCEPT_NUM_IDS = 8;
            
            %FTSN
            PERCEPTID_INDEX_FTSN = 1;
            PERCEPTID_MIDDLE_FTSN = 2;
            PERCEPTID_RING_FTSN = 3;
            PERCEPTID_LITTLE_FTSN = 4;
            PERCEPTID_THUMB_FTSN = 5;
            FTSN_PERCEPT_NUM_IDS = 5;
            
            b = uint8(b);
            data_bytes = typecast(b(1:4),'uint32');
            data = b(5:end);
            
            percepts_config = bitget(data(1),1:PERCEPT_ENABLE_NUM_IDS);
            ftsn_config = bitget(data(2),1:FTSN_PERCEPT_NUM_IDS);
            
            index_size = data(1);
            
            data_index = 2;
            
            Percepts_enable_config_id.PERCEPT_ENABLE_ACTUATED_PERCEPTS = 1;
            
            ToInt16 = @(b,p) typecast( b(p+1:p+2) ,'Int16');
            
            if (percepts_config(PERCEPT_ENABLE_ACTUATED_PERCEPTS) == true)
                for i = 0:PERCEPT_NUM_IDS-1
                    tlm.Percept(i+1).Position = ToInt16(data,data_index + i * 7);
                    tlm.Percept(i+1).Velocity = ToInt16(data,data_index + 2 + i * 7);
                    tlm.Percept(i+1).Torque = ToInt16(data,data_index + 4 + i * 7);
                    tlm.Percept(i+1).Temperature = data(1 + data_index + 6 + i * 7);                    
                end
                data_index = data_index + 70;
            end
            
            % tlm.Percept(6)
            
            if (percepts_config(PERCEPT_ENABLE_UNACTUATED_PERCEPTS) == true)
                for i = 0:UNACTUATED_PERCEPT_NUM_IDS-1
                    tlm.UnactuatedPercept(i+1).Position = ToInt16(data, data_index + i * 2);
                end
                data_index = data_index + 16;
            end
            
            % tlm.UnactuatedPercept(1)
            
            
            for i = 0:FTSN_PERCEPT_NUM_IDS-1
                if (percepts_config(i+2) == true)
                    tlm.FtsnPercept(i+1).forceConfig = ftsn_config(i+1);
                    
                    % old style
                    if (ftsn_config(i+1) == false)
                        tlm.FtsnPercept(i+1).force_pressure = ToInt16(data, data_index);
                        data_index = data_index + 2;
                        tlm.FtsnPercept(i+1).force_shear = ToInt16(data, data_index);
                        data_index = data_index + 2;
                        tlm.FtsnPercept(i+1).force_axial = ToInt16(data, data_index);
                        data_index = data_index + 2;
                        
                        tlm.FtsnPercept(i+1).acceleration_x = data(data_index+1);
                        data_index = data_index + 1;
                        tlm.FtsnPercept(i+1).acceleration_y = data(data_index+1);
                        data_index = data_index + 1;
                        tlm.FtsnPercept(i+1).acceleration_z = data(data_index+1);
                        data_index = data_index + 1;
                    else
                        % new sytle
                        for j = 0:14-1
                            tlm.FtsnPercept(i+1).force(j+1) = data(data_index+1);
                            data_index = data_index + 1;
                        end
                        
                        tlm.FtsnPercept(i+1).acceleration_x = data(data_index+1);
                        data_index = data_index + 1;
                        tlm.FtsnPercept(i+1).acceleration_y = data(data_index+1);
                        data_index = data_index + 1;
                        tlm.FtsnPercept(i+1).acceleration_z = data(data_index+1);
                        data_index = data_index + 1;
                        
                    end
                end
            end
            
            % tlm.FtsnPercept(1)
            if (percepts_config(PERCEPT_ENABLE_CONTACT) == true)
                contact_data = data(data_index+1:data_index+12);
                
                tlm.ContactSensorPercept.index_contact_sensor = contact_data(1);
                tlm.ContactSensorPercept.middle_contact_sensor = contact_data(2);
                tlm.ContactSensorPercept.ring_contact_sensor = contact_data(3);
                tlm.ContactSensorPercept.little_contact_sensor = contact_data(4);
                
                tlm.ContactSensorPercept.index_abad_contact_sensor_1 = contact_data(5);
                tlm.ContactSensorPercept.index_abad_contact_sensor_2 = contact_data(6);
                
                tlm.ContactSensorPercept.little_abad_contact_sensor_1 = contact_data(7);
                tlm.ContactSensorPercept.little_abad_contact_sensor_2 = contact_data(8);
                
            end
                        
            if length(b) > 518
                % Process LMC Percepts
                %                 
                % 
                % 
                % typedef struct {
                %   StatusPollResponse status;
                %   int16_T torque;              [25,26]
                %   int16_T motor_position;      [27,28]
                %   int16_T motor_velocity;      [29,30]
                %   int16_T motor_acceleration;  [31,32]
                %   int16_T link_position;       [33,34]
                %   uint8_T temperature;         [35]
                %   int16_T motor_current;  [20?][36,37]
                %   uint8_T is_motor_powered;   [38]
                %   uint8_T is_motor_running;   [39]
                %   uint8_T fault;          [40]
                %   int16_T bus_voltage;    [41,42]
                %   int16_T bus_current;    [43,44]
                % } LMC_SensorData;
                % 
                % typedef struct { [24?]
                %   MotorDirection motor_dir;  
                %   uint8_T udc_sign;
                %   CurrentLimit is_current_limited;
                %   BIT_States bit_state;
                %   HandStates sw_state;
                % } StatusPollResponse;                
                
                %%
                lmc = reshape(b(end-308+1:end),44,7);
% %                 typecast(lmc(4,[27,28]),'int16')
% %                 lmc(1:24,4)'
% fp = fopen('test_log.txt','a+');
% fprintf(fp,'%04d ',lmc(:,4));
% fprintf(fp,'\n');
% 
% %                 lmc(25:end,4)'
                
            else
                lmc = [];
            end
            
            tlm.LMC = lmc;
            
            
        end
        function [s, sequenceNumber] = cpch_bytes_to_signal(b)
            
            % Determine expected packet size
            numPacketHeaderBytes = 6;
            numSamplesPerPacket = 20;
            numSampleHeaderBytes = 4;
            if length(b) == 406
                numChannelsPerPacket = 8;
            elseif length(b) == 726
                numChannelsPerPacket = 16;
            elseif length(b) == 1366
                numChannelsPerPacket = 32;
            end
            numBytesPerChannel = 2;
            numBytesPerSample = numChannelsPerPacket*numBytesPerChannel + numSampleHeaderBytes;
            cpchpacketSize = numPacketHeaderBytes+numBytesPerSample*numSamplesPerPacket;
            
            % First 6 bytes of message are global header
            %hdr = b(1:numPacketHeaderBytes);
            data = reshape(b(numPacketHeaderBytes+1:cpchpacketSize),...
                numBytesPerSample,numSamplesPerPacket);
            
            % First 5 bytes per sample are header
            databytes = data(numSampleHeaderBytes+1:end,:);
            s = reshape(typecast(databytes(:),'int16'),...
                numChannelsPerPacket,numSamplesPerPacket);
            
            sequenceNumber = data(3,:);
            
            % DEBUG!!!!! added this to check sequence numbers
            s(end,:) = int16(sequenceNumber);
            
        end        
    end
end
