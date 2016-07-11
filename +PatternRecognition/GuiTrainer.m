classdef GuiTrainer < PatternRecognition.TrainingInterfaceBase
    % This is a gui front end for handling real time training.  The user
    % can use the mouse and ui controls to select a target class and add /
    % clear data.  This GUI only generates Events that must be subscribed
    % to by the actual retraining object.  
    %
    % Similarly, the GUI subscribes to notifications from the
    % TrainingManager in order to keep the GUI current with the latest
    % class and data counts
    %         addlistener(hTrainingSource,'DataCountChange',@(src,evt)obj.update() );
    
    properties
        TrainingManager    % Handle to Training Data Manager to receive events
        SelectionIndex = 1;
        Images          % cell array of class images

        hg              % handle graphics   
        hListenData         % handle to event listeners
        hListenClass         % handle to event listeners
    end
    methods
        function initialize(obj, TrainingManager)
            % Setup GUI and event handlers 
            
            obj.Verbose = 1;
            
            obj.TrainingManager = TrainingManager;
            % Subscribe to changes in the data set that will be updated on
            % the GUI
            obj.hListenData = addlistener(obj.TrainingManager,'DataCountChange',@(src,evt) eventDataCountChange(obj,src,evt) );
            obj.hListenClass = addlistener(obj.TrainingManager,'CurrentClass',@(src,evt) eventCurrentClass(obj,src,evt) );

            obj.loadClassImages();
            
            ClassNames = obj.TrainingManager.getClassNames;
            obj.SelectionIndex = length(ClassNames);
            
            % Setup the Display
            obj.hg.Figure = UiTools.create_figure('User Driven Training Interface','uiTrainTag');
            
            pos = get(obj.hg.Figure,'Position');
            pos(3) = 1.3*pos(3);
            pos(4) = 1.1*pos(4);
            set(obj.hg.Figure,'Position',pos)
            set(obj.hg.Figure,'CloseRequestFcn',@(src,evt) obj.close() )
            
            obj.hg.hSelection = uicontrol('Parent',obj.hg.Figure,'Style','listbox',...
                'Units','Normalized','Value',obj.SelectionIndex,...
                'Position',[0.01 0.1 0.296 0.88],'Callback',@(src,evt)cbChangedClass(obj));
            set(obj.hg.hSelection,'String',ClassNames);
            set(obj.hg.hSelection,'FontSize',14);
            
            obj.hg.hAdd = uicontrol('Parent',obj.hg.Figure,'Style','togglebutton',...
                'Units','Normalized',...
                'Position',[0.05 0.01 0.1 0.088],...
                'String','Add',...
                'Callback',@(src,evt) cbAdd(obj) );
            obj.hg.hClear = uicontrol('Parent',obj.hg.Figure,'Style','pushbutton',...
                'Units','Normalized',...
                'Position',[0.16 0.01 0.1 0.088],...
                'String','Clear',...
                'Callback',@(src,evt) notify(obj,'ClearClass') );
            
            obj.hg.ImAxes = axes('Parent',obj.hg.Figure,'Units','Normalized',...
                'Position',[0.35 0.125 0.6 0.8]);
            obj.hg.StatusAxes = axes('Parent',obj.hg.Figure,'Units','Normalized',...
                'Position',[0.35 0.06 0.6 0.12]);
            obj.hg.StatusBar = rectangle('Position',[0.05,0.05,1,0.9],...
                ...'Curvature',[0.8,0.4],...
                'LineWidth',2,'LineStyle','-','FaceColor','r','Parent',obj.hg.StatusAxes);
            
%             % trigger a change class event with the current settings
%             obj.setDisplay();
            
            % notify the UI's current class
            obj.cbChangedClass()
            
        end
        function update(obj)
            if isempty(obj.hg.Figure)
                return
            end
            
            % Update the sample count progress bar
            labelCounts = max(1,obj.TrainingManager.getClassLabelCount());
            cnt = labelCounts(obj.SelectionIndex);
            
            set(obj.hg.StatusBar,'Position',[0.05 0.05 cnt 0.9])
            if cnt < 50
                set(obj.hg.StatusBar,'FaceColor','r')
            elseif cnt < 200
                set(obj.hg.StatusBar,'FaceColor','y')
            else
                set(obj.hg.StatusBar,'FaceColor','g')
            end
            ylim(obj.hg.StatusAxes,[0 1]);
            set(obj.hg.StatusAxes,'YTick',[]);
            maxNum = 200;
            if cnt < maxNum
                xlim(obj.hg.StatusAxes,[0 maxNum]);
            else
                xlim(obj.hg.StatusAxes,'auto');
            end
        end
        function setDisplay(obj)
            if isempty(obj.hg.Figure)
                return
            end
            
            i = obj.SelectionIndex;
            
            classNames = obj.TrainingManager.getClassNames;
            
            currentClass = classNames{i};
            
            set(obj.hg.hSelection,'Value',obj.SelectionIndex);
            % Prevent changing class while adding data
            if get(obj.hg.hAdd,'Value')
                set(obj.hg.hSelection,'Enable','off');
            else
                set(obj.hg.hSelection,'Enable','on');
            end
            
            % Get the image (RGB) and display
            im = obj.Images{i};
            
            %     % Flip the image manually and display using normal xy axis
            %     % since on release R2013 this led to inverted axis labels
            %     imFlip = im;
            %     for i = 1:size(imFlip,3)
            %         % flip each dimension
            %         imFlip(:,:,i) = flipud(imFlip(:,:,i));
            %     end
            % 
            %     % show image
            %     image(imFlip,'Parent',obj.hg.ImAxes);
            %     axis(obj.hg.ImAxes,'xy')
            %     axis(obj.hg.ImAxes,'off')
            %     daspect(obj.hg.ImAxes,[1 1 1]);

            imshow(im,'Parent',obj.hg.ImAxes)

            update(obj);
            
            h = title(currentClass,'Parent',obj.hg.ImAxes);
            set(h,'FontSize',18)
        end
        
        function loadClassImages(obj)
            % on startup load all class images
            classNames = obj.TrainingManager.getClassNames();
            numClasses = length(classNames);
            
            % picture path
            pathstr = fileparts(which('PatternRecognition.SimpleTrainer'));
            pathImages = fullfile(pathstr,'Images');
            
            for iClass = 1:numClasses
                className = classNames{iClass};
                
                % first assume classname equals the filename
                structDir = dir(fullfile(pathImages,[className '.*']));
                if length(structDir) == 1
                    fileName = fullfile(pathImages,structDir(1).name);
                else
                    % check manual mapping to filename
                    % TODO abstract this into an xml or otherwise
                    switch className
                        case 'Humeral Internal Rotation'
                            imgName = 'shoulder(humeral) rotation in.jpg';
                        case 'Humeral External Rotation'
                            imgName = 'shoulder(humeral) rotation out.jpg';
                        case 'Elbow Flexion'
                            imgName = 'elbow flexion.jpg';
                        case 'Elbow Extension'
                            imgName = 'elbow extension.jpg';
                        case 'Wrist Rotate In'
                            imgName = 'wrist pronation.jpg';
                        case 'Wrist Rotate Out'
                            imgName = 'wrist supination.jpg';
                        case 'Wrist Flex In'
                            imgName = 'wrist flexion.jpg';
                        case 'Wrist Extend Out'
                            imgName = 'wrist extension.jpg';
                        case {'Up','Hand Up', 'Radial Deviation','Wrist Abduction'}
                            imgName = 'wrist abduction.jpg';
                        case {'Down','Hand Down', 'Ulnar Deviation','Wrist Adduction'}
                            imgName = 'wrist adduction.jpg';
                        case 'Hand Open'
                            imgName = 'hand open.jpg';
                        case 'Lateral Grasp'
                            imgName = 'lateral grip.jpg';
                        case 'Cylindrical Grasp'
                            imgName = 'cylindrical grip.jpg';
                        case 'Tip Grasp'
                            imgName = 'fine pinch grip.jpg';
                        case 'Hook Grasp'
                            imgName = 'hook grip.jpg';
                        case 'Spherical Grasp'
                            imgName = 'power grip mode.jpg';
                        case 'Pointer Grasp'
                            imgName = 'point grip.jpg';
                        case 'No Movement'
                            imgName = 'no movement (rest).jpg';
                        case {'Index' 'Index Grasp'}
                            imgName = 'IndexFinger.png';
                        case {'Middle' 'Middle Grasp'}
                            imgName = 'MiddleFinger.png';
                        case {'Ring' 'Ring Grasp'}
                            imgName = 'RingFinger.png';
                        case {'Little' 'Little Grasp'}
                            imgName = 'LittleFinger.png';
                        case {'Thumb' 'Thumb Grasp'}
                            imgName = 'ThumbFinger.png';
                        otherwise
                            fprintf('Unmatched class: "%s"\n',className);
                            imgName = '';
                    end
                    
                    fileName = fullfile(pathImages,imgName);
                end
                
                if exist(fileName,'file') ~= 2
                    fprintf('Image failed: "%s\n"',fileName);
                    obj.Images{iClass} = [];
                else
                    img = imread(fileName);
                    obj.Images{iClass} = img;
                end
            end
        end
        function close(obj)
            % close figure
            if ishandle(obj.hg.Figure)
                delete(obj.hg.Figure);
                obj.hg.Figure = [];
            end
            
            delete(obj.hListenData);
            obj.hListenData = [];
            
            delete(obj.hListenClass);
            obj.hListenClass = [];
        end
    end
    methods (Access = 'private')
        function cbChangedClass(obj)
            % Callback for selecting a new class from the list box
            obj.SelectionIndex = get(obj.hg.hSelection,'Value');

            ClassNames = obj.TrainingManager.getClassNames;
            evtdata = PatternRecognition.ChangeClassEventData(...
                obj.SelectionIndex,ClassNames{obj.SelectionIndex});
            notify(obj,'ClassChange',evtdata);
            
            obj.setDisplay();
        end
        function cbAdd(obj)
            % Toggle button callback
            if get(obj.hg.hAdd,'Value')
                set(obj.hg.hAdd,'String','Stop')
                % it's important to send the class name since if multiple
                % interfaces are connected a single start might trigger
                % adding data to the wrong class
                ClassNames = obj.TrainingManager.getClassNames;
                evtdata = PatternRecognition.ChangeClassEventData(...
                    obj.SelectionIndex,ClassNames{obj.SelectionIndex});
                notify(obj,'ClassChange',evtdata);

                notify(obj, 'StartAdd')
            else
                set(obj.hg.hAdd,'String','Add')
                notify(obj, 'StopAdd')
                notify(obj, 'ForceRetrain')
            end
            
            setDisplay(obj)
        end
        function eventCurrentClass(obj,src,evt)
            % change the class based on input from the GUI.  The changed
            % value can be read from the event source
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
            
            obj.SelectionIndex = evt.NewClassId;
            obj.setDisplay();
            
        end
        function eventDataCountChange(obj,src,evt)
            % change the class based on input from the GUI.  The changed
            % value can be read from the event source
            
            if obj.Verbose
                fprintf('[%s] Got "%s" event from %s interface\n',...
                    mfilename, evt.EventName, class(src));
            end
        end
    end
    methods (Static = true)
        function Test
            %%
            % PatternRecognition.GuiTrainer.Test()
            
            hManager = PatternRecognition.TrainingManager.Test;
            
            hInterface = PatternRecognition.GuiTrainer();
            
            hManager.attachInterface(hInterface);
            hInterface.initialize(hManager);
            

            % class changes are UI event driven
            % Add data will require update function to get new data
            hManager.update();
            
            StartStopForm([]);
            while StartStopForm()
                pause(0.02);
                hManager.update();
            end
            
        end
    end % (Static = true)
end
