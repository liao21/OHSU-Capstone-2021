%% Setup
s = serial ('com15','Baudrate',57600);
fopen(s)

%% Activate selected tactor
vals = repmat(0,1,5);
tactorNum = 4;
vals(tactorNum) = 255
fwrite(s,sprintf('[%d,%d,%d,%d,%d]',vals))

%% All off
vals = repmat(0,1,5)
fwrite(s,sprintf('[%d,%d,%d,%d,%d]',vals))