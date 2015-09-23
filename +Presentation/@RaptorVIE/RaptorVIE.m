classdef RaptorVIE < handle
    % Class object for creating and moving a virtual 3d printed hand
    %Presentation.RaptorVIE
    %
    %
    % Revisions:
    % 23SEP2015 Armiger: Initial Revision
    
    properties
        
        enableTriads = 1
        enableSurfaces = 1
        
        patchData
        
        hPatches
        hTransforms
        hTriads
        
    end
    
    methods
        function initialize(obj)
            
            obj.patchData = loadStl();
            [obj.hPatches, obj.hTransforms, obj.hTriads] = initDisplay(obj.patchData);
            
            % set initial offsets
            update(obj,zeros(11,1))
            
        end
        function update(obj,handAnglesDegrees,baseAngles)
            % set joint angles independantly (degrees)
            %
            % 1 - Wrist Flex
            % 2 - LittleProx
            % 3 - RingProx
            % 4 - MiddleProx
            % 5 - IndexProx
            % 6 - ThumbProx
            % 7 - LittleDist
            % 8 - RingDist
            % 9 - MiddleDist
            % 10 - IndexDist
            % 11 - ThumbDist
            
            if nargin < 3
                baseAngles = zeros(3,1);
            end
            
            
            %update hand angles
            angles = handAnglesDegrees * pi/180;
            
            obj.hTransforms(1).Matrix = makehgtform('xrotate',angles(1));
            obj.hTransforms(2).Matrix = makehgtform('Translate',[-44 111 -6],'xrotate',angles(2));
            obj.hTransforms(3).Matrix = makehgtform('Translate',[-15 111 -6],'xrotate',angles(3));
            obj.hTransforms(4).Matrix = makehgtform('Translate',[12 111 -6],'xrotate',angles(4));
            obj.hTransforms(5).Matrix = makehgtform('Translate',[41 111 -6],'xrotate',angles(5));
            obj.hTransforms(6).Matrix = makehgtform('Translate',[61 49 -8],'xrotate',deg2rad(15),'yrotate',angles(6),'zrotate',deg2rad(-95),...
                'Translate',[0 0 0]);
            obj.hTransforms(7).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',angles(7));
            obj.hTransforms(8).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',angles(8));
            obj.hTransforms(9).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',angles(9));
            obj.hTransforms(10).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',angles(10));
            obj.hTransforms(11).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',angles(11));
            
            % update base angles
            p = baseAngles * pi / 180;
            obj.hTransforms(12).Matrix = makehgtform(...
                'zrotate',p(3),...
                'yrotate',p(2),...
                'xrotate',p(1)) * makehgtform('zrotate',-pi/2);

            
            % update display
            if obj.enableTriads
                set(obj.hTriads,'Visible','on');
            else
                set(obj.hTriads,'Visible','off');
            end
            
            if obj.enableSurfaces
                set(obj.hPatches,'Visible','on');
            else
                set(obj.hPatches,'Visible','off');
            end
            
            drawnow
            
        end
    end
    methods (Static = true)
        function obj = TestMotion(movieFile)
            %Presentation.RaptorVIE.TestMotion
            % create a demo movie or render motion onscreen
            
            obj = Presentation.RaptorVIE;
            obj.initialize;
            
            if nargin < 1
                movieFile = [];
            end
            
            % Set offsets and motion variables
            if ~isempty(movieFile)
                writerObj = VideoWriter(movieFile);
                open(writerObj);
            end
            
            N = 40;
            
            for v = [linspace(0,2,N) linspace(2,0,N)]
                
                obj.update(v.*[15 -20 -10 -5 -5 10 20 25 30 35 40])
                
                obj.hTransforms(12).Matrix = makehgtform('xrotate',0.1);
            
                if ~isempty(movieFile)
                    frame = getframe;
                    writeVideo(writerObj,frame);
                end
            end
            
            if ~isempty(movieFile)
                close(writerObj);
            end
            
        end
        function obj = TestMyo()
            %Presentation.RaptorVIE.TestMyo
            % create a demo movie or render motino onscreen
            
            obj = Presentation.RaptorVIE;
            obj.initialize;
            
            hMyo = Inputs.MyoUdp.getInstance;
            hMyo.initialize;
            
            hMyo.update
            hMyo.Orientation
            
            %%
            obj.enableTriads = 0;
            StartStopForm([])
            while StartStopForm
                drawnow
                
                hMyo.update
                p = hMyo.Orientation(:,end);
                obj.update(zeros(11,1),p)
                disp(p)
                
            end
        end
    end
end

function p = loadStl()

% Load all the STL files
import Presentation.CytonI.*
pathName = fileparts(which('Presentation.RaptorVIE'));

p.DistalMedium = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerDistalMedium-3.stl')));
p.DistalLong = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerDistalLong-1.stl')));
p.DistalShort = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerDistalShort-1.stl')));
p.Proximal = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerProximal-5.stl')));
p.Palm = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-Palm-1.stl')));
p.Wrist = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-Gauntlet-1.stl')));

end


function [hPatches, hTransforms, hTriads] = initDisplay(p)
%% Render each of the segments
import Presentation.CytonI.*

clf
hAxes = gca;
colorOrder = get(gca, 'ColorOrder');

hPatches(1) = patch(p.Wrist,'EdgeColor','none','FaceColor',colorOrder(1,:),'Parent',hAxes);
hPatches(2) = patch(p.Palm,'EdgeColor','none','FaceColor',colorOrder(2,:),'Parent',hAxes);
hPatches(3) = patch(p.Proximal,'EdgeColor','none','FaceColor',colorOrder(3,:),'Parent',hAxes);
hPatches(4) = patch(p.Proximal,'EdgeColor','none','FaceColor',colorOrder(4,:),'Parent',hAxes);
hPatches(5) = patch(p.Proximal,'EdgeColor','none','FaceColor',colorOrder(5,:),'Parent',hAxes);
hPatches(6) = patch(p.Proximal,'EdgeColor','none','FaceColor',colorOrder(6,:),'Parent',hAxes);
hPatches(7) = patch(p.Proximal,'EdgeColor','none','FaceColor',colorOrder(7,:),'Parent',hAxes);
hPatches(8) = patch(p.DistalShort,'EdgeColor','none','FaceColor',colorOrder(5,:),'Parent',hAxes);
hPatches(9) = patch(p.DistalMedium,'EdgeColor','none','FaceColor',colorOrder(1,:),'Parent',hAxes);
hPatches(10) = patch(p.DistalLong,'EdgeColor','none','FaceColor',colorOrder(2,:),'Parent',hAxes);
hPatches(11) = patch(p.DistalMedium,'EdgeColor','none','FaceColor',colorOrder(3,:),'Parent',hAxes);
hPatches(12) = patch(p.DistalMedium,'EdgeColor','none','FaceColor',colorOrder(4,:),'Parent',hAxes);

% Create reference triads
nPatches = 12;
nTransforms = 12;

triadScale = 50;
hTriads = zeros(1,nTransforms);
for i = 1:nTransforms
    hTriads(i) = Utils.plot_triad(hAxes,eye(4),triadScale);
end

% Create parent transform
hGlobal = hgtransform('Parent',hAxes);

% Create transforms between relative segments
hTransforms(1) = hgtransform('Parent',hGlobal);
hTransforms(2) = hgtransform('Parent',hTransforms(1));
hTransforms(3) = hgtransform('Parent',hTransforms(1));
hTransforms(4) = hgtransform('Parent',hTransforms(1));
hTransforms(5) = hgtransform('Parent',hTransforms(1));
hTransforms(6) = hgtransform('Parent',hTransforms(1));
hTransforms(7) = hgtransform('Parent',hTransforms(2));
hTransforms(8) = hgtransform('Parent',hTransforms(3));
hTransforms(9) = hgtransform('Parent',hTransforms(4));
hTransforms(10) = hgtransform('Parent',hTransforms(5));
hTransforms(11) = hgtransform('Parent',hTransforms(6));

hTransforms(12) = hGlobal;

% map each patch to its parent transform
set(hPatches(1),'Parent',hGlobal);
set(hPatches(2),'Parent',hTransforms(1));
set(hPatches(3),'Parent',hTransforms(2));
set(hPatches(4),'Parent',hTransforms(3));
set(hPatches(5),'Parent',hTransforms(4));
set(hPatches(6),'Parent',hTransforms(5));
set(hPatches(7),'Parent',hTransforms(6));
set(hPatches(8),'Parent',hTransforms(7));
set(hPatches(9),'Parent',hTransforms(8));
set(hPatches(10),'Parent',hTransforms(9));
set(hPatches(11),'Parent',hTransforms(10));
set(hPatches(12),'Parent',hTransforms(11));

% map each triad to its parent transform
set(hTriads(2),'Parent',hTransforms(1));
set(hTriads(3),'Parent',hTransforms(2));
set(hTriads(4),'Parent',hTransforms(3));
set(hTriads(5),'Parent',hTransforms(4));
set(hTriads(6),'Parent',hTransforms(5));
set(hTriads(7),'Parent',hTransforms(6));
set(hTriads(8),'Parent',hTransforms(7));
set(hTriads(9),'Parent',hTransforms(8));
set(hTriads(10),'Parent',hTransforms(9));
set(hTriads(11),'Parent',hTransforms(10));
set(hTriads(12),'Parent',hTransforms(11));


view(50,40)
axis equal tight
camlight

end
