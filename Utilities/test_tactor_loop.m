comPort = 'COM8';
lowVal = 0;
highVal = 200;

commandVals = zeros(1,5);
s = instrfind('port',comPort);
if isempty(s)
    s = serial(comPort,'Baudrate',57600,'Timeout',0.5,'Terminator',0);
    fprintf('Opening port %s...',comPort)
    fopen(s);
    fprintf('Done\n');
end

id = 0;
StartStopForm([])
while StartStopForm
id = id + 1;
if id > 5
    id = 1;
end
newVals = zeros(1,5) + lowVal;
newVals(id) = highVal;

commandVals = newVals;
fprintf(s,'[%d,%d,%d,%d,%d]',commandVals);
nBytes = s.BytesAvailable;
if nBytes > 0
    c = char(fread(s,nBytes,'char')');
    disp(c)
end

fprintf('Tactor %d\n',id)
pause(0.05)
end
%%

commandVals(:) = 0;

fprintf(s,'[%d,%d,%d,%d,%d]',commandVals);
pause(0.1)
nBytes = s.BytesAvailable;
if nBytes > 0
    c = char(fread(s,nBytes,'char')');
    disp(c)
end
