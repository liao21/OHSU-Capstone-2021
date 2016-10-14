%%
[notfound,warnings] = loadlibrary('PPSDaq.dll','PPSDaq.h')

%%
configfile = 'fingertps-05bc.cfg'
calllib('PPSDaq','ppsInitialize',configfile)

%% Device should start to blink
calllib('PPSDaq','ppsStart')

%%
try
    RecordSize = calllib('PPSDaq','ppsGetRecordSize')
catch ME
    ME
end

%%
try
    framesReady = calllib('PPSDaq','ppsFramesReady')
catch ME
    ME
end
%%


try
    nFrames = int32(1);
    timeStampPtr = libpointer('ulongPtr',zeros(nFrames,1));
    dataPtr = libpointer('singlePtr',zeros(12,1));
        calllib('PPSDaq','ppsGetData',nFrames,timeStampPtr,dataPtr)
        b = get(dataPtr,'Value')
end

%%
try
    calllib('PPSDaq','ppsGetMaxSignal')
catch ME
    ME
end
%%
try
    calllib('PPSDaq','ppsStop')
catch ME
    ME
end
%%

unloadlibrary('PPSDaq')

