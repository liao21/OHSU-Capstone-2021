classdef PptMaker < handle
    properties
        Title = '';
        Author = '';
        SubTitle = '';
        
        EnableTOC = 1;
        
        SlideNames = {};
        
        OutputFile = [tempname '.pptx'];
    end
    methods
        function initialize(obj)
            
            % Start new presentation
            isOpen  = exportToPPTX();
            if ~isempty(isOpen)
                % If PowerPoint already started, then close first and then open a new one
                exportToPPTX('close');
            end
            
            % Add title slide
            exportToPPTX('new','Title',obj.Title, ...
                'Author',obj.Author);
            exportToPPTX('addslide');
            if iscell(obj.SubTitle)
                subTitle = obj.SubTitle(:);
            else
                subTitle = {obj.SubTitle};
            end
            exportToPPTX('addtext',[{obj.Title}; {''}; subTitle], ...
                'VerticalAlignment','middle', ...
                'HorizontalAlignment','center', ...
                'FontSize',20);
            
            if obj.EnableTOC
                % Add TOC
                exportToPPTX('addslide');
                exportToPPTX('addtext','Table of Contents',...
                    'HorizontalAlignment','center');
            end
        end
        
        function addslide(obj,hFigs)
            
            if nargin < 2
                % get figure handles
                hFigs = flipud(findobj(0,'type','figure'));
            end
            
            % Add content
            for i = 1:length(hFigs)
                hFig = hFigs(i);
                hFig.Color = [1 1 1];
                obj.SlideNames = cat(1,obj.SlideNames,hFig.Name);
                
                exportToPPTX('addslide');
                exportToPPTX('addtext',hFig.Name); %,'Position','Title 1');
                exportToPPTX('addpicture',hFig,'Scale','maxfixed');
                
                if obj.EnableTOC
                    exportToPPTX('addtext','Table of Contents','Position',[1 7.25 8 0.25],...
                        'OnClick',2,'HorizontalAlignment','center','FontSize',10);
                end
            end
            
        end
        
        function addtable(obj,tdata,name,varargin)
            
            % Add content
            obj.SlideNames = cat(1,obj.SlideNames,name);
            
            exportToPPTX('addslide');
            exportToPPTX('addtext',name); %,'Position','Title 1');
            exportToPPTX('addtable',tdata,varargin{:});
            
        end
        
        
        function close(obj)
            
            if obj.EnableTOC
                % Add TOC
                exportToPPTX('switchslide',2);
                
                dy = 0.25;
                maxRows = 25;
                for iSlide = 1:size(obj.SlideNames,1)
                    i = mod(iSlide-1,maxRows);
                    j = floor((iSlide-1)/maxRows);
                    exportToPPTX('addtext',obj.SlideNames{iSlide},...
                        'OnClick',iSlide + 2, ...
                        'Position',[0.1+(5*j) (dy*i)+1 5 dy],...
                        'FontSize',10);
                end
            end
            
            % Check current presentation
            fileStats = exportToPPTX('query');
            if ~isempty(fileStats)
                fprintf('Presentation size: %f x %f\n',fileStats.dimensions);
                fprintf('Number of slides: %d\n',fileStats.numSlides);
            end
            
            % Save presentation -- overwrite file if it already exists
            % Filename automatically checked for proper extension
            try
                newFile = exportToPPTX('save',obj.OutputFile);
            catch ME
                reply = warndlg('Error writing PPT. Close file and retry.');
                uiwait(reply);
                newFile = exportToPPTX('save',obj.OutputFile);
            end
            
            % Close presentation
            exportToPPTX('close');
            
            fprintf('New file has been saved: <a href="matlab:winopen(''%s'')">%s</a>\n',newFile,newFile);
            
        end
    end
    methods (Static = true)
        function exportAllFigsPPT(pptTitle)
            % PptMaker.exportAllFigsPPT()
            % exportAllFigsPPT(pptTitle,templateFile)
            % Copy all open figures to PPT
            %
            
            % get figure handles
            hFigs = flipud(findobj(0,'type','figure'));
            
            hPpt = PptMaker;
            hPpt.Title = 'Title';
            hPpt.Author = 'Author';
            hPpt.SubTitle = 'Subtitle';
            hPpt.OutputFile = 'OutputFile';  % .pptx will be appended
            hPpt.initialize();
            
            %f = figure(255);
            %f.Position = [50 50 1600 900];
            
            % Add content
            for i = 1:length(hFigs)
                hPpt.addslide(hFigs(i));
            end
            hPpt.close();
        end
    end
end