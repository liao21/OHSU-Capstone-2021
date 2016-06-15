classdef DataSource < hgsetget
    properties (Abstract = true) 
    end
    
    methods (Abstract) 
        data = getData(obj)
        close(obj) 
    end 
end
