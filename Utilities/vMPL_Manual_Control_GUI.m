function varargout = vMPL_Manual_Control_GUI(varargin)
% VMPL_MANUAL_CONTROL_GUI MATLAB code for vMPL_Manual_Control_GUI.fig
%      VMPL_MANUAL_CONTROL_GUI, by itself, creates a new VMPL_MANUAL_CONTROL_GUI or raises the existing
%      singleton*.
%
%      H = VMPL_MANUAL_CONTROL_GUI returns the handle to a new VMPL_MANUAL_CONTROL_GUI or the handle to
%      the existing singleton*.
%
%      VMPL_MANUAL_CONTROL_GUI('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in VMPL_MANUAL_CONTROL_GUI.M with the given input arguments.
%
%      VMPL_MANUAL_CONTROL_GUI('Property','Value',...) creates a new VMPL_MANUAL_CONTROL_GUI or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before vMPL_Manual_Control_GUI_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to vMPL_Manual_Control_GUI_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help vMPL_Manual_Control_GUI

% Last Modified by GUIDE v2.5 08-Jun-2016 13:22:02

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @vMPL_Manual_Control_GUI_OpeningFcn, ...
                   'gui_OutputFcn',  @vMPL_Manual_Control_GUI_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before vMPL_Manual_Control_GUI is made visible.
function vMPL_Manual_Control_GUI_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to vMPL_Manual_Control_GUI (see VARARGIN)

% run driver program to generate base workspace
evalin('base', 'vMPL_Manual_Control_Driver;');

% set initial GUI slider positions to relative zeros
initial = evalin('base','initial');
set(handles.slider1, 'value', initial(1));
set(handles.slider3, 'value', initial(2));
set(handles.slider4, 'value', initial(3));
set(handles.slider5, 'value', initial(4));
set(handles.slider6, 'value', initial(5));
set(handles.slider7, 'value', initial(6));
set(handles.slider8, 'value', initial(7));

% Choose default command line output for vMPL_Manual_Control_GUI
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes vMPL_Manual_Control_GUI wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = vMPL_Manual_Control_GUI_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% set GUI to always on top
WinOnTop(hObject);

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on button press in pushbutton1.
function pushbutton1_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
evalin('base', 'handAngles = Tip;')
update_vMPL_joints();


% --- Executes on button press in pushbutton2.
function pushbutton2_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
evalin('base', 'handAngles = Cylindrical;')
update_vMPL_joints();

% --- Executes on slider movement.
function slider1_Callback(hObject, eventdata, handles)
% hObject    handle to slider1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(1) = get(hObject, 'Value')*evalin('base', 'range(1)') + evalin('base', 'offset(1)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();


% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on slider movement.
function slider3_Callback(hObject, eventdata, handles)
% hObject    handle to slider3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(2) = get(hObject, 'Value')*evalin('base', 'range(2)') + evalin('base', 'offset(2)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider3_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on slider movement.
function slider4_Callback(hObject, eventdata, handles)
% hObject    handle to slider4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(3) = get(hObject, 'Value')*evalin('base', 'range(3)') + evalin('base', 'offset(3)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider4_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on slider movement.
function slider5_Callback(hObject, eventdata, handles)
% hObject    handle to slider5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(4) = get(hObject, 'Value')*evalin('base', 'range(4)') + evalin('base', 'offset(4)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider5_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on slider movement.
function slider6_Callback(hObject, eventdata, handles)
% hObject    handle to slider6 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(5) = get(hObject, 'Value')*evalin('base', 'range(5)') + evalin('base', 'offset(5)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider6_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider6 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on slider movement.
function slider7_Callback(hObject, eventdata, handles)
% hObject    handle to slider7 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(6) = get(hObject, 'Value')*evalin('base', 'range(6)') + evalin('base', 'offset(6)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider7_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider7 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on slider movement.
function slider8_Callback(hObject, eventdata, handles)
% hObject    handle to slider8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

angle = evalin('base', 'upperArmAngles');
angle(7) = get(hObject, 'Value')*evalin('base', 'range(7)') + evalin('base', 'offset(7)');
assignin('base', 'upperArmAngles', angle);
update_vMPL_joints();

% Hints: get(hObject,'Value') returns position of slider
%        get(hObject,'Min') and get(hObject,'Max') to determine range of slider


% --- Executes during object creation, after setting all properties.
function slider8_CreateFcn(hObject, eventdata, handles)
% hObject    handle to slider8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: slider controls usually have a light gray background.
if isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor',[.9 .9 .9]);
end


% --- Executes on button press in pushbutton3.
function pushbutton3_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
evalin('base', 'handAngles = Lateral;')
update_vMPL_joints();


% --- Executes on selection change in popupmenu1.
function popupmenu1_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenu1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Determine the selected data set.
str = get(hObject, 'String');
val = get(hObject,'Value');
% Set current data to the selected data set.
switch str{val};
case 'Left Arm' % Control left arm of vMPL
    evalin('base', 'leftHand = true;');
    evalin('base', 'UdpDestinationPort = 25100;');
    evalin('base', 'hArm.close();');
    evalin('base', 'hArm = PnetClass(UdpLocalPort,UdpDestinationPort,UdpAddress) ');
    evalin('base', 'hArm.initialize();');
    %update_vMPL_joints();
    
case 'Right Arm' % Control right arm of vMPL
    evalin('base', 'leftHand = false;');
    evalin('base', 'UdpDestinationPort = 25000;');
    evalin('base', 'hArm.close();');
    evalin('base', 'hArm = PnetClass(UdpLocalPort,UdpDestinationPort,UdpAddress) ');
    evalin('base', 'hArm.initialize();');
    %update_vMPL_joints();
    
end
% Save the handles structure.
guidata(hObject,handles)

% Hints: contents = cellstr(get(hObject,'String')) returns popupmenu1 contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupmenu1


% --- Executes during object creation, after setting all properties.
function popupmenu1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupmenu1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in radiobutton1.
function radiobutton1_Callback(hObject, eventdata, handles)
% hObject    handle to radiobutton1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of radiobutton1


% --- Executes on button press in radiobutton2.
function radiobutton2_Callback(hObject, eventdata, handles)
% hObject    handle to radiobutton2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of radiobutton2


% --- Executes on button press in togglebutton1.
function togglebutton1_Callback(hObject, eventdata, handles)
% hObject    handle to togglebutton1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of togglebutton1


% --- Executes on button press in pushbutton4.
function pushbutton4_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
evalin('base', 'handAngles = zeros(1,20);')
update_vMPL_joints();

% --- Updates the current position of the vMPL based on the joint angles
function update_vMPL_joints()
evalin('base', 'msg = typecast(single([upperArmAngles,handAngles]),varType);');
evalin('base', 'hArm.putData(msg);');



% --- Executes during object deletion, before destroying properties.
function pushbutton4_DeleteFcn(hObject, eventdata, handles)
% hObject    handle to pushbutton4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)


% --- Executes when user attempts to close figure1.
function figure1_CloseRequestFcn(hObject, eventdata, handles)
% hObject    handle to figure1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

evalin('base', 'hArm.close();');

% Hint: delete(hObject) closes the figure
delete(hObject);


% --- Executes on button press in pushbutton5.
function pushbutton5_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% reset vMPL joint angles
evalin('base', 'handAngles = zeros(1,20);')
evalin('base', 'upperArmAngles = zeros(1,7);')

%set slider positions to zeros
initial = evalin('base','initial');
set(handles.slider1, 'value', initial(1));
set(handles.slider3, 'value', initial(2));
set(handles.slider4, 'value', initial(3));
set(handles.slider5, 'value', initial(4));
set(handles.slider6, 'value', initial(5));
set(handles.slider7, 'value', initial(6));
set(handles.slider8, 'value', initial(7));
update_vMPL_joints();
