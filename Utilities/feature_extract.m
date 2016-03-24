function features = feature_extract(windowData,windowSize,zc_thresh,ssc_thresh) %% codegen
% Extract time domain feature extraction function
% Note that this is not an exact copy of the previous methodology,
% but RSA tried and tested this code with minimal differences
% Inputs:
%   windowData - Buffer of windowed EMG data, typically 16x150
% Outputs:
%   features - [numChannels 4] matrix of features;
%       order: [MAV(:) LEN(:) ZC(:) SSC(:)]
%
% R. Armiger 07-July-2009: Revised to isolate feature extraction functionality only
%                  Signal magnitude will be extracted on a per classifier
%                  basis.  Also set to inherit class type and made
%                  windowSize tunable
% R. Armiger 30-Nov-2009: Updated to include thresholding on zero-crossing
%       and slope sign changes
% R. Armiger 09-Feb-2016: Vectorized code to improve speed:
%       Before: Elapsed time is 0.001198 seconds.
%       After:  Elapsed time is 0.000358 seconds.
%

%  Thresholds for computing zero crossing and slope sign change features

if nargin < 4
    ssc_thresh = 0.15;
end
if nargin < 3
    zc_thresh = 0.15;
end

[nChannels, nSamples] = size(windowData);

windowSize = max(windowSize,10);
windowSize = min(windowSize,nSamples);

% VAR = zeros(nChannels,1,myType);    % variance

%  Value to compute 'zero-crossing' around
t = 0.0;

%  Normalize features so they are independant of the window size
Fs = 1000;
n = windowSize;

idStart = (1+nSamples-windowSize);
y = windowData(1:nChannels,idStart:end)';

%  MAV shouldn't be normalized
MAV = mean( abs( y ) );

%  Curve length is the sum of the absolute value of the derivative of the
%  signal, normalized by the sample rate

LEN = sum( abs( diff(y) ) ) * Fs / n;


%  Criteria for crossing zero
%  zeroCross=(y[iSample] - t > 0 and y[iSample + 1] - t < 0) or (y[iSample] - t < 0 and y[iSample + 1] - t > 0)
%  overThreshold=abs(y[iSample] - t - y[iSample + 1] - t) > zc_thresh
%  if zeroCross and overThreshold:
%      %  Count a zero cross
%      ZC[iChannel]=ZC[iChannel] + 1

ZC = sum(...
    ((y(1:n-1,:) - t > 0) & (y(2:n,:) - t < 0) | ...
    (y(1:n-1,:) - t < 0) & (y(2:n,:) - t > 0)) & ...
    (abs(y(1:n-1,:) - t - y(2:n,:) - t) > zc_thresh) ...
    ) * Fs / n;


%  Criteria for counting slope sign changes
%  signChange = (y[iSample] > y[iSample - 1]) and (y[iSample] > y[iSample + 1]) or (y[iSample] < y[iSample - 1]) and (y[iSample] < y[iSample + 1])
%  overThreshold=abs(y[iSample] - y[iSample + 1]) > ssc_thresh or abs(y[iSample] - y[iSample - 1]) > ssc_thresh
%  if signChange and overThreshold:
%      %  Count a slope change
%      SSC[iChannel]=SSC[iChannel] + 1

SSC = sum( ...
    ((y(2:n-1,:) > y(1:n-2,:)) & (y(2:n-1,:) > y(3:n,:)) |  ...
    (y(2:n-1,:) < y(1:n-2,:)) & (y(2:n-1,:) < y(3:n,:))) &  ...
    ((abs(y(2:n-1,:) - y(3:n,:)) > ssc_thresh) | (abs(y(2:n-1,:) - y(1:n-2,:)) > ssc_thresh))...
    ) * Fs / n;

features = [MAV(:) LEN(:) ZC(:) SSC(:)];
