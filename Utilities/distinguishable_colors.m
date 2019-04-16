function colors = distinguishable_colors(n_colors,varargin)
% Creates a wrapper around the MATLAB file exchange function
% distinguishable_colors, which requires the Image Processing Toolbox.
% Adding a catch block in case user is missing this toolbox with a few
% pre-stored color maps.
%
% Note the file exchage function does allow a custom mex file to be used as
% a color map to avoid the toolbox as well.
%
%Revisions:
% 4/14/2019 Armiger: Created

try
    colors = distinguishable_colors_file_exchange(n_colors,varargin{:});
catch ME
    warning(ME.message)
    if n_colors == 16
        colors = [
            0         0    1.0000
            1.0000         0         0
            0    1.0000         0
            0         0    0.1724
            1.0000    0.1034    0.7241
            1.0000    0.8276         0
            0    0.3448         0
            0.5172    0.5172    1.0000
            0.6207    0.3103    0.2759
            0    1.0000    0.7586
            0    0.5172    0.5862
            0         0    0.4828
            0.5862    0.8276    0.3103
            0.9655    0.6207    0.8621
            0.8276    0.0690    1.0000
            0.4828    0.1034    0.4138];
    elseif n_colors == 32
        colors = [
            0         0    1.0000
            1.0000         0         0
            0    1.0000         0
            0         0    0.1724
            1.0000    0.1034    0.7241
            1.0000    0.8276         0
            0    0.3448         0
            0.5172    0.5172    1.0000
            0.6207    0.3103    0.2759
            0    1.0000    0.7586
            0    0.5172    0.5862
            0         0    0.4828
            0.5862    0.8276    0.3103
            0.9655    0.6207    0.8621
            0.8276    0.0690    1.0000
            0.4828    0.1034    0.4138
            0.9655    0.0690    0.3793
            1.0000    0.7586    0.5172
            0.1379    0.1379    0.0345
            0.5517    0.6552    0.4828
            0.9655    0.5172    0.0345
            0.5172    0.4483         0
            0.4483    0.9655    1.0000
            0.6207    0.7586    1.0000
            0.4483    0.3793    0.4828
            0.6207         0         0
            0    0.3103    1.0000
            0    0.2759    0.5862
            0.8276    1.0000         0
            0.7241    0.3103    0.8276
            0.2414         0    0.1034
            0.9310    1.0000    0.6897];
    elseif n_colors == 15
        colors = [
            0         0    1.0000
            1.0000         0         0
            0    1.0000         0
            0         0    0.1724
            1.0000    0.1034    0.7241
            1.0000    0.8276         0
            0    0.3448         0
            0.5172    0.5172    1.0000
            0.6207    0.3103    0.2759
            0    1.0000    0.7586
            0    0.5172    0.5862
            0         0    0.4828
            0.5862    0.8276    0.3103
            0.9655    0.6207    0.8621
            0.8276    0.0690    1.0000];
    else
        colors = rand(n_colors,3);
    end
end
