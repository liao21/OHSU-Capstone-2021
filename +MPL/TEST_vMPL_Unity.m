% TEST_vMPL_Unity
% See also: MPL.EnumArm for a list of joint enumerations

% Tests basic function of MPL Unity wrappers as well as direct udp
% communications (especially for 4 arm case (ghost targets)

% Revisions:
% 2019-Mar-09 Armiger: Added ghost arm test and all default ports


% TEST using MPL Wrappers:
hSink = MPL.MplUnitySink();
hSink.setPortDefaults()
% hSink.MplLocalPort = 9999
hSink.initialize()

%% Synch Current position and target position
perceptData = hSink.getPercepts();
jointAngles = perceptData.jointPercepts.position; %radians
hSink.putData(jointAngles);

%% Smooth Home
hSink.gotoSmooth([0.1 -0.5 0.2 1.9 0.1 0.0 0.0]);

%%
hSink.gotoSmooth([0.5 -0.5 0.2 0.9 0.1 0.0 0.0]);

%%
ang = zeros(1,27);
ang(1) = 37*pi/180;
ang(2) = -13*pi/180;
ang(3) = 17*pi/180;
ang(4) = 63*pi/180;

hSink.putData(ang)






%%  NEW Test focused on controlling the 'quad arm' control case.
% This varient includes two 'solid' vMPL arms (left/right) and two 'ghost'
% vMPL arms (left/right).  The purpose ofthe ghost arms is to provide
% 'targets' when evaluating prosthetic control

% Typical Port Settings:
% Right Arm Solid:
%   Cmd Port: 25000
%   Percept/Feedback Port: 25001
% Left Arm Solid:
%   Cmd Port: 25100
%   Percept/Feedback Port: 25101
% Right Arm Ghost:
%   Cmd Port: 25010
% Left Arm Ghost:
%   Cmd Port: 25110

% You can now change both the color of the ghost limbs and if they should
% be enabled/disabled using the CONFIG file or using UDP communication.
% The port to send the color and enable/disable values to is: 27000
%
% The enable/disable should be sent first: 1.0 == enabled,  0.0 == disabled
%
%
% The color values should be sent next (R,G,B,A in this order) which need
% to be between 0.0-1.0 since unity determines color on a 0-1 scale instead
% of a 0-256 scale.
%
% If you would like any other features to be added or run into any issues
% please let me know.

% the right shadow accepts the commands on 27000 and the left on 27100

% repo location:
% https://bitbucket.xrcs.jhuapl.edu/scm/real/vmplv5room.git
%

% Running vMPLRoomShadow

pnet('closeall')
hRightSolid = PnetClass(25001,25000,'127.0.0.1');
hRightSolid.initialize();
hLeftSolid = PnetClass(25101,25100,'127.0.0.1');
hLeftSolid.initialize();
hRightGhost = PnetClass(25011,25010,'127.0.0.1');
hRightGhost.initialize();
hLeftGhost = PnetClass(25111,25110,'127.0.0.1');
hLeftGhost.initialize();

hRightGhostControl = PnetClass(27001,27000,'127.0.0.1');
hRightGhostControl.initialize();
hLeftGhostControl = PnetClass(27101,27100,'127.0.0.1');
hLeftGhostControl.initialize();


% Send some test commands to each arm
%
hRightSolid.putData(typecast(single(rand(27,1)),'uint8'))
%
hRightGhost.putData(typecast(single(rand(27,1)),'uint8'))
%
hLeftGhost.putData(typecast(single(rand(27,1)),'uint8'))
%
hLeftSolid.putData(typecast(single(rand(27,1)),'uint8'))
%
hLeftGhostControl.putData(typecast(single([1.0 ones(1,4)]),'uint8'))
%
hRightGhostControl.putData(typecast(single([1.0 rand(1,4)]),'uint8'))

% Read percept data
allPackets = hRightSolid.getAllData;
if ~isempty(allPackets)
    packets = allPackets{end};
    
    % convert to joint angles and velocity
    nJoints = 27;
    nBytesPerFloat = 4;
    floatData = typecast(packets(1:nJoints*nBytesPerFloat*3),'single');
    % reshape to position velocity accel and convert to double
    % precision floating point
    floatData = double(reshape(floatData,3,nJoints));
    
    %data = extract_mpl_percepts_v2(packets);
    data.jointPercepts.position = floatData(1,:);
    data.jointPercepts.velocity = floatData(2,:);
    
    armDegrees = data.jointPercepts.position(1:7) * 180 / pi;
    fprintf(['Arm Angles: SHFE=%6.1f | SHAA=%6.1f | HUM=%6.1f'...
        '| EL=%6.1f | WR=%6.1f | DEV=%6.1f | WFE=%6.1f Degrees\n'],...
        armDegrees);
else
    disp('No Data')
end


%%  Demo controlling 2 arms

pnet('closeall')
hRightSolid = PnetClass(25001,25000,'127.0.0.1');
hRightSolid.initialize();
hLeftSolid = PnetClass(25101,25100,'127.0.0.1');
hLeftSolid.initialize();
hRightGhost = PnetClass(25011,25010,'127.0.0.1');
hRightGhost.initialize();
hLeftGhost = PnetClass(25111,25110,'127.0.0.1');
hLeftGhost.initialize();

hRightGhostControl = PnetClass(27001,27000,'127.0.0.1');
hRightGhostControl.initialize();
hLeftGhostControl = PnetClass(27101,27100,'127.0.0.1');
hLeftGhostControl.initialize();

%% Start with ghost arms off
hLeftGhostControl.putData(typecast(single([0.0 ones(1,4)]),'uint8'))
hRightGhostControl.putData(typecast(single([0.0 rand(1,4)]),'uint8'))

%%
% Send some test commands to each arm
%
% visual params with colormap 
alpha_val = 0.6;
N = 256;
c_map = [jet(N/2); flipud(jet(N/2))];
ang = zeros(27,1);
ang2 = zeros(27,1);

hRightGhost.putData(typecast(single(ang),'uint8'))
hRightSolid.putData(typecast(single(ang2),'uint8'))

%% 
% fade in
for i = linspace(0.0,alpha_val,50)
    hRightGhostControl.putData(typecast(single([1.0 c_map(1,:) i]),'uint8'))
    pause(0.02)
end

% run haversine curve with phase lag
for i = 1:size(c_map,1)
    % generate haversine curves
    val = 135*pi/180*(-0.5*cos(2*pi*i/N)+0.5);
    val2 = 135*pi/180*(-0.5*cos(2*pi*(i/N - 0.05))+0.5);
    ang(MPL.EnumArm.ELBOW) = val;
    ang2 = ang;
    ang2(MPL.EnumArm.ELBOW) = val2;
    hRightGhost.putData(typecast(single(ang),'uint8'))
    hRightGhostControl.putData(typecast(single([1.0 c_map(i,:) 0.6]),'uint8'))
    hRightSolid.putData(typecast(single(ang2),'uint8'))
    pause(0.02)
end

% fade out
for i = linspace(0.6,0.0,50)
    hRightGhostControl.putData(typecast(single([1.0 c_map(end,:) i]),'uint8'))
    pause(0.02)
end

