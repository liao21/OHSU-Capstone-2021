function [f, t] = createWaveform(dt, pulseWidth, pulseNum, pulseGap)

% handle args
if nargin < 2
    pulseWidth = 0.1;
end

if nargin < 3
    pulseNum = 1;
end

if nargin < 4
    pulseGap = pulseWidth;
end

% create the time vector
t = 0 : dt : (pulseNum * (pulseWidth + pulseGap));
f = zeros(size(t));

% set the waveform here
currTime = 0;
for pulseLoop = 1 : pulseNum 
    
    % turn on for pulseWidth
    f(t >= currTime & t < currTime + pulseWidth) = 1;
    
    % turn off for pulseGap
    f(t >= currTime + pulseWidth & t < currTime + pulseWidth + pulseGap) = 0;
    
    % update currTime
    currTime = currTime + pulseWidth + pulseGap;
end