classdef DataCollector < handle
    properties
        DataSource
    end
    methods
        function attachSource(obj, source)
            % ATTACHSOURCE
            %
            % attachSource(obj, source)
            %
            % Attaches the given data source 
            
            if isempty(obj.DataSource)
                obj.DataSource = {source};
            else
                obj.DataSource = [obj.DataSource {source}];
            end
        end
        function data = getData(obj,varargin)
            % Call get data method for all sources and merge results
            
            data = [];
            
            for i = 1:length(obj.DataSource)
                
                ds = obj.DataSource{i};
                data = cat(2,ds.getData(varargin{:}));
                
            end
            
            
        end
    end
end
