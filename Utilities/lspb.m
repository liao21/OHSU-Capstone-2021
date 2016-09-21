% lspb.m - Linear Segments with Parabolic Blends
%
% Description: Computes LSPB to compute trajectory given sufficient initial
% conditions.
%
% Params: q0 = initial position
%         qf = final position
%          V = desired constant velocity during middle segment.
%         tf = final time (amount of time to complete trajectory)
%
% Output: qt = trajectory time series with joint angle position data
%
% Also, at the end of the script, qt will be plotted versus time.
%
% NOTE: Appropriate value for V must be given with relation to q0 and qf,
% otherwise, the trajectory will appear discontinuous.
%
% Example values: lspb(0, 40, 20, 3)
%                 lspb(0, 40, 60, 1)
%                 lspb(40, 80, 20, 1)  <-- error case
%
%
% Note the minimum time to complete an lspb move is:
%   (qf - q0) / V)
%
%
% Revisions:
%   2016Sept21 Armiger: Created

function qt = lspb(q0, qf, V, tf)

% check scaling since segment equations assume qf > q0, so just flip as
% needed
if qf < q0
    scale = -1;
    q0 = -q0;
    qf = -qf;
else
    scale = 1;
end

% assume t0 = 0 and tf > 0
dt = 0.02;
% define implicit time
t = 0:dt:tf;

if q0 == qf
    qt = qf*ones(size(t));
    t_1 = 0;
    t_3 = tf;
    qt_1 = qf;
    qt_3 = qf;
    
else
    % check that velocity is sufficient for motion
    assert( ((qf - q0) / V) < tf, ' insufficient time')
    
    % We will allow the user to go slower than velocity provided
    %assert( (2*(qf - q0) / V) >= tf, ' max velocity reached')
    if (2*(qf - q0) / V) <= tf
        V = 2*(qf - q0) / tf;
    end
    
    % qt is the time history trajectory for the motion
    % qf is the final destination value
    % alpha is
    % tf is the final time in seconds
    
    tb = (q0 - qf + V*tf) / V;
    alpha = V / tb;
    t_1 = t( t <= tb );
    t_2 = t( (tb < t) & (t <= (tf-tb) ) );
    t_3 = t( (tf-tb) < t);
    
    qt_1 = q0 + (0.5*alpha*t_1.^2);
    qt_2 = 0.5*(qf + q0 - V*tf) + V*t_2;
    qt_3 = qf - 0.5*alpha*tf^2 + alpha*tf*t_3 - (alpha/2)*t_3.^2;
    
    qt_1 = scale*qt_1;
    qt_2 = scale*qt_2;
    qt_3 = scale*qt_3;
    
    qt = cat(2,qt_1,qt_2,qt_3);
    
end

assert(length(t) == length(qt),'error creating trajectory')

% Plot trajectory
if nargout < 1
    plot(t, qt,'Marker','.');
    line(t_1(end), qt_1(end),'Color','r','Marker','o')
    line(t_3(1), qt_3(1),'Color','r','Marker','o')
    xlabel('Time (sec)');
    ylabel('Angle (deg)');
    set(gcf, 'Name', 'LPSB Plot');
end

return

%% Test Area: Use Cell Function Mode to execute and test values
q0 = 0;
qf = -40;
V = 50;
tf = 1;
lspb(q0,qf,V,tf);
