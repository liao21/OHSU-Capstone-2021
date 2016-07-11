classdef RemoveOffset < Inputs.Filter
    % RemoveOffset Filter object, extends filter object
    % Usage: hFilter = Inputs.RemoveOffset(numAvg);
    % Example: hFilter = Inputs.RemoveOffset(50);
    %
    % This filter simply computes the moving average of each channel 
    % and subtracts it, thus removing offset
    %
    % 05-Mar-2013 Armiger: Created
    methods
        function obj = RemoveOffset(windowSize)
            % Create Filters
            if nargin < 1
                windowSize = 50;
            end
            obj.Hb = ones(1,windowSize)/windowSize;
            obj.Ha = 1;
        end
        function filteredData = apply(obj,unfilteredData)
            %filteredData = apply(obj,unfilteredData)
            %
            % Apply filter based on the parameters specified Ha Hb
            %
            % Overloaded method since offset removal computes a mean and
            % does a manual subtraction
            %

            % user can specify multiple frequencies to filter (e.g. a notch
            % filter at [60, 120, 240] Hz
            numFilters = size(obj.Hb,1);
            
            % Check validity of saved filter state
            numChannels = size(unfilteredData,2);
            
            % Transient startup
            if isempty(obj.lastFilterState)
                obj.lastFilterState = cell(numFilters,1);
            end

            % Check filter state size
            for i = 1:numFilters
                if ~isequal(numChannels,size(obj.lastFilterState{i},2))
                    % Size mismatch, can't use previous data
                    obj.lastFilterState{i} = [];
                end
            end
            
            
            % Now apply filter

            % For a moving average filter, the filter is applied to get
            % the mean, then the computed mean is subtracted from the
            % signal
            movingAverage = filter(obj.Hb,obj.Ha,unfilteredData);
            
            filteredData = unfilteredData - movingAverage;
                        
        end
    end
end
