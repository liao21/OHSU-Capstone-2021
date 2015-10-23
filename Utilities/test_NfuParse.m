load('C:\Users\VIE-MPL\Desktop\NFU Builds\2015OCT19\after2.mat','dataBytes')
% load('C:\Users\VIE-MPL\Desktop\NFU Builds\2015OCT19\before.mat','dataBytes')

numDataBytes = 1366;  % CPCH bytes

% sensor bytes
% old fomat 516 bytes
% new format 824 bytes

% read data and mark as new
b1 = dataBytes(1:numDataBytes);  %cpch bytes
[dataValues, sequenceNumber] = MPL.NfuUdp.cpch_bytes_to_signal(b1);

b2 = dataBytes(1+numDataBytes:end);  %percept bytes

sensorVals = MPL.NfuUdp.decode_percept_msg(b2);
sensorVals
