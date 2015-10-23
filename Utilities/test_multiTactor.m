% Device Name = RNBT-DE3D
%'Passkey = 1234'
%
% Tested 10/19/2015 Armiger, Carroll

s = serial ('com15','Baudrate',57600);
fopen(s);
fwrite(s,uint8(sprintf('[%d,%d,%d,%d,%d]',repmat(128,1,5))))
fwrite(s,uint8(sprintf('[%d,%d,%d,%d,%d]',repmat(255,1,5))))
fwrite(s,uint8(sprintf('[%d,%d,%d,%d,%d]',repmat(0,1,5))))
