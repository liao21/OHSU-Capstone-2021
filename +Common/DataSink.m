classdef DataSink < hgsetget
    properties (Abstract = true) 
    end
    
    methods (Abstract) 
        putData(obj,jointData)
        close(obj) 
    end 
end
