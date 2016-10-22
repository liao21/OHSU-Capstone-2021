
h = LivePlot(8,200);
nPackets = 0;
cellPackets = a.getAllData;
tic
StartStopForm([]);
while StartStopForm
    drawnow
    cellPackets = a.getAllData;
    
    for i = 1:length(cellPackets)
        bytes = cellPackets{i};
        d = double(typecast(bytes,'int8'));
        h.putdata(d(1:8) + 200*(1:8) );
        h.putdata(d(9:16) + 200*(1:8) );
        nPackets = nPackets + 2;
    end
    
end
t = toc;
fprintf('%d packets received in %f seconds : %f Hz\n',nPackets,t,nPackets/t);
