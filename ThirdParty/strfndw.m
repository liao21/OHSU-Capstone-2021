function [idx] = strfndw(array, expStr, caseSensitive)
%% STRFNDW
%   Wild card selection from cell array of strings. It allows the use of 
%   wildcards '*' and '?' and returns only the matching element indexes of the cell 
%   array.
%
%   The '*' wildcard stands for any number (including zero) of characters.
%   The '?' wildcard stands for a single character.
%
%   Usage:
%       IDX = STRCMPW(ARRAY, EXPSTR, CASESENSITIVE) returns the index array, IDX,
%       containing the index number to the elements of ARRAY satisfying the
%       search criteria in EXPSTR
%
%   Example:
%       A = {'Hello world!'; 'Goodbye world!'; 'Goodbye everyone'};
%       idx = strcmpw(A, '*world!');
%
%    ans = [1;2]
%
%   Adapted for command line use from the WILDSEL GUI developed by
%   Richard Stephens (ristephens@theiet.org) v1.2 2007/03/01
%
% Revision History
%   1.00.[EO]2009.06.24 Converted to non-gui function from WILDSEL
%   2.00 Armiger: Escaped special characters and allowed optional case
%        restrictions

if nargin < 3
    % default is case insensitive, like the original function
    caseSensitive = false;
end

% Armiger Mod: 
% Release these characters so they are detected by regexp
modStr = expStr;
modStr = strrep(modStr,'.','\.');
modStr = strrep(modStr,'{','\{');
modStr = strrep(modStr,'}','\}');
modStr = strrep(modStr,'(','\(');
modStr = strrep(modStr,')','\)');
modStr = strrep(modStr,'+','\+');
modStr = strrep(modStr,'-','\-');
modStr = strrep(modStr,'$','\$');

regStr = ['^',strrep(strrep(modStr,'?','.'),'*','.{0,}'),'$'];

if caseSensitive
    starts = regexp(array, regStr);
else
    starts = regexpi(array, regStr);
end

iMatch = ~cellfun(@isempty, starts);
idx = find(iMatch);
