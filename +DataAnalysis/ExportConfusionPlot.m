function ExportConfusionPlot(hTraining, outputFile)

%Plot all results on seperate figures

close all
for i = 1:length(hTraining);
    hClassifier = SignalAnalysis.Lda;
    hClassifier.initialize(hTraining(i));
    output = hClassifier.train;
    if isempty(output)
        continue
    end
    testName = hTraining(i).Name;

    f = figure(i);
    set(f,'Units','pixels')
    set(f,'ToolBar','figure')
    p = get(f,'Position');
    p = [p(1) p(2)/2 800 720];
    set(f,'Position',p);
    clf(f)
    hAxes = axes('Parent',f);
    
    hClassifier.plotConfusion(hAxes);
    t = {sprintf('Actual versus predicted class, Avg = %4.1f %%',100*hClassifier.computeError) ...
        testName };
    title(t,'Parent',hAxes,'Interpreter','None');
    drawnow
end

%% Copy figures to PPT

% Start new presentation
isOpen  = exportToPPTX();
if ~isempty(isOpen),
    % If PowerPoint already started, then close first and then open a new one
    exportToPPTX('close');
end

t = sprintf('Training Data Confusion %s',datestr(now));
exportToPPTX('new','Title',t, ...
    'Author','RSA');
exportToPPTX('addslide');
exportToPPTX('addtext',{t,'',which(mfilename)}, ...
    'VerticalAlignment','middle', ...
    'HorizontalAlignment','center', ...
    'FontSize',20);

for i = 1:length(findobj(0,'type','figure'))
    slideNum = exportToPPTX('addslide');
    exportToPPTX('addpicture',figure(i),'Scale','maxfixed');
end

% Check current presentation
fileStats   = exportToPPTX('query');
if ~isempty(fileStats),
    fprintf('Presentation size: %f x %f\n',fileStats.dimensions);
    fprintf('Number of slides: %d\n',fileStats.numSlides);
end

% Save presentation -- overwrite file if it already exists
% Filename automatically checked for proper extension
newFile = exportToPPTX('save',outputFile);

% Close presentation
exportToPPTX('close');

fprintf('New file has been saved: <a href="matlab:winopen(''%s'')">%s</a>\n',newFile,newFile);

end