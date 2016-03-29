classdef DataEmitter < handle
    % Data emitter is a container class for attaching various output
    % modules allowing limb commands to go to multiple destinations
    %
    % 28Mar2016 Armiger: Created
    properties (SetAccess = 'protected')
        sinks = [];
    end
    
    methods
        function obj = DataEmitter()
            % DATAEMITTER
            % DataEmitter constructor.
            obj.sinks = [];
        end
        
        function attachSink(obj, sink)
            % Pass in a handle to a data sink module and it will be added
            % to the list of outputs.
            
            % Check a couple things before attaching a sink:
            if ~isa(sink,'Common.DataSink')
                error('Valid Sinks must be a derivitive of the DataSink class (mySink < Common.DataSink)');
            end
            
            if isempty(obj.sinks)
                obj.sinks = {sink};
            else
                for i = 1:length(obj.sinks)
                    %             if strcmp(get(dataEmitter.sinks{i}, 'id'), get(sink, 'id') )
                    %                 disp('Sink already attached:')
                    %                 display(sink)
                    %                 return
                    %             end
                end
                obj.sinks = [obj.sinks {sink}];
            end
        end
        
        function putData(dataEmitter, jointAngles, jointVelocities)
            % PUTDATA
            %
            % putdata(dataEmitter, jointAngles, jointVelocities)
            %
            % Calls putdata() on all attached sinks.
            
            userProvidedVelocities = (nargin == 3);
            
            if isempty(dataEmitter.sinks)
                return
            end
            
            for iSink = 1:length(dataEmitter.sinks)
                % RSA: Found bug where if you don't make a local variable copy
                % of the Emitter, the putdata method gets confused and tries to
                % access class properties of other sinks within the DataEmitter
                % container.
                hSink = dataEmitter.sinks{iSink};
                if userProvidedVelocities
                    putData(hSink, jointAngles, jointVelocities)
                else
                    putData(hSink, jointAngles);
                end
            end
        end %putData
    end
end
