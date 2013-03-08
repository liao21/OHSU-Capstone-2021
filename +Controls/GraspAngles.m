classdef  GraspAngles
    % See also GraspTypes.m
    properties (Constant)
        Tip = [10; 0; -25; 35; -75;...
            -20; 50; 43; 28; 23;...
            -10; 80; 90; 55; 0;...
            80; 100; 45; 0; 80;...
            100; 35; 0; -30; 65;...
            -60; -10; 20; 0];
        Relaxed = [10; 0; -35; 30; 55;...
            -50; 15; 15; 15; 15;...
            0; 15; 15; 15; 0;...
            15; 15; 15; 0; 15;...
            15; 15; 5; 0; 0;...
            0; 15; 15; 0;];
        Hook = [0; 10; 0; 5; 60;...
            -10; 40; 62; 55; 20;...
            -3; 70; 50; 25; 2;...
            60; 63; 20; 0; 35;...
            75; 30; 5; -15; 20;...
            0; 5; 0; 0;];
        Extension = [ 10; 0; -25; 15; -75;...
            10; 50; 20; 0; 0;...
            0; 20; 0; 0; 0;...
            20; 0; 0; 0; 20;...
            0; 0; 0; -8; 45;...
            5; 1; 0; 0;];
        Power = [10; 0; -25; 35; -75;...
            -30; 50; 25; 38; 33;...
            0; 30; 38; 33; 0;...
            20; 53; 33; 0; 15;...
            38; 33; 0; -30; 85;...
            -75; 0; 0; 0;];
        Spherical = [10; 0; -40; 95; -39;...
            -35; 10; 10; 55; 5;...
            0; 10; 55; 5; 0;...
            10; 55; 5; 0; 15;...
            57; 5; 15; -25; 10;...
            -10; 20; 8; 0;];
        Tripod = [10; 0; -25; 35; -7;...
            -35; 10; 12; 70; 15;...
            -2; 15; 80; 15; -11;...
            92; 80; 28; 0; 69;...
            83; 55; 0; -20; 80;...
            -70; 0; 0; 0;];
        Lateral = [10; 0; -25; 35; -75;...
            -15; 60; 60; 45; 25;...
            0; 65; 60; 10; 0;...
            65; 70; 35; 0; 70;...
            55; 85; 0; -8; 20;...
            0; 0; 0; 0;];
        Index = [0; 0; 0; 0; 0;...
            0; 0; 80; 80; 80;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0;];
        Middle = [0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 80; 80; 80; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0;];
        Ring = [0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            80; 80; 80; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0;];
        Little = [0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 80;...
            80; 80; 0; 0; 0;...
            0; 0; 0; 0;];
        Thumb = [0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 0;...
            0; 0; 0; 0; 50;...
            0; 50; 50; 0;];
        Cylindrical = [10; 0; -25; 35; -75;...
            -30; 50; 25; 38; 33;...
            0; 30; 38; 33; 0;...
            20; 53; 33; 0; 15;...
            38; 33; 0; -30; 85;...
            -75; 0; 0; 0;];  % copied from "power" 
    end
    methods (Static = true)
        function Test
            
            a = Presentation.MiniV;
            
            [enumGrasp, cellGrasps] = enumeration('Controls.GraspTypes');
            for i = 1:length(cellGrasps)
                grasp = cellGrasps{i};
                
                a.set_hand_angles_degrees(Controls.GraspAngles.(grasp))
                a.redraw
                pause(0.3);
            end
        end
    end
end

