% Incomplete, get udp daata and plot
hP = LivePlot(8,200);


StartStopForm([])

while StartStopForm
    drawnow
    d = typecast(a.getData,'single');
    if ~isempty(d)
        hP.putdata(d)
    end
end


    