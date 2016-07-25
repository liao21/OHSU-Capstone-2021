classdef GraspConverter < handle
    % See also: Controls.GraspTypes
    methods (Static)
        function graspId = graspLookup(enumGraspName, rocNames)
            if nargin < 2
                graspId = MPL.GraspConverter.lookupStatic(enumGraspName);
            else
                graspId = MPL.GraspConverter.lookupByName(enumGraspName,rocNames);
            end
        end
        function graspId = lookupByName(enumGraspName,rocNames)
            % MPL.GraspConverted.graspLookup
            % Map the minivie grasp enumeration to the ROC ids on the
            % Limb
            if isempty(enumGraspName)
                graspId = 0;
            else
                
                % setup a cell array of the enumerated grasps, with thos
                % specified in ROC table.
                graspNameMap = {
                    'Tip', {'FinePinch(American)'}
                    'Lateral', {'Lateral'}
                    'Tripod', {'ThreeFingerPinch'}
                    'Spherical', {'Spherical'}
                    'Power', {'Cylindrical'}
                    'Extension', {'Palmar(Tray)'}
                    'Hook', {'Hook'}
                    'Relaxed', {'rest'}
                    'Index', {'Index Only'}
                    'Middle', {'Middle Only'}
                    'Ring', {'Ring Only'}
                    'Little', {'Little Only'}
                    'Thumb', {'Thumb Only'}
                    'Cylindrical', {'Cylindrical'}
                    'Point', {'Trigger(Drill)'}
                    'Trigger', {'Trigger(Drill)'}
                    };
                
                thisGrasp = find(strcmp(char(enumGraspName),graspNameMap(:,1)),1);
                if isempty(thisGrasp)
                    warning('Unmatched INPUT grasp %s\n',char(enumGraspName));
                    graspId = 0;
                    return
                end
                thisRoc = graspNameMap{thisGrasp,2};
                graspId = find(strcmp(rocNames,thisRoc{1}),1);
                if isempty(graspId)
                    warning('Unmatched ROC grasp %s\n',thisRoc{1});
                    graspId = 0;
                    return
                end
                
                % return zero based grasp
                graspId = graspId - 1;
                
            end
        end
        
        function graspId = lookupStatic(enumGraspName)
            % MPL.GraspConverted.graspLookup
            % Map the minivie grasp enumeration to the ROC ids on the
            % Limb
            if isempty(enumGraspName)
                graspId = 0;
            else
                switch char(enumGraspName)
                    case 'Tip'
                        %graspId = 1;  % Pinch (British)
                        graspId = 2;  % Pinch (American)
                    case 'Lateral'
                        graspId = 15;  % Key
                    case 'Tripod'
                        graspId = 4;  % 3 Finger Pinch
                    case 'Spherical'
                        graspId = 7;  % Spherical
                        %graspId = 1;
                    case 'Cylindrical'
                        graspId = 5;  % Cylindrical
                    case 'Power'
                        graspId = 5;  % Cylindrical
                    case 'Extension'
                        graspId = 3;  % Palmar (Tray)
                    case 'Hook'
                        graspId = 8;  % Hook
                    case 'Relaxed'
                        graspId = 0;
                    case 'Index'
                        graspId = 9;
                    case 'Middle'
                        graspId = 10;
                    case 'Ring'
                        graspId = 11;
                    case 'Little'
                        graspId = 12;
                    case 'Thumb'
                        graspId = 13;
                    case {'Point', 'Pointer', 'Trigger'}
                        graspId = 6;
                    otherwise
                        graspId = 0;
                end
                % zero based index from the enumeration
                %graspId = find(obj.GraspId == enumeration('Controls.GraspTypes'))-1;
                
                %graspId = 1;  % Pinch (American)
                
            end
        end % function graspLookup
        
    end % methods (Static)
end