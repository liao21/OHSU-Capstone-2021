classdef guiRocEditor < handle
    % GUI for manually setting joint angles via sliders for Roc Tables
    %
    % This allows you to load, edit, save, and visualize changes in
    % real-time with vulcanX for the vMPL or MPL.
    % TODO: Still have a lot of features to add like copy paste insert
    % remove, etc but for minor tweaks due to sensor drift this should work.
    %
    % Usage:
    %
    % %setup
    % MiniVIE.configurePath
    % import GUIs.*
    %
    % %run
    % guiRocEditor
    %
    %
    % 07NOV2013 Armiger: Created
    % 16JUN2016 Samson: Added +/- ROC and Waypoint
    properties
        hDataEmitter = Common.DataEmitter;  % handle to the data output sinks (udp)
        hMud = MPL.MudCommandEncoder;       % handle for the message encoder
        hParent;        % Figure
        
        structRoc;                          % structure for storing the current roc table
        
        CurrentFilename = 'NEW_ROC.xml';
        IsDirty = 0;
        
        % All Ids are 1 based since this is matlab
        CurrentRocId = 1;
        CurrentWaypointId = 1;
        
        NumOpenSteps = 100;
        NumCloseSteps = 100;
        
        CommsHold = 1; % controlled by toggle to delay communications with limb until released
        
        Verbose = 0;
    end
    properties  (SetObservable)
        jointAngles = zeros(1,27);
    end
    properties (Access = 'protected')
        hAxes;          % Array of axes for sliders
        
        % roc related gui handles
        hJointSliders;
        hRocSpinBox;
        hRocWaypoints;
        hRocDescription;
        hRocNames;
        hAngleBox;
        jSpinnerModel;
        
    end
    methods
        function obj = guiRocEditor(rocFilename)
            % obj = guiRocEditor(rocFilename)
            %
            % Creator Function takes an optional argument to specify the
            % current roc filename to begin with.
            
            if nargin < 1
                rocFilename = [];
            end
            
            obj.createFigure();
            
            if isempty(rocFilename)
                obj.structRoc = MPL.RocTable.createRocTables();
            else
                obj.structRoc = MPL.RocTable.readRocTable(rocFilename);
                obj.CurrentFilename = rocFilename;
            end
            
            % Set Roc Names Listbox after creating the ROC Tables
            set(obj.hRocNames,'String',{obj.structRoc.name})
            
            obj.updateFigure();
        end
        function createFigure(obj,hParent,nSliders)
            if nargin < 2
                hParent = default_figure;
                set(hParent,'CloseRequestFcn',@(src,evt)obj.close());
            end
            if nargin < 3
                nSliders = 27;
            end
            
            obj.hParent = hParent;
            
            nSlidersPerRow = 9;
            parentPos = get(obj.hParent,'Position');
            xPos = linspace(20,parentPos(3)-50,nSlidersPerRow);
            axesWidth = 40;
            axesHeight = 150;
            
            axesRange = repmat([-pi pi],nSliders,1);
            sliderRange = axesRange;
            
            sliderTitle = fieldnames(MPL.EnumArm);
            hAx = zeros(nSliders,1);
            
            patchWidth = (axesRange(:,2) - axesRange(:,1))/15;
            
            % take the total number of sliders and divide by the number
            % of siders per row.  the remainder gives the column
            % position and the quotient gives the row number
            numRows = floor(nSliders/nSlidersPerRow);
            numCols = rem(nSliders,nSlidersPerRow); %#ok<NASGU>
            
            for i = 1:nSliders
                iRow = floor((i-1)/nSlidersPerRow);
                iCol = rem(i-1,nSlidersPerRow);
                hAx(i) = axes(...
                    'Parent',hParent,...
                    'XLim',[0 1],'XTick',[],...
                    'XTickLabelMode','manual',...
                    'YTickLabelMode','manual',...
                    'YMinorTick','on',...
                    'LineWidth',1,...
                    'TickDir','out',...
                    'TickLength',[.05 .1],...
                    'Units','Pixels',...
                    'Position',[xPos(iCol+1) 180*(numRows-iRow-1)+20 axesWidth axesHeight]);
                t(i) = text('Parent',hAx(i),...
                    'Position',[0.5 0],...
                    'String',sliderTitle{i},...
                    'Rotation',90,...
                    'FontWeight','Bold',...
                    'Interpreter','None',...
                    'HorizontalAlignment','center');
                
                % title(hAx(i),sliderTitle{i},'Interpreter','None');
                obj.hJointSliders{i} = GUIs.widgetSlider(...
                    'Parent',hAx(i),...
                    'Type',{'Vertical'},...
                    'PatchWidth',patchWidth(i),...
                    'ButtonMotionFcn',@(src,evnt) set_position(src,evnt,obj,i),...
                    'ButtonUpFcn',@(src,evnt) set_position(src,evnt,obj,i),...
                    'Range',sliderRange(i,:));
                set(hAx(i),'YTick',[axesRange(i,1) 0 axesRange(i,2)]);
                set(hAx(i),'YLim',axesRange(i,:))
            end
            
            obj.hAxes = hAx;
            
            % Add menus
            set(hParent,'Menubar','None');
            menuFile = uimenu(hParent,'Label','&File');
            menuFileOpen = uimenu(menuFile,'Label','Open...','Callback',@(src,evt)uiOpen(obj));
            menuFileSave = uimenu(menuFile,'Label','Save As...','Callback',@(src,evt)uiSaveAs(obj));
            
            % unimplemented menu items to edit ROC names and Waypoint values
            %menuEdit = uimenu(hParent,'Label','&Edit');
            %menuEditRenameROC = uimenu(menuEdit,'Label','Rename ROC','Callback',@(src,evt)uiRenameROC(obj));
            %menuFileSetWaypoint = uimenu(menuEdit,'Label','Set Waypoint','Callback',@(src,evt)uiSetWaypoint(obj));
            
            menuOutput = uimenu(hParent,'Label','&Output');
            menuOutputUnity = uimenu(menuOutput,'Label','Unity');
            uimenu(menuOutputUnity,'Label','Left Arm','Callback',@cbSetOutput);
            uimenu(menuOutputUnity,'Label','Right Arm','Callback',@cbSetOutput);
            uimenu(menuOutputUnity,'Label','Custom','Callback',@cbSetOutput);
            
            menuOutputVulcanX = uimenu(menuOutput,'Label','VulcanX');
            uimenu(menuOutputVulcanX,'Label','Left Arm','Callback',@cbSetOutput);
            uimenu(menuOutputVulcanX,'Label','Right Arm','Callback',@cbSetOutput);
            uimenu(menuOutputVulcanX,'Label','Custom','Callback',@cbSetOutput);
            
            %MPL-NFU
            menuOutputMplNfu = uimenu(menuOutput,'Label','MPL-NFU');
            uimenu(menuOutputMplNfu,'Label','Left Arm','Callback',@cbSetOutput);
            uimenu(menuOutputMplNfu,'Label','Right Arm','Callback',@cbSetOutput);
            uimenu(menuOutputMplNfu,'Label','Custom','Callback',@cbSetOutput);
            
            % Roc ID Spinner Label
            uicontrol(hParent,'Style','text','Position',[10 620, 60, 20],...
                'String','RocID:','HorizontalAlignment','Left');
            
            % Roc ID Spinner
            numRocs = 1;  % needs to be updated when new roc added
            % ref: http://undocumentedmatlab.com/blog/using-spinners-in-matlab-gui/
            %obj.jSpinnerModel = javax.swing.SpinnerNumberModel(0,0,numRocs,1);
            obj.jSpinnerModel = javaObjectEDT(javax.swing.SpinnerNumberModel(0,0,numRocs,1));
            jSpinner = javax.swing.JSpinner(obj.jSpinnerModel);
            jhSpinner = javacomponent(jSpinner, [10,600,40,20], hParent);
            jhSpinner.StateChangedCallback = @(src,evt)cbSpinner(src);
            
            % Test Button
            uicontrol(hParent,'Style','pushbutton','Position',[10 570, 80, 20],...
                'String','Test Close','HorizontalAlignment','Left','Callback',@(src,evt)cbTestClose);
            uicontrol(hParent,'Style','pushbutton','Position',[10 550, 80, 20],...
                'String','Test Open','HorizontalAlignment','Left','Callback',@(src,evt)cbTestOpen);
            
            % Roc Names Label
            uicontrol(hParent,'Style','text','Position',[100 620, 80, 20],...
                'String','Roc Names:','HorizontalAlignment','Left');
            
            % Add/Delete ROC
            uicontrol(hParent,'Style','pushbutton','Position',[260 620, 20, 20],'TooltipString','Insert Copy of Current ROC',...
                'String','+','HorizontalAlignment','Left','Callback',@(src,evt)cbAddROC);
            uicontrol(hParent,'Style','pushbutton','Position',[280 620, 20, 20],'TooltipString','Delete Current ROC',...
                'String','-','HorizontalAlignment','Left','Callback',@(src,evt)cbDeleteROC);
            
            % Roc Names Listbox
            obj.hRocNames = uicontrol(hParent,'Style','listbox','Position',[100 555, 200, 65],...
                'String',{'-empty-'},'Callback',@(src,evt)cbListBoxName(src));
            
            % Roc Waypoint Label
            uicontrol(hParent,'Style','text','Position',[320 620, 80, 20],...
                'String','RocWaypoint:','HorizontalAlignment','Left');
            
            % Add/Delete Waypoint
            uicontrol(hParent,'Style','pushbutton','Position',[400 620, 20, 20],'TooltipString','Insert Copy of Current Waypoint',...
                'String','+','HorizontalAlignment','Left','Callback',@(src,evt)cbAddWaypoint);
            uicontrol(hParent,'Style','pushbutton','Position',[420 620, 20, 20],'TooltipString','Delete Current Waypoint',...
                'String','-','HorizontalAlignment','Left','Callback',@(src,evt)cbDeleteWaypoint);
            
            % Roc Waypoint Listbox
            obj.hRocWaypoints = uicontrol(hParent,'Style','listbox','Position',[320 555, 120, 65],...
                'String',{'0.0' '0.5' '1.0'},'Callback',@(src,evt)cbListBox(src));
            
            % Angles Label
            uicontrol(hParent,'Style','text','Position',[460 620, 120, 20],...
                'String','Angle Values (deg):','HorizontalAlignment','Left');
            
            % Angles Text Box
            obj.hAngleBox = uicontrol(hParent,'Style','edit','Max',2,'Position',[460 540, 500, 80],...
                'horizontalalignment','left');
            
            % Set Angles Button
            uicontrol(hParent,'Style','pushbutton','Position',[600 620, 80, 20],...
                'String','Set Angles','HorizontalAlignment','Left','Callback',@(src,evt)cbSetAngles);
            
            % HOLD Button
            uicontrol(hParent,'Style','togglebutton','Value',1,'Position',[700 620, 80, 20],...
                'String','HOLD','HorizontalAlignment','Left','Callback',@(src,evt)cbHold(src));
            
            % Rename ROC Name text box
            uicontrol(hParent,'Style','edit','Position',[100 540, 200, 16],'HorizontalAlignment','left',...
                'TooltipString','Rename Current ROC...','Callback',@(src,evt)cbEditRocName(src));
            
            % Edit Waypoint text box
            uicontrol(hParent,'Style','edit','Position',[320 540, 120, 16],'HorizontalAlignment','left',...
                'TooltipString','Edit Waypoint Value...','Callback',@(src,evt)cbEditWaypoint(src));
            
            obj.IsDirty = false;
            
            return
            
            function cbSetOutput(src,~)
                
                % determine whether to add or remove base on checked
                if strcmp(get(src,'Checked'),'off')
                    set(src,'Checked','on')
                    
                else
                    %set(src,'Checked','off')
                    warning('sink removal not implemented')
                    return
                end
                
                % Get Text labels
                parentLabel = get(get(src,'Parent'),'Label');
                armLabel = get(src,'Label');
                
                % Determine source
                switch parentLabel
                    
                    case 'Unity'
                        hSink = MPL.MplUnitySink();
                        hSink.setPortDefaults( strcmp(armLabel,'Left Arm') );
                        hSink.initialize();
                    case 'VulcanX'
                        hSink = MPL.MplVulcanXSink();
                        hSink.setPortDefaults( strcmp(armLabel,'Left Arm') );
                        hSink.initialize();
                    case 'MPL-NFU'
                        hSink = MPL.MplNfuSink();
                        hSink.initialize();
                    otherwise
                        errordlg('Unmatched Output Module');
                        return
                end
                
                obj.attachSink(hSink);
                
            end
            
            function cbSpinner(src)
                obj.CurrentRocId = src.Value+1;
                obj.CurrentWaypointId = 1;
                obj.updateFigure();
            end
            
            function cbListBox(src)
                obj.CurrentWaypointId = get(src,'Value');
                obj.updateFigure();
            end
            
            function cbHold(src)
                obj.CommsHold = get(src,'Value');
                obj.updateFigure();
            end
            
            function cbSetAngles()
                obj.IsDirty = true;
                
                oldAngles = obj.jointAngles;
                newAngles = textscan(get(obj.hAngleBox,'String'),'%f,');
                newAngles = newAngles{1}'*pi/180;
                % set sliders
                setSliders(obj,oldAngles,newAngles)
                
                % update the internal roc table in memory
                rocId = obj.CurrentRocId;
                waypointId = obj.CurrentWaypointId;
                nROCAngles = length(obj.structRoc(rocId).angles(waypointId,:));
                nNewAngles = length(newAngles);
                obj.structRoc(rocId).angles(waypointId,:) = newAngles((nNewAngles-nROCAngles+1):end);
                display('Joint angles set')
                
                obj.updateFigure();
            end
            
            function cbListBoxName(src)
                obj.CurrentRocId = get(src,'Value');
                obj.CurrentWaypointId = 1;
                obj.updateFigure();
            end
            
            function cbTestCloseOpen()
                
                cbTestClose;
                pause(0.2)
                cbTestOpen;
                
            end
            function cbTestOpen()
                
                idx = obj.CurrentRocId;
                thisRoc = obj.structRoc(idx);
                RocId = thisRoc.id;
                RocName = thisRoc.name;
                
                rocVal = linspace(1,0,obj.NumOpenSteps);
                for iVal = 1:length(rocVal)
                    fprintf('Entry #%d, RocId=%d, %14s %6.2f Pct\n',...
                        idx,RocId,RocName,rocVal(iVal)*100);
                    
                    allAngles = zeros(1,27);
                    allAngles(thisRoc.joints) = interp1(thisRoc.waypoint,thisRoc.angles,rocVal(iVal));
                    obj.jointAngles = allAngles;
                    obj.transmit();
                    
                    pause(0.02);
                    %drawnow
                end
                
            end
            function cbTestClose()
                
                idx = obj.CurrentRocId;
                thisRoc = obj.structRoc(idx);
                RocId = thisRoc.id;
                RocName = thisRoc.name;
                
                rocVal = linspace(0,1, obj.NumCloseSteps);
                for iVal = 1:length(rocVal)
                    fprintf('Entry #%d, RocId=%d, %14s %6.2f Pct\n',...
                        idx,RocId,RocName,rocVal(iVal)*100);
                    
                    allAngles = zeros(1,27);
                    allAngles(thisRoc.joints) = interp1(thisRoc.waypoint,thisRoc.angles,rocVal(iVal));
                    obj.jointAngles = allAngles;
                    obj.transmit();
                    
                    pause(0.02);
                end
                
            end
            
            function cbAddROC
                % TO-DO: need to add ability name a new ROC
                idx = obj.CurrentRocId;
                struct = obj.structRoc
                
                % insert copy of current ROC below current
                obj.structRoc = [struct(1:idx) struct(idx:length(struct))];
                
                resetRocIDs();
                obj.updateFigure();
            end
            
            function cbDeleteROC
                % TO-DO: add warning for deleting a ROC
                idx = obj.CurrentRocId;
                struct = obj.structRoc
                % element to delete is not first or last
                if (idx < length(struct) && idx > 1)
                    obj.structRoc = [struct(1:idx-1) struct(idx+1:length(struct))];
                    % element to delete is first
                elseif (idx == 1 && length(struct) ~= 1)
                    obj.structRoc = struct(idx+1:length(struct));
                    % element to delete is last
                elseif (idx == length(struct) && length(struct) ~= 1)
                    obj.structRoc = struct(1:length(struct)-1)
                    obj.CurrentRocId = obj.CurrentRocId -1;
                    % element to delete is the only element
                elseif (length(struct) == 1)
                    obj.structRoc(1).name = 'NewROC';
                    obj.structRoc(1).waypoint = [0];
                    obj.structRoc(1).angles = zeros(1,length(struct.joints));
                    obj.structRoc(1).impedance = zeros(1,length(struct.joints))-1;
                end
                
                resetRocIDs();
                obj.updateFigure();
                
            end
            
            function cbAddWaypoint
                % TO-DO: add ability to set waypoint time
                idx = obj.CurrentRocId;
                idw = obj.CurrentWaypointId;
                waypt = obj.structRoc(idx).waypoint;
                angs = obj.structRoc(idx).angles;
                imps = obj.structRoc(idx).impedance;
                
                % insert copy of current waypoint below current
                obj.structRoc(idx).waypoint = [waypt(1:idw) waypt(idw:length(waypt))];
                obj.structRoc(idx).angles = [angs(1:idw, 1:size(angs,2)); angs(idw:size(angs,1), 1:size(angs,2))];
                obj.structRoc(idx).impedance = [imps(1:idw, 1:size(imps,2)); imps(idw:size(imps,1), 1:size(imps,2))];
                
                obj.updateFigure();
            end
            
            function cbDeleteWaypoint
                % TO-DO: add warning for deleting a waypoint
                idx = obj.CurrentRocId;
                idw = obj.CurrentWaypointId;
                waypt = obj.structRoc(idx).waypoint;
                angs = obj.structRoc(idx).angles;
                imps = obj.structRoc(idx).impedance;
                
                % element to delete is not first or last
                if (idw < length(waypt) && idw > 1)
                    obj.structRoc(idx).waypoint = [waypt(1:idw-1) waypt(idw+1:length(waypt))];
                    obj.structRoc(idx).angles = [angs(1:idw-1, 1:size(angs,2)); angs(idw+1:size(angs,1), 1:size(angs,2))];
                    obj.structRoc(idx).impedance = [imps(1:idw-1, 1:size(imps,2)); imps(idw+1:size(imps,1), 1:size(imps,2))];
                    % element to delete is first
                elseif (idw == 1 && length(waypt) ~= 1)
                    obj.structRoc(idx).waypoint = waypt(idw+1:length(waypt));
                    obj.structRoc(idx).angles = angs(idw+1:size(angs,1), 1:size(angs,2));
                    obj.structRoc(idx).impedance = imps(idw+1:size(imps,1), 1:size(imps,2));
                    % element to delete is last
                elseif (idw == length(waypt) && length(waypt) ~= 1)
                    obj.structRoc(idx).waypoint = waypt(1:length(waypt)-1);
                    obj.structRoc(idx).angles = angs(1:idw-1, 1:size(angs,2));
                    obj.structRoc(idx).impedance = imps(1:idw-1, 1:size(imps,2));
                    obj.CurrentWaypointId = obj.CurrentWaypointId -1;
                    % element to delete is the only element
                elseif (length(waypt) == 1)
                    obj.structRoc(idx).waypoint = [0];
                    obj.structRoc(idx).angles = zeros(1,length(obj.structRoc(1).joints));
                    obj.structRoc(idx).impedance = zeros(1,length(obj.structRoc(1).joints))-1;
                end
                
                obj.updateFigure();
            end
            
            function cbEditRocName(src)
                idx = obj.CurrentRocId;
                idw = obj.CurrentWaypointId;
                str = get(src,'string');
                set(src,'string','');
                if (~isempty(str) && isstrprop(str(1),'alpha'))
                    obj.structRoc(idx).name = str;
                else
                    errordlg('Name should start with a letter');
                    return
                end
                
                obj.updateFigure();
            end
            
            function cbEditWaypoint(src)
                idx = obj.CurrentRocId;
                idw = obj.CurrentWaypointId;
                newVal = str2double(get(src,'string'));
                set(src,'string','');
                
                if (~isnan(newVal) && newVal >= 0 && newVal <= 1)
                    obj.structRoc(idx).waypoint(idw) = newVal;
                else
                    errordlg('Invalid input. Waypoints must be a value from 0 to 1');
                    return
                end
                
                obj.updateFigure();
            end
            
            function resetRocIDs
                for (idx = 1:length(obj.structRoc))
                    obj.structRoc(idx).id = idx-1;
                end
            end
            
        end
        function ang = getdata(obj)
            ang = obj.jointAngles;
        end
        function attachSink(obj,hSink)
            % Attach a new output (sink) to the module
            obj.hDataEmitter.attachSink(hSink)
        end
        function updateFigure(obj,idCurrent)
            
            % if the user is driving one slider, don't try to update it
            if nargin < 2
                idCurrent = -1;
            end
            
            rocId = obj.CurrentRocId;
            waypointId = obj.CurrentWaypointId;
            
            roc = obj.structRoc(rocId);
            
            % set roc names list box
            set(obj.hRocNames,'String',{obj.structRoc(:).name})
            set(obj.hRocNames,...
                'Value',rocId);
            
            % set roc waypoints list box
            set(obj.hRocWaypoints,...
                'String',cellfun(@num2str,num2cell(roc.waypoint),'UniformOutput',false),...
                'Value',waypointId);
            
            % set spinner
            set(obj.jSpinnerModel,...
                'Maximum',length(obj.structRoc)-1,...
                'Value',rocId-1); %zero based
            
            % Set sliders
            currentAngles = obj.jointAngles;
            
            finalAngles = currentAngles;
            for i = 1:length(roc.joints)
                
                
                iJoint = roc.joints(i);
                newAngle = roc.angles(waypointId,i);
                if i ~= idCurrent
                    set(obj.hJointSliders{iJoint},'Value',newAngle);
                end
                finalAngles(iJoint) = newAngle;
            end
            
            % move the limb using interpolation to ensure movements are
            % smooth.  the number of steps is based on the error between
            % the current position and the final desired position
            
            % interpolate
            maxDiff = max(abs(finalAngles - currentAngles));
            
            numSteps = floor(maxDiff / 0.05);
            
            fprintf('%Interpolating %d steps\n',numSteps);
            for i = 1:numSteps
                interpAngles = interp1([0 1],[currentAngles; finalAngles],i/numSteps);
                obj.jointAngles = interpAngles;
                transmit(obj);
                pause(0.02);
            end
            
            % resend final values
            obj.jointAngles = finalAngles;
            transmit(obj);
            
            % set angle text box
            setAngleTextBox(obj)
            
            % Update figure title
            if obj.IsDirty
                figTitle = sprintf('JHU/APL: Reduced Order Control (ROC) Editor - %s*',obj.CurrentFilename);
            else
                figTitle = sprintf('JHU/APL: Reduced Order Control (ROC) Editor - %s',obj.CurrentFilename);
            end
            if ishandle(obj.hParent) && isa(obj.hParent,'matlab.ui.Figure')
                set(obj.hParent,'Name',figTitle)
            end
            
        end
        
        function setAngleTextBox(obj)
            angleTextBox = sprintf('%+ 6.1f, ',obj.jointAngles*180/pi);
            set(obj.hAngleBox, 'String',angleTextBox(1:end-2),'FontName','Courier');
        end
        
        function setSliders(obj,oldAngles,newAngles)
            
            currentAngles = oldAngles;
            
            finalAngles = zeros(1,length(obj.hJointSliders));
            for i = 1:length(obj.hJointSliders)
                newAngle = newAngles(i);
                set(obj.hJointSliders{i},'Value',newAngle);
                finalAngles(i) = newAngle;
            end
            
            % interpolate
            maxDiff = max(abs(finalAngles - currentAngles));
            
            numSteps = floor(maxDiff / 0.05);
            
            for i = 1:numSteps
                interpAngles = interp1([0 1],[currentAngles; finalAngles],i/numSteps);
                obj.jointAngles = interpAngles;
                transmit(obj);
                pause(0.02);
            end
            
            % resend final values
            obj.jointAngles = finalAngles;
            transmit(obj);
        end
        
        function uiOpen(obj)
            [fileName, pathName, filterIndex] = uigetfile('*.xml');
            if filterIndex == 0
                %User Cancelled
                return
            end
            
            xmlFileName = fullfile(pathName,fileName);
            
            obj.structRoc = MPL.RocTable.readRocTable(xmlFileName);
            obj.updateFigure();
        end
        function success = uiSaveAs(obj)
            % Interactively save file
            success = false;
            
            [fileName, pathName, filterIndex] = uiputfile('*.xml',...
                'Select ROC File to Write',obj.CurrentFilename);
            if filterIndex == 0
                %User Cancelled
                return
            end
            
            xmlFileName = fullfile(pathName,fileName);
            
            MPL.RocTable.writeRocTable(xmlFileName,obj.structRoc);
            
            obj.IsDirty = false;
            obj.updateFigure()
            
            success = true;
            
        end
        
        function set.jointAngles(obj,value)
            obj.jointAngles = value;
            
            % slow down the transmit rate when moving sliders
            if delay_send(30)
                return
            else
                transmit(obj);
                
                angleTextBox = sprintf('%+ 6.1f, ',obj.jointAngles*180/pi);
                set(obj.hAngleBox, 'String',angleTextBox(1:end-2),'FontName','Courier');
            end
            
        end
        function transmit(obj)
            if obj.Verbose
                fprintf('Joint Command:');
                fprintf(' %6.3f',obj.jointAngles);
                fprintf('\n');
            end
            
            if obj.CommsHold
                fprintf('Comms on hold\n');
                return
            end
            
            obj.hDataEmitter.putData(obj.jointAngles);
            
        end
        function close(obj)
            % Check for unsaved changes before closing
            if obj.IsDirty
                reply = questdlg('Do you want to save changes to the ROC table?','Unsaved Changes','Save','Don''t Save','Cancel','Save');
                switch reply
                    case 'Save'
                        success = uiSaveAs(obj);
                        if ~success
                            return
                        end
                    case 'Don''t Save'
                        % Do nothing and exit
                    otherwise
                        return
                end
            end
            
            for iSink = length(obj.hDataEmitter.sinks):-1:1
                hSink = obj.hDataEmitter.sinks{iSink};
                hSink.close();
                obj.hDataEmitter.removeSink(hSink);
            end
            
            
            %close(obj.hAxes);
            delete(obj.hParent)
            obj.hAxes = [];
        end
    end
end

%Callbacks
function set_position(src,evnt,obj,i) %#ok<INUSL>

newAngle = get(src,'Value');
m = MPL.EnumArm;

indexGroup = [m.INDEX_MCP m.INDEX_DIP m.INDEX_PIP];
middleGroup = [m.MIDDLE_MCP m.MIDDLE_DIP m.MIDDLE_PIP];
ringGroup = [m.RING_MCP m.RING_DIP m.RING_PIP];
littleGroup = [m.LITTLE_MCP m.LITTLE_DIP m.LITTLE_PIP];

if ismember(i,indexGroup)
    idGroup = indexGroup;
    newAngle = [newAngle 0.45.*([newAngle newAngle])];
elseif ismember(i,middleGroup)
    idGroup = middleGroup;
    newAngle = [newAngle 0.45.*([newAngle newAngle])];
elseif ismember(i,ringGroup)
    idGroup = ringGroup;
    newAngle = [newAngle 0.45.*([newAngle newAngle])];
elseif ismember(i,littleGroup)
    idGroup = littleGroup;
    newAngle = [newAngle 0.45.*([newAngle newAngle])];
else
    idGroup = i;
end

% Update joint angles for transmission
obj.jointAngles(idGroup) = newAngle;

% update the internal roc table in memory
rocId = obj.CurrentRocId;
waypointId = obj.CurrentWaypointId;

[~,id] = intersect(obj.structRoc(rocId).joints,idGroup);
if ~isempty(id)
    % update ROC table
    obj.structRoc(rocId).angles(waypointId,id) = newAngle;
    obj.IsDirty = true;
end

obj.updateFigure(i)

end

% Helper
function isDelayed = delay_send(Hz)
persistent tLastSent

if isempty(tLastSent)
    tLastSent = clock;
    isDelayed = 0;
    return
end

if etime(clock,tLastSent) < 1/Hz
    isDelayed = 1;
else
    tLastSent = clock;
    isDelayed = 0;
end

end

function hFig = default_figure()

hFig = UiTools.create_figure('JHU/APL: Reduced Order Control (ROC) Editor','guiRocEditor');

% return monitor positions, secondary monitors are in each row
mp = get(0, 'MonitorPositions');

topLeft = [mp(1,1) mp(1,4)-mp(1,2)];
windowSize = [1000 650];

set(hFig,...
    'Units','pixels',...
    'Position',[topLeft(1)+10 topLeft(2)-windowSize(2)-50 windowSize]);
end
