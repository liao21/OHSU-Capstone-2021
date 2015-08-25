classdef mpl_upper_arm_enum
    % List joint enumeration for the JHU/APL MPL system.  Total number of
    % joints is 27.  Includes upper arm (7) and hand (20) angles.  Constant
    % properti3es can be called directly.
    %
    % Example
    % 
    %     mpl_upper_arm_enum.INDEX_MCP
    % 
    %     ans =
    % 
    %          9    
    %
    % Revisions:
    % 2015AUG08 Armiger: Added hand angles
    properties (Constant = true)
        
        SHOULDER_FE = 1;    % + Flexion
        SHOULDER_ADAB = 2;  % + Adduction (toward midline)
        HUMERAL_ROT = 3;    % + Internal (Medial) Rotation
        ELBOW = 4;          % + Flexion
        WRIST_ROT = 5;      % + Supination
        WRIST_DEV = 6;      % + Ulnar Deviation
        WRIST_FE = 7;       % + Flexion

        INDEX_AB_AD = 8;
        INDEX_MCP = 9;
        INDEX_PIP = 10;
        INDEX_DIP = 11;
        MIDDLE_AB_AD = 12;
        MIDDLE_MCP = 13;
        MIDDLE_PIP = 14;
        MIDDLE_DIP = 15;
        RING_AB_AD = 16;
        RING_MCP = 17;
        RING_PIP = 18;
        RING_DIP = 19;
        LITTLE_AB_AD = 20;
        LITTLE_MCP = 21;
        LITTLE_PIP = 22;
        LITTLE_DIP = 23;
        THUMB_CMC_AD_AB = 24;
        THUMB_CMC = 25;
        THUMB_MCP = 26;
        THUMB_DIP = 27;
        
    end
end
