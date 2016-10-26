function varargout = buttons_1to5(varargin)
% BUTTONS_1TO5 MATLAB code for buttons_1to5.fig
%      BUTTONS_1TO5, by itself, creates a new BUTTONS_1TO5 or raises the existing
%      singleton*.
%
%      H = BUTTONS_1TO5 returns the handle to a new BUTTONS_1TO5 or the handle to
%      the existing singleton*.
%
%      BUTTONS_1TO5('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in BUTTONS_1TO5.M with the given input arguments.
%
%      BUTTONS_1TO5('Property','Value',...) creates a new BUTTONS_1TO5 or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before buttons_1to5_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to buttons_1to5_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help buttons_1to5

% Last Modified by GUIDE v2.5 21-Oct-2016 09:35:09

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @buttons_1to5_OpeningFcn, ...
                   'gui_OutputFcn',  @buttons_1to5_OutputFcn, ...
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


% --- Executes just before buttons_1to5 is made visible.
function buttons_1to5_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to buttons_1to5 (see VARARGIN)

% Choose default command line output for buttons_1to5
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes buttons_1to5 wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = buttons_1to5_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on button press in button1.
function button1_Callback(hObject, eventdata, handles)
% hObject    handle to button1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of button1


% --- Executes on button press in button2.
function button2_Callback(hObject, eventdata, handles)
% hObject    handle to button2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of button2


% --- Executes on button press in button3.
function button3_Callback(hObject, eventdata, handles)
% hObject    handle to button3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of button3


% --- Executes on button press in button4.
function button4_Callback(hObject, eventdata, handles)
% hObject    handle to button4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of button4


% --- Executes on button press in button5.
function button5_Callback(hObject, eventdata, handles)
% hObject    handle to button5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of button5
