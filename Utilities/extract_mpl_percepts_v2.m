function [feedback_data] = extract_mpl_percepts_v2(udpData)
dbstop if error

rocs = [];
feedback_data = [];

segment_to_display = 0;
%force_to_display = 3; % 1 for x, 2, for y, 3 for z

PERCEPT_DATA = uint8(200);
NONE = uint8(0);
ALL_DOM_POS_VEL_TORQUE = uint8(1);      % this actually also contains temperature
ROC_TABLE_POS_VAL = uint8(1);
CONTACT_FORCE_ACCEL_TEMP = uint8(1); % MUD ICD Value - Old FTSN Sensors
CONTACT_FORCEv2_ACCEL_TEMP = uint8(2); % MUD ICD Value - New FTSN Sensors

len = typecast(udpData(1:2),'uint16');
MplStreamingMessageId = udpData(3);    % should be 200
ind = 0;
%disp(MplStreamingMessageId);

switch MplStreamingMessageId
    case PERCEPT_DATA
        ind = uint16(4);
        
        %Parse LimbPercepstType Data
        LimbPerceptsType = udpData(ind);
        switch LimbPerceptsType
            case NONE
                % do nothing
                ind = ind + 1;
            otherwise
                warning('invalid LimbPerceptsType');
                disp(udpData);
        end
        
        %Parse JointPerceptsType Data
        JointPerceptsType = udpData(ind);
        switch JointPerceptsType
            case NONE
                %Fill the return structure with zeros
                feedback_data.jointPercepts.position = zeros(1, 27);
                feedback_data.jointPercepts.velocity = zeros(1, 27);
                feedback_data.jointPercepts.torque = zeros(1, 27);
                feedback_data.jointPercepts.temperature = zeros(1, 27);
                ind = ind + 1;
            case ALL_DOM_POS_VEL_TORQUE
                % percept types are pos, vel, torque, temperature
                ind = ind + 1;
                temp = reshape(swapbytes(typecast(udpData(ind:(ind+4*4*27-1)),'single')),[27 4]);
                feedback_data.jointPercepts.position = temp(:,1)';
                feedback_data.jointPercepts.velocity = temp(:,2)';
                feedback_data.jointPercepts.torque = temp(:,3)';
                feedback_data.jointPercepts.temperature = temp(:,4)';
                ind = ind + 4*4*27; % 4 percept types * sizeof(single) * 27 joints
            otherwise
                warning('invalid JointPerceptsType');
                disp(udpData);
        end
        
        %Parse ROCPerceptsType Data
        ROCPerceptsType = udpData(ind);
        ind = ind + 1;
        switch ROCPerceptsType
            case NONE
                % do nothing
            case ROC_TABLE_POS_VAL
                numRocTables = uint16(udpData(ind));
                ind = ind + 1;
                SIZE_OF_ROC_TABLE = 14;         % num bytes
                NUM_ELEMENTS_IN_ROC_TABLE = 5;
                rocs = zeros(numRocTables, NUM_ELEMENTS_IN_ROC_TABLE);
                
                for tableInd = 0:numRocTables - 1
                    % RocTablePosValType:
                    %   uint8 rocTableid
                    %   uint8 indexMode
                    %   single index
                    %   single value
                    %   single weight
                    
                    rocs(tableInd+1,:) = ...
                        [single(udpData(ind)) single(udpData(ind+1)) ...
                        swapbytes(typecast(udpData(ind+uint16(2:13)), 'single'))];
                    ind = ind + SIZE_OF_ROC_TABLE;
                end
                
                feedback_data.rocs = rocs;
            otherwise
                warning('invalid ROCPerceptsType');
                disp(udpData);
        end
        
        %Parse SegmentPerceptsType Data
        SegmentPerceptsType = udpData(ind);
        ind = ind + 1;
        feedback_data.segmentPercepts.fstnForce = zeros(14, 5);
        feedback_data.segmentPercepts.fstnAccel = zeros(3, 5);
        feedback_data.segmentPercepts.contactPercepts = zeros(1,37);
        switch SegmentPerceptsType
            case NONE
                % do nothing
                
            case CONTACT_FORCE_ACCEL_TEMP
                % ContactForceAccelTempType struct has four elements:
                %   ContactPerceptsType     contact         37 (37 enum for each of potential contact sensors)
                %   FtsnForcePerceptsType   force           60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60)) - force sensors
                %   FtsnAccelPerceptsType   acceleration    60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60)) - accel sensors
                %   FtsnTempPerceptsType    temperature     20 (1 x 32-bit value (1 x 4 bytes) for each of 5 fingers, so (1x4x5 = 20)) - temperature sensors
                %
                % (to skip)-> ind = ind + 37 + 60 + 60 + 20;
                %SIZE_OF_SEG_DATA = (37+60+60+20);         % num bytes, CONST_PERCEPTS_JOINTS=27
                NUM_CONTACT_SENSORS = 37;
                NUM_FTSN_SEGMENTS = 5; %index, middle, ring, little, thumb
                NUM_FTSN_DATA_TYPES = 3; %force, acceleration, temperature
                NUM_FTSN_DATA_TYPES_FORCE = 1;
                NUM_FTSN_DATA_TYPES_ACCEL = 2;
                NUM_FTSN_DATA_TYPES_TEMP = 3;
                NUM_FTSN_DATA_MAX_NUMBER_VALUES = 3; % 3 axes for force and acceleration data (only 1 for temperature)
                %NUM_FTSN_DATA_MAX_NUMBER_VALUES_X = 1;
                %NUM_FTSN_DATA_MAX_NUMBER_VALUES_Y = 2;
                %NUM_FTSN_DATA_MAX_NUMBER_VALUES_Z = 3;
                
                %---------------------------------------
                % CONTACT SENSORS PERCEPTS
                %---------------------------------------
                
                % TODO - Implement Contact Sensor Percepts Parsing - 2/13/12
                
                % SKIP parsing of contact sensor - 2/13/12
                %segContactPercepts = typecast(udpData(ind:(ind+NUM_CONTACT_SENSORS-1)), 'single');
                %segContactPercepts = udpData(ind:(ind+NUM_CONTACT_SENSORS-1));
                segContactPercepts = single(typecast(udpData(ind:(ind+NUM_CONTACT_SENSORS*2-1)), 'uint16'));                
                ind = ind + NUM_CONTACT_SENSORS*2; %Increment UDP Array Index (+37 currently)
                
                %---------------------------------------
                % FTSN SENSORS PERCEPTS
                %---------------------------------------
                % Format the FTSN Percepts Array
                segFTSNPercepts = zeros(NUM_FTSN_SEGMENTS, NUM_FTSN_DATA_TYPES, NUM_FTSN_DATA_MAX_NUMBER_VALUES); %converted to singles below
                
                % FTSN FORCE
                % Traverse each FTSN Segment (5 stated for each finger,
                % but currently only thumb, pointer, and middle finger
                % implemented)
                % for segmentId = 1:5
                
                for segmentId = 1:NUM_FTSN_SEGMENTS
                    
                    %Traverse each axis of force value
                    for axisId = 1:NUM_FTSN_DATA_MAX_NUMBER_VALUES
                        %force_temp = typecast(udpData(ind:ind+3), 'single'); %Float32 z
                        force_temp = swapbytes(typecast(udpData(ind:ind+3), 'single')); %Float32 z
                        %force_temp = swapbytes(typecast(udpData(ind:ind+3), 'double')); %Float32 z
                        ind = ind + 4; %Increment UDP Array Index - (4 Bytes in each Float32 value)
                        
                        feedback_data.segmentPercepts.fstnForce(axisId, segmentId) = force_temp;
                        
                        % Populate segFTSNPercepts Array - Force Values
                        segFTSNPercepts(segmentId, NUM_FTSN_DATA_TYPES_FORCE, axisId) = force_temp;
                        
                    end %/for - Traversing each axis (x, y, z)
                    
                end %/for - Traversing each FTSN segment (index, middle, etc.)
                
                % FTSN ACCELERATION
                % for segmentId = 1:5
                for segmentId = 1:NUM_FTSN_SEGMENTS
                    
                    %Traverse each axis of accel value
                    for axisId = 1:NUM_FTSN_DATA_MAX_NUMBER_VALUES
                        %accel_temp = typecast(udpData(ind:ind+3), 'single'); %Float32 z
                        accel_temp = swapbytes(typecast(udpData(ind:ind+3), 'single')); %Float32 z
                        %accel_temp = swapbytes(typecast(udpData(ind:ind+3), 'double')); %Float32 z
                        ind = ind + 4; %Increment UDP Array Index - (4 Bytes in each Float32 value)
                        
                        feedback_data.segmentPercepts.fstnAccel(axisId,segmentId) = accel_temp;
                        
                        % Populate segFTSNPercepts Array - Acceleration Values
                        segFTSNPercepts(segmentId, NUM_FTSN_DATA_TYPES_ACCEL, axisId) = accel_temp;
                        
                    end %/for - Traversing each axis (x, y, z)
                    
                end %/for - Traversing each FTSN segment (index, middle, etc.)
                
                % FTSN TEMPERATURE
                %for segmentId = 1:5
                for segmentId = 1:NUM_FTSN_SEGMENTS
                    temperature_temp = swapbytes(typecast(udpData(ind:ind+3), 'single')); %Float32, temporary value of temperature
                    ind = ind + 4; %Increment UDP Array Index - (4 Bytes in each Float32 value)
                    
                    % Populate segFTSNPercepts Array - Temperature Values
                    segFTSNPercepts(segmentId, NUM_FTSN_DATA_TYPES_TEMP, 1) = temperature_temp; %Only 1 value of tempertuare per sensor (unlike 3 axis values for force/accel)
                    
                end %/for - Traversing each FTSN segment (index, middle, etc.)
                
            case CONTACT_FORCEv2_ACCEL_TEMP
                % ContactForceAccelTempType struct has four elements:
                %   ContactPerceptsType     contact         37 (37 enum for each of potential contact sensors)
                %   FtsnForcePerceptsType   force           60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60)) - force sensors
                %   FtsnAccelPerceptsType   acceleration    60 (3-axis x 32-bit values (3 x 4 bytes) for each of 5 fingers, so (3x4x5 = 60)) - accel sensors
                %   FtsnTempPerceptsType    temperature     20 (1 x 32-bit value (1 x 4 bytes) for each of 5 fingers, so (1x4x5 = 20)) - temperature sensors
                %
                % (to skip)-> ind = ind + 37 + 60 + 60 + 20;
                %SIZE_OF_SEG_DATA = (37+60+60+20);         % num bytes, CONST_PERCEPTS_JOINTS=27
                NUM_CONTACT_SENSORS = 37;
                NUM_FTSN_SEGMENTS = 5; %index, middle, ring, little, thumb
                NUM_FTSN_DATA_TYPES = 3; %force, acceleration, temperature
                NUM_FTSN_DATA_TYPES_FORCE = 1;
                NUM_FTSN_DATA_TYPES_ACCEL = 2;
                NUM_FTSN_DATA_TYPES_TEMP = 3;
                NUM_FTSN_FORCE_MAX_NUMBER_VALUES = 14; % 14 capacitive force sensors
                NUM_FTSN_ACCEL_MAX_NUMBER_VALUES = 3; % 3 axes for force and acceleration data (only 1 for temperature)
                %NUM_FTSN_DATA_MAX_NUMBER_VALUES_X = 1;
                %NUM_FTSN_DATA_MAX_NUMBER_VALUES_Y = 2;
                %NUM_FTSN_DATA_MAX_NUMBER_VALUES_Z = 3;
                
                %---------------------------------------
                % CONTACT SENSORS PERCEPTS
                %---------------------------------------
                
                % TODO - Implement Contact Sensor Percepts Parsing - 2/13/12
                
                % SKIP parsing of contact sensor - 2/13/12
                %segContactPercepts = typecast(udpData(ind:(ind+NUM_CONTACT_SENSORS-1)), 'single');
                %segContactPercepts = udpData(ind:(ind+NUM_CONTACT_SENSORS-1));
                segContactPercepts = single(typecast(udpData(ind:(ind+NUM_CONTACT_SENSORS*2-1)), 'uint16'));
                feedback_data.segmentPercepts.contactPercepts = segContactPercepts;
                
                ind = ind + NUM_CONTACT_SENSORS*2; %Increment UDP Array Index (+37 currently)
                
                %---------------------------------------
                % FTSN SENSORS PERCEPTS
                %---------------------------------------
                % Format the FTSN Percepts Array
                segFTSNPercepts = zeros(NUM_FTSN_SEGMENTS, NUM_FTSN_DATA_TYPES, NUM_FTSN_FORCE_MAX_NUMBER_VALUES); %converted to singles below
                
                % FTSN FORCE
                % Traverse each FTSN Segment (5 stated for each finger,
                % but currently only thumb, pointer, and middle finger
                % implemented)
                % for segmentId = 1:5
                for segmentId = 1:NUM_FTSN_SEGMENTS
                    
                    ind = ind + 1; %Increment UDP Array Index - (1 Bytes to specify which ftsn type)
                    %Traverse each axis of force value
                    for axisId = 1:NUM_FTSN_FORCE_MAX_NUMBER_VALUES
                        %force_temp = typecast(udpData(ind:ind+3), 'single'); %Float32 z
                        force_temp = swapbytes(typecast(udpData(ind:ind+3), 'single')); %Float32 z
                        %force_temp = swapbytes(typecast(udpData(ind:ind+3), 'double')); %Float32 z
                        ind = ind + 4; %Increment UDP Array Index - (4 Bytes in each Float32 value)
                        
                        feedback_data.segmentPercepts.fstnForce(axisId, segmentId) = force_temp;
                        
                        
                        % Populate segFTSNPercepts Array - Force Values
                        segFTSNPercepts(segmentId, NUM_FTSN_DATA_TYPES_FORCE, axisId) = force_temp;
                        
                    end %/for - Traversing each axis (x, y, z)
                    
                end %/for - Traversing each FTSN segment (index, middle, etc.)
                
                % FTSN ACCELERATION
                % for segmentId = 1:5
                for segmentId = 1:NUM_FTSN_SEGMENTS
                    
                    %Traverse each axis of accel value
                    for axisId = 1:NUM_FTSN_ACCEL_MAX_NUMBER_VALUES
                        %accel_temp = typecast(udpData(ind:ind+3), 'single'); %Float32 z
                        accel_temp = swapbytes(typecast(udpData(ind:ind+3), 'single')); %Float32 z
                        %accel_temp = swapbytes(typecast(udpData(ind:ind+3), 'double')); %Float32 z
                        ind = ind + 4; %Increment UDP Array Index - (4 Bytes in each Float32 value)
                        
                        feedback_data.segmentPercepts.fstnAccel(axisId,segmentId) = accel_temp;
                        
                        % Populate segFTSNPercepts Array - Acceleration Values
                        segFTSNPercepts(segmentId, NUM_FTSN_DATA_TYPES_ACCEL, axisId) = accel_temp;
                        
                    end %/for - Traversing each axis (x, y, z)
                    
                end %/for - Traversing each FTSN segment (index, middle, etc.)
                
                % FTSN TEMPERATURE
                %for segmentId = 1:5
                for segmentId = 1:NUM_FTSN_SEGMENTS
                    temperature_temp = swapbytes(typecast(udpData(ind:ind+3), 'single')); %Float32, temporary value of temperature
                    ind = ind + 4; %Increment UDP Array Index - (4 Bytes in each Float32 value)
                    
                    % Populate segFTSNPercepts Array - Temperature Values
                    segFTSNPercepts(segmentId, NUM_FTSN_DATA_TYPES_TEMP, 1) = temperature_temp; %Only 1 value of tempertuare per sensor (unlike 3 axis values for force/accel)
                    
                end %/for - Traversing each FTSN segment (index, middle, etc.)
                
                
            otherwise
                % Invalid Segment Percepts Reporting Mode value
                warning('invalid SegmentPerceptsType');
                disp(udpData);
                
        end  %switch - check Percepts Reporting Configuration - Segment/Stim Pecepts On/Off
    otherwise
        warning('invalid MplStreamingMessageId');
        disp(udpData);
end

if ind ~= 0
    checksum = udpData(ind);
else
    checksum = 0;
    warning('ind is 0....this shouldn''t happen');
end

if checksum ~= mod(sum(udpData(1:end-1)),256)
    warning('invalid checksum in MPL percepts message');
end
if ind ~= (len+2)
    warning('invalid length in MPL percepts message');
end
end