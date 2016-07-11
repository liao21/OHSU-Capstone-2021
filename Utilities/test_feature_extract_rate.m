% Objective is to compare the feature extraction at different sample rates.
%  in both cases the desire is to extract 150 ms of data and extract
%  features.  Signal 1 is sampled at 1000Hz and Signal 2 at 300Hz.  Results
%  differ by as much as 20% for curve length.
%
% Additionally, simple upsampling via interp1 can cause additional
% variation as original peaks are not recovered and MAV declines on time
% resample.  'resample' function does a better job but is ~5x slower

% Test feature extract
% full rate signal:

windowTime = 0.150; % seconds

sampleRate1 = 1000;
f = 100;
t = linspace(0,1,sampleRate1);
s = sin(2*pi*f*t);
f1 = feature_extract(s,round(windowTime*sampleRate1),0,0,sampleRate1)

% reduced rate
sampleRate2 = 300;
t2 = linspace(0,1,sampleRate2);
s2 = sin(2*pi*f*t2);
f2 = feature_extract(s2,round(windowTime*sampleRate2),0,0,sampleRate2)

% upsampled
sampleRate3 = 1000;

t3 = interp1(1:length(t2),t2,linspace(1,length(t2),sampleRate3));

tic
s3 = interp1(1:length(t2),s2,linspace(1,length(t2),sampleRate3));
toc
% tic
% s3 = resample(s2,sampleRate3,sampleRate2);
% toc
f3 = feature_extract(s3,round(windowTime*sampleRate3),0,0,sampleRate3)

disp('Percentage Difference')
(f2-f1) ./ f1 * 100
(f3-f1) ./ f1 * 100

%%
clf
plot(t,s,'b.-')
hold on
plot(t2,s2,'ro-')
plot(t3,s3,'g*')
xlim([0 0.150])
%%
clf
plot(t(1:end-1),diff(s).*sampleRate1,'b.-')
hold on
plot(t2(1:end-1),diff(s2).*sampleRate2,'ro-')
xlim([0 0.150])
