classdef MeshTools
    % Tools for manipulating meshes and triangulations in 2D and 3D.
    %
    % Includes tools for loading saving and converting .stl, .vtk, patch
    % objects and stlMesh matrices.  
    % 
    % Static Methods:
    %
    %   PATCH2VTK - Convert a patch object to vtk file format
    %   PATCH2STL - Convert a patch object to stl file format
    %   PATCH2STLMESH - Convert a patch object to stlMesh matrix
    %   SAVE_STL - Save stl file from stlMesh matrix
    %   READ_STL - Read stl file as stlMesh matrix
    %   STLMESH2PATCH - Convert a stlMesh matrix to patch object
    %   STLMESH_TO_PATCH - Convert a stlMesh matrix to patch object
    
    methods (Static = true)
        function faceNormal = faceNormals(varargin)
            %%% migrated from BGSS shared functions by ASI:20140828
            % F_FACE_NORMALS - compute face normals
            %
            % faceNormals = f_face_normals(surf)
            %   Given a surface with fields elementData and nodeData compute the face
            %   normals. The transpose of the output can be set as surf.faceNormals
            %
            % faceNormals = f_face_normals(a1,a3,a3)
            %   Given 3 lists of 3xN vertices and return normal vectors.
            
            % 3/16/05 Bobby Armiger
            
            if nargin == 1
                % a surface was passed in
                model = varargin{1};
                faces = model.elementData';
                verts = model.nodeData';
                
                a1 = verts(:, faces(1, :));
                a2 = verts(:, faces(2, :));
                a3 = verts(:, faces(3, :));
            elseif nargin == 3
                a1 = varargin{1};
                a2 = varargin{2};
                a3 = varargin{3};
            else
                error('BGS:f_face_normals:Usage',...
                    'f_face_normals expects either 1 or 3 arguments');
            end
            
            if size(a1,1) ~= 3
                error('Use Column Vectors');
            end
            
            v12 = a2-a1;
            v13 = a3-a1;
            %%% eliminated by ASI to take out dependency of BGSS
%             faceNormal = f_normalize(cross(v12,v13));
            faceNormal = LinAlg.normalize(cross(v12,v13));
        end
        function [hit,location] = rayFire(sur,R,Rn)
            %%% migrated from BGSS shared functions by ASI:20140828
            %% inputs:
            %% surface model (sur.nodeData; sur.elementData)
            %% Ray Origin: R
            %% Ray Direction: Rn
            
            % Re-allowed close points for cartilage thickness computation - Ryan 3/24/09
            % Edited for case where plane is parallel to ray (badPts) - Bobby 6/10/05
            % Modified code so that points very near the start of the ray are also
            % excluded - Bobby 4/14/05
            
            % R = [0;0;0];
            % theta = 60;
            % scale = 2;
            % AimPoint = [scale*cos(theta*pi/180); scale*sin(theta*pi/180);0];
            % Rn = f_normalize(AimPoint-R);
            % hold on
            % f_plot3([R AimPoint],'r');
            % axis equal
            % v1 = [sqrt(3);1;0];
            % v2 = [1;sqrt(3);1];
            % v3 = [1;sqrt(3);-1];
            % f_plot3([v1 v2 v3 v1],'b');
            
            %%%%%%%%%%%%%%%%%%%%%%
            if isfield(sur,'nodeData')
                vertices = sur.nodeData;
            elseif isfield(sur,'vertices')
                vertices = sur.vertices;
            else
                error('No vertex info found for input data')
            end
            
            if isfield(sur,'elementData')
                faces = sur.elementData;
            elseif isfield(sur,'faces')
                faces = sur.faces;
            else
                error('No face info found for input data')
            end
            
            % Extract vertex coords from each face
            v1 = vertices(faces(:,1),:)';
            v2 = vertices(faces(:,2),:)';
            v3 = vertices(faces(:,3),:)';
            % Center of each face:
            c = (v1 + v2 + v3) ./3;
            nFaces = length(c);
            
            % Plane is described by normal Xn and point X
            Xn = MeshTools.faceNormals(v2,v1,v3);
            
            % Point on plane is:
            X = c;
            
            % Ray = R + t.* Rn
            R_mult = repmat(R,[1 nFaces]);
            Rn_mult = repmat(Rn,[1 nFaces]);
            
            % Check for case where Ray is parallel to plane:
            check = dot(Xn,Rn_mult);
            % Ray is not parallel to Plane, so intersection is possible
            badPts = find(abs(check) < eps);
            % Set plane normal to ray normal to avoid divide by zero:
            if length(badPts) > 0,Xn(:,badPts) = repmat(Rn,[1,length(badPts)]);end
            
            % Solve for intersection of ray and plane
            t = (dot(Xn,X-R_mult)) ./ dot(Xn,Rn_mult);
            t(badPts) = 0;
            t_mult = repmat(t,[3 1]);
            % Origin of ray and behind are not valid
            indexNo = find(t <= 0);
            % idx = find(t <= 10);
            
            % Call this intersection point M
            M = R_mult + (t_mult .* Rn_mult);
            
            results = PointInTriangle(M,v1,v2,v3);
            results(indexNo) = 0; %removed due to global variable
            hit = find(results == 1);
            location = M(:,hit);
            
            function result = SameSide(p1,p2,a,b)
                cp1 = cross(b-a, p1-a);
                cp2 = cross(b-a, p2-a);
                result = zeros(1,length(a));
                indexYes = find(dot(cp1,cp2) >= 0);
                result(indexYes) = 1;
                return
            end
            
            function result = PointInTriangle(p,a,b,c)
                list1 = SameSide(p,a,b,c);
                list2 = SameSide(p,b,a,c);
                list3 = SameSide(p,c,a,b);
                result = zeros(1,length(a));
                indexYes = find(list1 == 1 & list2 == 1 & list3 == 1);
                result(indexYes) = 1;
                return
            end
            
        end
        function success = patch2vtk(patchObject, fullFilename, strDescription)
            %patch2vtk(patchObject, fullFilename, strDescription)
            %
            % Convert a patch object to a vtk file.
            %
            % Inputs :
            %   patchObject - MATLAB patch object with the fields:
            %           .vertices - is a [nVertices x 3] list of each vertex in cartesian space.
            %           .faces - is the list of the connectivity of the
            %               vertices (1-based).  Note the output .vtk file will
            %               indicate these as 0-based
            %
            %   fullFilename - the full filename of the output.  Typically
            %       with .vtk extension.  If a filename is not provided or
            %       is empty, a user prompt will appear to select a file to
            %       write
            %
            %   strDescription - Optional: string description for .vtk file
            %       to be printed in the header file
            %
            % Sample example :
            %
            %   [x y z] = sphere;
            %   FV = surf2patch(x,y,z,z)
            %   patch(FV);
            %   shading faceted; view(3)
            %   MeshTools.patch2vtk(FV,'sphere_test.vtk','Sphere Test 0.1')
            %
            %
            % See "http://www.vtk.org/VTK/img/file-formats.pdf" for file
            % format description
            %
            % Revisions:
            % 21JUL2014 Armiger: Initial Revision
            
            % Prompt for filename
            if nargin < 2 || isempty(fullFilename)
                
                [FileName,PathName,FilterIndex] = uiputfile('*.vtk');
                if FilterIndex == 0
                    % User Cancelled
                    success = 0;
                    return
                end
                
                fullFilename = fullfile(PathName,FileName);
                
            end
            
            % add description or base off of filename
            if nargin < 3
                [~,f,e] = fileparts(fullFilename);
                strDescription = sprintf('VTK MATLAB Writer: %s',strcat(f,e));
            end
            
            % get data size info
            numPoints = size(patchObject.vertices,1);
            [numFaces, numVerticesPerFace] = size(patchObject.faces);
            
            % open file or writing
            fid = fopen(fullFilename,'w');
            
            % Write header
            fprintf(fid,'# vtk DataFile Version 3.0\n');
            fprintf(fid,'%s\n',strDescription);
            fprintf(fid,'ASCII\n');
            fprintf(fid,'DATASET POLYDATA\n');
            
            % Write points data
            fprintf(fid,'POINTS %d float\n',numPoints);
            fprintf(fid,'%3.7f %3.7f %3.7f\n',patchObject.vertices');
            
            % Write polygon connectivity
            fprintf(fid,'POLYGONS %d %d\n',numFaces,numFaces*(numVerticesPerFace+1));
            
            % Create a formatting template for the number of vertices per polygon
            strFormat = repmat('%d ',1,numVerticesPerFace + 1);
            strFormat = strcat(strFormat,'\n');
            
            % Write the connectivity
            fprintf(fid,strFormat,cat(2,repmat(numVerticesPerFace,numFaces,1),patchObject.faces-1)');
            
            % close file
            fclose(fid);
            
            success = 1;
        end
        
        function success = patch2stl(patchObject, fullFilename)
            % success = patch2stl(patchObject, fullFilename)
            % Save patch object as stl file
            %
            % Sample example :
            %
            %   [x y z] = sphere;
            %   FV = surf2patch(x,y,z,z)
            %   patch(FV);
            %   shading faceted; view(3)
            %   MeshTools.patch2stl(FV,'sphere_test.stl')
            %
            % Revisions:
            % 21JUL2014 Armiger: Initial Revision
            
            stlMesh = MeshTools.patch2stlMesh(patchObject);
            
            MeshTools.save_stl(fullFilename,stlMesh);
            
            success = 1;
        end
        
        function stlMesh = patch2stlMesh(patch)
            % stlMesh = patch2stl(patch) - Convert patch data to stlMesh
            % matrix
            %
            % Bobby Edited 5/30/06 to incorporate multiple structure forms
            % Bobby Edited 6/9/05 to add nodenormals logic (helps convert surfaces that
            % don't have all the fields defined)
            % Bobby Edited 10/12/05 to trim code with try-catch block faceNormals are
            % required; loop eliminated
            if isfield(patch,'faces') && isfield(patch,'vertices')
                vertices = patch.vertices;
                faces = patch.faces;
            elseif isfield(patch,'nodeData') && isfield(patch,'elementData')
                vertices = patch.nodeData;
                faces = patch.elementData;
            else
                error('Input format must contain vertex and face info')
            end
            
            % Get original patch faces and validate
            if size(faces,2) == 4 %% Find quad faces and split them to triangles:
                %faces4vIdx = find(faces(:,3) ~= faces(:,4));
                faces4vIdx = faces(:,3) ~= faces(:,4);
                triFaces = faces(faces4vIdx,[1 3 4]);
                faces(:,4) = [];
                faces = [faces; triFaces];
            end
            
            try patch.faceNormals(1);
                normals = patch.elementNormals;
            catch
                % This means that nodeNormals need to be defined
                v1 = vertices(faces(:,1),:);
                v2 = vertices(faces(:,2),:);
                v3 = vertices(faces(:,3),:);
                normals = MeshTools.faceNormals(v1',v2',v3')';
            end
            
            nFaces = size(faces,1);
            % Extract the three vertices of every face:
            a = vertices(faces',:);
            % Reshape to an XYZ x nVertices x nFaces matrix
            b = reshape(a',[3 3 nFaces]);
            % Reshape to an nVertices x XYZ x nFaces matrix
            c = permute(b,[2 1 3]);
            n = reshape(normals',[1 3 nFaces]);
            % Add Normals as row 4 for every face
            stlMesh = [c;n];
            
        end
                
        function save_stl(filename,stlMesh)
            % convert from 'mesh' format back to stl and save
            % 10/12/05 Bobby reduced code and optimized
            
            if nargin == 0, error('Usage: MeshTools.save_stl(fileName,stlMesh)');
            elseif nargin == 1
                stlMesh = filename;
                [filename,pathname, FilterIndex] = uiputfile('*.stl', 'STL File (*.stl)');
                if FilterIndex == 0,return,end
                % write the data into the file
                filename = fullfile(pathname, filename);
            end
            
            S = fopen(filename,'w');
            if S < 1
                error('Error opening %s for writing',filename);
            end
            nFaces = size(stlMesh,3);
            
            % creating new '.stl' file for the new surface
            % Writing according to the format of the '.stl' file
            fprintf(S, 'solid ');
            [~, fname] = fileparts(filename);
            fprintf(S, '%s\n',fname);
            for iFace = 1:nFaces
                fprintf(S,' facet normal %f %f %f\n',stlMesh(4,1:3,iFace));
                fprintf(S,'    outer loop\n');
                fprintf(S,'       vertex %f %f %f\n',stlMesh(1:3,1:3,iFace)');
                fprintf(S,'    endloop\n');
                fprintf(S,' endfacet\n');
            end
            fprintf(S,'endsolid\n');
            fclose(S);
        end
        
        function [stlMesh, msg] = read_stl(fileName)
            % MESHTOOLS.READ_STL - read stl file
            %
            %   [stlMesh msg] = MeshTools.read_stl()
            %       Prompts the user for an stl file. Reads and converts it into the
            %       easily portable 'mesh' matrix format. This function automatically
            %       checks for binary vs ascii stl files.
            %
            %   [stlMesh msg] = MeshTools.f_read_stl(filename)
            %       Reads in the given stl file.
            
            % $Log: f_read_stl.m  $
            % Revision 1.10 2012/02/15 08:29:37EST Murphy, Ryan J. (murphrj2-a)
            % minor improvement to reading in STL
            % Revision 1.9 2010/12/16 17:39:17EST Armiger, Robert S. (ArmigRS1-a)
            % revised stl binary read methodology and added compatability for big endian files
            % Revision 1.8 2010/08/23 16:25:43EDT murphrj2-a
            % added auto determination of binary files
            
            % 25 Feb 2009 RSA: revised to use textscan which is hugely faster than
            % fscanf in a loop
            
            if nargin < 1
                [filename, pathname, filterindex] = uigetfile( ...
                    {'*.stl', 'STL File (*.STL)';'*.*', 'All Files (*.*)'}, ...
                    'Pick an STL file to load');
                if filterindex == 0
                    stlMesh = [];
                    msg = 'User Cancelled';
                    return
                end
                fileName = fullfile(pathname,filename);
            end
            
            % open file for reading
            [fid, msg] = fopen(fileName, 'r');
            if fid < 0
                stlMesh = [];
                msg = sprintf('File %s could not be opened.\n Error was: "%s" \n',fileName,msg);
                return
            end
            
            % check for binary or ascii - look for solid/endsolid tags
            % solid is supposed to suffice but solidworks does not follow this
            % convention.
            init = strtrim(fread(fid,80,'char=>char')');
            fseek(fid,-50,'eof');
            end_str = strtrim(fread(fid,50,'char=>char')');
            
            foundBegin = strcmpi(init(1:5),'solid');
            foundEnd = strfind( lower(end_str), 'endsolid' );
            
            isBinary =  (~foundBegin || isempty(foundEnd));
            
            
            % go back to beginning of file
            fseek(fid,0,-1);
            
            try
                if isBinary
                    strFormat = 'BINARY';
                    stlMesh = read_binary_format(fid);
                else
                    strFormat = 'ASCII';
                    stlMesh = read_ascii_format(fid);
                end
                msg = [];
                fclose(fid);
            catch ME
                fclose(fid);
                stlMesh = [];
                msg = sprintf('Unable to read file: %s in %s format: %s\n ',fileName,strFormat,ME.message);
            end
            
            function stlMesh = read_ascii_format(fid)
                
                % Reading out info from stl file
                % Store them into normal and points matrix
                
                % Read file contents
                fgetl(fid);    %read off first line [solid] and filename
                % read formatted data.  note %*2c reads [and discards] 2 EOL chars <CRLF>
                C = textscan(fid, [...
                    '%*[facet normal] %f %f %f %*2c'  ...
                    '%*[outer loop] %*2c' ...
                    '%*[vertex] %f %f %f %*2c' ...
                    '%*[vertex] %f %f %f %*2c' ...
                    '%*[vertex] %f %f %f %*2c' ...
                    '%*[endloop] %*2c' ...
                    '%*[endfacet] %*2c' ...
                    ]);
                %make sure we're at the end
                fgetl(fid); % read off final line
                if ~feof(fid)
                    warning('Shared_Functions:EofNotReached','End of STL file not reached');
                end
                % expect [endsolid] and EOF here, this may cause a couple NaNs to show
                % up at the end of the read
                nFaces = size(C{end},1);  % use last element since we may have Nan in the first column
                
                % store in 'stlMesh' data structure
                stlMesh = zeros(4,3,nFaces);
                
                % row 4 = face normal
                stlMesh(4,1,:) = C{1}(1:nFaces);
                stlMesh(4,2,:) = C{2}(1:nFaces);
                stlMesh(4,3,:) = C{3}(1:nFaces);
                
                % row 1 = v1: xyz
                stlMesh(1,1,:) = C{4}(1:nFaces);
                stlMesh(1,2,:) = C{5}(1:nFaces);
                stlMesh(1,3,:) = C{6}(1:nFaces);
                
                % row 2 = v2: xyz
                stlMesh(2,1,:) = C{7}(1:nFaces);
                stlMesh(2,2,:) = C{8}(1:nFaces);
                stlMesh(2,3,:) = C{9}(1:nFaces);
                
                % row 3 = v3: xyz
                stlMesh(3,1,:) = C{10}(1:nFaces);
                stlMesh(3,2,:) = C{11}(1:nFaces);
                stlMesh(3,3,:) = C{12}(1:nFaces);
                
            end
            
            function [stlMesh, colorRGB] = read_binary_format(fid)
                
                % This function reads an STL file in binary format into a single 3d matrix.
                
                if nargout > 2
                    error('Too many output arguments')
                end
                
                % Need to determine the endianess of the file fread defaults to little
                % endian on pc
                
                fseek(fid,0,1);  % seek to end of file
                numBytes = ftell(fid);  % total number of bytes
                numHeaderBytes = 84;
                sizeOfSingle = 4;
                sizeOfUInt16 = 2;
                numSinglesPerFacet = 12;
                numDataBytesPerRecord = numSinglesPerFacet * sizeOfSingle + sizeOfUInt16;
                numFacetsExpected = (numBytes - numHeaderBytes) / numDataBytesPerRecord;
                hasRemainder = rem(numFacetsExpected,1) ~= 0;
                if hasRemainder
                    error('File size is not consistent with STL binary standard')
                else
                    % Verified, re-seek to beginning
                    fseek(fid,0,-1); % seek to beginning
                end
                
                % Read file header
                ftitle = fread(fid,80,'*char'); % Read file title
                numFacetBytes = fread(fid,4,'*uint8'); % Read number of Facets
                
                % Use the expected number of facets to check endian
                numFacets = typecast(numFacetBytes,'int32');
                if numFacets == numFacetsExpected
                    fprintf('[%s] File Format is Little Endian\n',mfilename);
                    isLittleEndian = true;
                elseif swapbytes(numFacets) == numFacetsExpected
                    fprintf('[%s] File Format is Big Endian\n',mfilename);
                    isLittleEndian = false;
                    numFacets = swapbytes(numFacets);
                else
                    error('Number of expected facets does not match file header');
                end
                
                fprintf('[%s] Header: "%s"\n', mfilename, ftitle);
                fprintf('[%s] Number of Facets=%d\n', mfilename, numFacets);
                
                % Preallocate memory to save running time
                stlMesh = zeros(4,3,numFacets);
                colorRGB = zeros(3,numFacets,'uint8');
                
                % Read file data
                % 12/16/2010 RSA: Revised file read approach from a looped read of each
                % face to the 'bulk' read here.  For 500k faces this decreased read
                % time from 14 seconds to 0.5;
                %
                dataBytes = fread(fid,[numDataBytesPerRecord numFacets],'*uint8');
                
                singleBytes = dataBytes(1:48,:);  % will be cast to single
                colorBytes = dataBytes(49:50,:);  % will be cast to uint16
                
                singleVals = typecast(singleBytes(:),'single');
                if ~isLittleEndian
                    singleVals = swapbytes(singleVals);
                end
                
                singleValMatrix = reshape(singleVals,12,numFacets);
                
                % facet normal
                stlMesh(4,1,:) = reshape(singleValMatrix(1,:),1,numFacets);
                stlMesh(4,2,:) = reshape(singleValMatrix(2,:),1,numFacets);
                stlMesh(4,3,:) = reshape(singleValMatrix(3,:),1,numFacets);
                
                % vertex1
                stlMesh(1,1,:) = reshape(singleValMatrix(4,:),1,numFacets);
                stlMesh(1,2,:) = reshape(singleValMatrix(5,:),1,numFacets);
                stlMesh(1,3,:) = reshape(singleValMatrix(6,:),1,numFacets);
                
                % vertex2
                stlMesh(2,1,:) = reshape(singleValMatrix(7,:),1,numFacets);
                stlMesh(2,2,:) = reshape(singleValMatrix(8,:),1,numFacets);
                stlMesh(2,3,:) = reshape(singleValMatrix(9,:),1,numFacets);
                
                % vertex3
                stlMesh(3,1,:) = reshape(singleValMatrix(10,:),1,numFacets);
                stlMesh(3,2,:) = reshape(singleValMatrix(11,:),1,numFacets);
                stlMesh(3,3,:) = reshape(singleValMatrix(12,:),1,numFacets);
                
                colorType = typecast(colorBytes(:),'uint16');
                if ~isLittleEndian
                    colorType = swapbytes(colorType);
                end
                
                if any(bitget(colorType,16)==1)
                    r = bitshift(bitand(2^16-1, colorType),-10);
                    g = bitshift(bitand(2^11-1, colorType),-5);
                    b = bitand(2^6-1, colorType);
                    colorRGB(1,:) = r;
                    colorRGB(2,:) = g;
                    colorRGB(3,:) = b;
                end
                
                % For more information http://rpdrc.ic.polyu.edu.hk/old_files/stl_binary_format.htm
            end
            
        end
        
        function patch = stlMesh2patch(stlMesh)
            % See: stlMesh_to_patch
            patch = MeshTools.stlMesh_to_patch(stlMesh);
        end
        function FV = stlMesh_to_patch(stlMesh)
            %stlMesh_to_patch  Convert stlMesh to faces and vertices.
            %   patch = MeshTools.stlMesh_to_patch(stlMesh)
            %   This tool is designed to convert STL data, which uses face normal convention, into
            %   the patch format.
            %
            %   Results can then be plotted with patch(FV);
            %   6/4/2006 RSA
            
            FV = [];
            
            if nargin < 1
                stlMesh = MeshTools.read_stl();
                if isempty(stlMesh),return,end
            end
            
            nFaces = size(stlMesh,3);
            
            % look at points only, not normals
            % do some rearranging to list all vertices
            pts = stlMesh(1:3,1:3,:);
            pts2 = reshape(pts,3,3*nFaces)';
            pts3 = reshape(pts2,3,3*nFaces)';
            [vertices,~,idxJ] = unique(pts3,'rows');
            
            faces = reshape(idxJ,nFaces,3);
            
            FV.faces = faces;
            FV.vertices = vertices;
            
        end
    end
end