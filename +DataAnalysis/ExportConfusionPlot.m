UserConfig.getInstance('MPL_04_user_config.xml');
p = UserConfig.getUserConfigVar('userBasePath','');
%d = rdir(fullfile(p,'\MPL_04 session 1\*.trainingData'));
d = rdir(fullfile(p,'\**\*.trainingData'));

for i = 1:length(d);
    f = d(i).name;
    [pathStr, fileName, fileExt] = fileparts(f);
    [pathRemain, Session, ~] = fileparts(pathStr);
    [~, Subject, ~] = fileparts(pathRemain);
    
    hTraining = TrainingDataAnalysis(f);
    hClassifier = SignalAnalysis.Lda;
    hClassifier.initialize(hTraining);
    hClassifier.train;

%     f = UiTools.create_figure('Confusion Matrix','Confusion_Matrix');
    f = figure;
    set(f,'Units','pixels')
    set(f,'ToolBar','figure')
    p = get(f,'Position');
    p = [p(1) p(2)/2 800 600];
    set(f,'Position',p);
    clf(f)
    hAxes = axes('Parent',f);
    
    hClassifier.plotConfusion(hAxes);
    title({'Actual versus predicted class (%)' fullfile(Subject,Session,fileName)},'Parent',hAxes,'Interpreter','None');
    drawnow
end