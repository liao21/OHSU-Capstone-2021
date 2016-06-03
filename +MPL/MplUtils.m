classdef MplUtils
    methods (Static = true)        
        function wait_for_ping_response()
            % Function blocks until a successful ping from the specified device
            
            ipRouter = UserConfig.getUserConfigVar('mplRouterIp','192.168.1.1');
            ipArm = UserConfig.getUserConfigVar('mplNfuIp','192.168.1.111');
            
            fprintf('Trying to connect to Router @ %s and MPL @ %s ...\n',ipRouter,ipArm);
            
            pingOk = false;
            
            while ~pingOk
                % ping router
                strPing = sprintf('!ping %s -n 1',ipRouter);
                strSuccess = sprintf('Reply from %s: bytes=32',ipRouter);
                response = evalc(strPing);
                foundId = strfind(response,strSuccess);
                routerOk = ~isempty(foundId);
                if routerOk
                    routerStatus = 'OK';
                else
                    routerStatus = 'FAILED';
                end
                
                strPing = sprintf('!ping %s -n 1',ipArm);
                strSuccess = sprintf('Reply from %s: bytes=32',ipArm);
                response = evalc(strPing);
                foundId = strfind(response,strSuccess);
                mplOk = ~isempty(foundId);
                if mplOk
                    mplStatus = 'OK';
                else
                    mplStatus = 'FAILED';
                end
                
                fprintf('Router Ping @ %s = %s; MPL Ping @ %s = %s\n',ipRouter,routerStatus,ipArm,mplStatus);
                
                pingOk = routerOk & mplOk;
                
            end % while
        end % wait_for_ping_response
    end
end