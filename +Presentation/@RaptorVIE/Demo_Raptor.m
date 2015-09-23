classdef RaptorVIE < handle
   
    
end


%% Load all the STL files
import Presentation.CytonI.*
pathName = '.';

pDistalMedium = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerDistalMedium-3.stl')));
pMiddle = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerDistalLong-1.stl')));
pRing = pDistalMedium;
pLittle = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerDistalShort-1.stl')));
pThumb = pDistalMedium;
pProximal = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-FingerProximal-5.stl')));
pPalm = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-Palm-1.stl')));
pWrist = Utils.stlMesh_to_patch(Utils.readStl(fullfile(pathName,'Left.Raptor-Gauntlet-1.stl')));

%% Render each of the segments
clf
hAxes = gca;
colorOrder = get(gca, 'ColorOrder');

hPatches(1) = patch(pWrist,'EdgeColor','none','FaceColor',colorOrder(1,:),'Parent',hAxes);
hPatches(2) = patch(pPalm,'EdgeColor','none','FaceColor',colorOrder(2,:),'Parent',hAxes);
hPatches(3) = patch(pProximal,'EdgeColor','none','FaceColor',colorOrder(3,:),'Parent',hAxes);
hPatches(4) = patch(pProximal,'EdgeColor','none','FaceColor',colorOrder(4,:),'Parent',hAxes);
hPatches(5) = patch(pProximal,'EdgeColor','none','FaceColor',colorOrder(5,:),'Parent',hAxes);
hPatches(6) = patch(pProximal,'EdgeColor','none','FaceColor',colorOrder(6,:),'Parent',hAxes);
hPatches(7) = patch(pProximal,'EdgeColor','none','FaceColor',colorOrder(7,:),'Parent',hAxes);
hPatches(8) = patch(pLittle,'EdgeColor','none','FaceColor',colorOrder(5,:),'Parent',hAxes);
hPatches(9) = patch(pDistalMedium,'EdgeColor','none','FaceColor',colorOrder(1,:),'Parent',hAxes);
hPatches(10) = patch(pMiddle,'EdgeColor','none','FaceColor',colorOrder(2,:),'Parent',hAxes);
hPatches(11) = patch(pDistalMedium,'EdgeColor','none','FaceColor',colorOrder(3,:),'Parent',hAxes);
hPatches(12) = patch(pDistalMedium,'EdgeColor','none','FaceColor',colorOrder(4,:),'Parent',hAxes);

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


%% Set offsets and motion variables
% writerObj = VideoWriter('raptor.avi');
% open(writerObj);
N = 40;
for v = [linspace(0,2,N) linspace(2,0,N)]
hGlobal.Matrix = makehgtform('xrotate',0.1)

hTransforms(1).Matrix = makehgtform('xrotate',0.2*v)
hTransforms(2).Matrix = makehgtform('Translate',[-44 111 -6],'xrotate',-0.3*v)
hTransforms(3).Matrix = makehgtform('Translate',[-15 111 -6],'xrotate',-0.2*v)
hTransforms(4).Matrix = makehgtform('Translate',[12 111 -6],'xrotate',-0.1*v)
hTransforms(5).Matrix = makehgtform('Translate',[41 111 -6],'xrotate',-0.0*v)
hTransforms(6).Matrix = makehgtform('Translate',[61 49 -8],'xrotate',deg2rad(15),'yrotate',deg2rad(15)*v,'zrotate',deg2rad(-95),...
    'Translate',[0 0 0])
hTransforms(7).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',0.3*v);
hTransforms(8).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',0.4*v);
hTransforms(9).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',0.5*v);
hTransforms(10).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',0.6*v);
hTransforms(11).Matrix = makehgtform('yrotate',pi,'Translate',[0 38 0],'xrotate',0.7*v);
drawnow

%     frame = getframe;
%    writeVideo(writerObj,frame);
end

% close(writerObj);

