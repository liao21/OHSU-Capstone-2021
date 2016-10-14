%%
try
    [notfound,warnings] = loadlibrary('PPSDaq.dll','PPSDaq.h')
catch ME
    ME
end

%%

try
    copyfile('C:\usr\Bobby\RP2009\VRE\Common\SourcesAndSinks\@WirelessFingerTPS\fingertps-05bc.cfg','fingertps-05bc.cfg')
            copyfile('C:\usr\Bobby\RP2009\VRE\Common\SourcesAndSinks\@WirelessFingerTPS\fingertps_cal-05bc.txt','fingertps_cal-05bc.txt')
            copyfile('C:\usr\Bobby\RP2009\VRE\Common\SourcesAndSinks\@WirelessFingerTPS\fingertps_display-05bc.txt','fingertps_display-05bc.txt')
            copyfile('C:\usr\Bobby\RP2009\VRE\Common\SourcesAndSinks\@WirelessFingerTPS\fingertps_geometry-05bc.txt','fingertps_geometry-05bc.txt')
            copyfile('C:\usr\Bobby\RP2009\VRE\Common\SourcesAndSinks\@WirelessFingerTPS\fingertps_hw-05bc.txt','fingertps_hw-05bc.txt')
            copyfile('C:\usr\Bobby\RP2009\VRE\Common\SourcesAndSinks\@WirelessFingerTPS\fingertps_vertex-05bc.txt','fingertps_vertex-05bc.txt')

            
            
            configfile = 'fingertps-05bc.cfg'
            calllib('PPSDaq','ppsInitialize',configfile)
        
            delete('fingertps-05bc.cfg')
            delete('fingertps_cal-05bc.txt')
            delete('fingertps_display-05bc.txt')
            delete('fingertps_geometry-05bc.txt')
            delete('fingertps_hw-05bc.txt')
            delete('fingertps_vertex-05bc.txt')

         
    
    
%     
% %     cd C:\usr\Bobby\VRE\Common\SourcesAndSinks\WirelessFingerTPS\setup
%     configfile = 'fingertps-05bc.cfg'
% %     configfile = 'emulator.cfg'
%     calllib('PPSDaq','ppsInitialize',configfile)
%     cd ..
catch ME
    ME
end
%%
try
    calllib('PPSDaq','ppsStart')
catch ME
    ME
end

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
%     nFrames = RecordSize;% int32(1) *ones(1,1,'int32')
%     
%     timeStampPtr = libpointer('ulongPtr',zeros(nFrames,1,'int32'));
%     dataPtr = libpointer('singlePtr',zeros(nFrames,1));
%     calllib('PPSDaq','ppsGetData',nFrames,timeStampPtr,dataPtr)
%     b = get(dataPtr,'Value')
% %     c = get(timeStampPtr,'Value')

    nFrames = int32(1);    
    timeStampPtr = libpointer('ulongPtr',zeros(nFrames,1));
    dataPtr = libpointer('singlePtr',zeros(12,1));
    plotter = livePlot(12,100);
    
    while StartStopForm
        drawnow
    calllib('PPSDaq','ppsGetData',nFrames,timeStampPtr,dataPtr)
    b = get(dataPtr,'Value')
    plotter.putdata(b);
%     c = get(timeStampPtr,'Value')
    end


catch ME
    ME
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

