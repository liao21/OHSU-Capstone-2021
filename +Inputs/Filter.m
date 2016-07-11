classdef Filter < handle
    % Filter object base class
    % Filters, HighPass, LowPass, Notch should inherit from this class
    %
    % 01-Sept-2010 Armiger: Created
    % 08-Mar-2013 Armiger: Updated to maintain part of the signal in buffer to avoid filtering edge effects
    %   This method hasn't been verified yet and is implemented here, but disabled
    properties
        Hb
        Ha
        
        lastFilterState % store filter state to avoid filter edge effects
        
        % Use these parameters to reflect and invert the signal
        % before applying the filter.  This reduces
        % edge effects especially when the signal is
        % noisy about zero or has a DC offest
        ReflectOnApply = 0;
        ReflectValue = 0;
        
    end
    methods
        function filteredData = apply(obj,unfilteredData)
            %filteredData = apply(obj,unfilteredData)
            %
            % Apply filter based on the parameters specified Ha Hb
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
            
            
            % Typically, the filter is applied and filtered data is
            % returned
            
            % If multiple filters are contained (e.g. notch filters at
            % various frequencies, apply each filter
            filteredData = unfilteredData;
            
            if obj.ReflectOnApply
                % This approach effectivly rotates the signal 180 degrees
                % about the origin to minimize edge effects when applying
                % the lowpass filter
                %
                % The input signal is expected to be size [nSamples, nChannels]
                sIn = double(unfilteredData);
                
                nSamples = size(sIn,1);
                
                % Find the offset.
                % Note: this is currently disabled since the number of
                % samples for computing offset may vary.  This could be
                % made an input parameter but for now is left to the user
                % to apply an offset filter before applying the LPF
                %
                % sOffset = mean(sIn(1:200,:),1);
                sOffset = double(obj.ReflectValue);
                
                % Reverse and reflect
                sReflected = [flipud(-bsxfun(@minus,sIn,sOffset)); bsxfun(@minus,sIn,sOffset) ];
                
                % Apply filter (phase corrected)
                sFiltered = filtfilt(obj.Hb,obj.Ha,sReflected);
                
                % Shift back to original offset
                sOffset = bsxfun(@plus,sFiltered,sOffset);
                
                % Remove added data
                sOut = sOffset(nSamples+1:end,:);
                
                filteredData = sOut;
            else
                % Apply filter in the usual way
                for i = 1:numFilters
                    % save the filter state for the next iteration
                    [filteredData, obj.lastFilterState{i}] = ...
                        filter(obj.Hb(i,:),obj.Ha(i,:),filteredData,obj.lastFilterState{i});
                end
            end
            
            
        end
    end
end
