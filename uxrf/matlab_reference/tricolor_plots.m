% tricolor_plots.m -- code cells extracted from tricolor_plots.mlx (MATLAB Live Script).
% Figure output embedded in the .mlx was dropped to keep the repository small.

%% ---- cell 1 ----
blur_sd = 2; % pixel blurring radius

set(0,'DefaultFigureWindowStyle','normal');

Kun19 = import_uxrf('19-AUS-19_*.txt',20,blur_sd);
Kun22 = import_uxrf('19-AUS-22_*.txt',20,blur_sd);

scalebar_length = 3000;

%% ---- cell 2 ----
r = 'S';
g = 'Cl';
b = 'Mg';

map = Kun22;
rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
rgb = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
%rgb = insertShape(rgb,"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
imwrite(rgb,['19-AUS-22 ' r g b '.tif']);

clear r g b rgb map rgb_adj;

%% ---- cell 3 ----
% r = 'Y';
% g = 'Sr';
% b = 'Ca';
% rgb_tiles = cell(8,1);
% 
% map = KNMER60_RtM2;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{1} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{1} = insertText(rgb_tiles{1},[0 0],'KNM-ER 64060 Right M2','BoxColor','white','FontSize',48);
% rgb_tiles{1} = insertShape(rgb_tiles{1},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = KNMER60_RtP4;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{2} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{2} = insertText(rgb_tiles{2},[0 0],'KNM-ER 64060 Right P4','BoxColor','white','FontSize',36);
% rgb_tiles{2} = insertShape(rgb_tiles{2},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% rgb_tiles{3} = imread('tricolor_scale.tif');
% rgb_tiles{3} = insertText(rgb_tiles{3},[230 0; 460 380; 0 380],{r,g,b},'BoxColor',{'red','green','blue'},'FontSize',36,'BoxOpacity',1);
% 
% map = KNMER61_Shaft;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{4} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{4} = insertText(rgb_tiles{4},[0 0],'KNM-ER 64061 Shaft','BoxColor','white','FontSize',24);
% rgb_tiles{4} = insertShape(rgb_tiles{4},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = KNMER61_Ulna;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{5} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{5} = insertText(rgb_tiles{5},[0 0],'KNM-ER 64061 Left Ulna','BoxColor','white','FontSize',24);
% rgb_tiles{5} = insertShape(rgb_tiles{5},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = KNMER61_Misc;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{6} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{6} = insertText(rgb_tiles{6},[0 0],'KNM-ER 64061 Misc. Fragment','BoxColor','white','FontSize',24);
% rgb_tiles{6} = insertShape(rgb_tiles{6},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = F26222_Tooth;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{7} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{7} = insertText(rgb_tiles{7},[0 0],'F26222 Tooth','BoxColor','white','FontSize',36);
% rgb_tiles{7} = insertShape(rgb_tiles{7},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = F26222_Medial;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{8} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{8} = insertText(rgb_tiles{8},[0 0],'F26222 Medial','BoxColor','white','FontSize',48);
% rgb_tiles{8} = insertShape(rgb_tiles{8},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = F26222_2013;
% rgb = cat(3, map.(r).blur, map.(g).blur, map.(b).blur);
% rgb_tiles{9} = imadjust(rgb,stretchlim(rgb),[],[1 1 1]);
% rgb_tiles{9} = insertText(rgb_tiles{9},[0 0],'F26222 2013','BoxColor','white','FontSize',24);
% rgb_tiles{9} = insertShape(rgb_tiles{9},"Line",[map.(r).Ref.ImageSize(2)-(scalebar_length/map.(r).px_size) 50 map.(r).Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% figure();
%     RGB_Image = imshow( imtile(rgb_tiles,'GridSize',[3 3]) );
%     imsave(RGB_Image);
%     clear r g b rgb map rgb_tiles RGB_Image;

%% ---- cell 4 ----
% IA_tiles = cell(8,1);
% 
% map = KNMER61_Misc;
% IA = map.Ca.blur_raw./map.P.blur_raw;
% IA_tiles{1} = imadjust(IA./max(IA(IA<Inf),[],'all'));
% %IA_tiles{1} = insertText(IA_tiles{1},[0 0],'KNM-ER 64060 Right M2','BoxColor','white','FontSize',48);
% %IA_tiles{1} = insertShape(IA_tiles{1},"Line",[map.Ca.Ref.ImageSize(2)-(scalebar_length/map.Ca.px_size) 50 map.Ca.Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% map = KNMER61_Misc;
% % IA = map.Ca.blur./map.P.blur;
% IA_tiles{2} = log10(IA);
% %IA_tiles{2} = insertText(IA_tiles{2},[0 0],'KNM-ER 64060 Right P4','BoxColor','white','FontSize',48);
% %IA_tiles{2} = insertShape(IA_tiles{2},"Line",[map.Ca.Ref.ImageSize(2)-(scalebar_length/map.Ca.px_size) 50 map.Ca.Ref.ImageSize(2) 50],"LineWidth",50,"Color","white");
% 
% figure();
%     IA_Image = imshow( imtile(IA_tiles,'GridSize',[3 3]) );
%     %imsave(IA_Image);
    %clear map IA_tiles IA_Image;

%% ---- cell 5 ----
function Img = img_proc_uxrf(filename,px_size,blur_sd)
    counts = importdata(filename);
    % TODO: allow cropping counts matrix
    Img.px_size = px_size;
    
    Img.Ref = imref2d(size(counts),px_size,px_size);
    Img.width = Img.Ref.ImageExtentInWorldX;
    Img.height = Img.Ref.ImageExtentInWorldY;
    
    Img.raw = counts;
    Img.total = sum(counts(:));
    Img.max = max(counts(:));
    Img.min = min(counts(:));

    Img.norm = counts-min(counts(:));
    Img.norm = Img.norm/max(Img.norm(:));

    Img.blur_sd = blur_sd;
    Img.blur_raw = imgaussfilt(counts,Img.blur_sd);
    Img.blur = Img.blur_raw-min(Img.blur_raw(:));
    Img.blur = Img.blur/max(Img.blur(:));

%     Img.raw = tall(Img.raw);
%     Img.norm = tall(Img.norm);
%     Img.blur_raw = tall(Img.blur_raw);
%     Img.blur = tall(Img.blur);
end

% TODO: Implement Datastores

function Map = import_uxrf(file_search,px_size,blur_sd)
    files = dir(file_search);
    for i = 1:length(files)
        Img = img_proc_uxrf([files(i).folder '\' files(i).name],px_size,blur_sd);
        element = files(i).name(find(files(i).name=='_',1,'last')+1:end-4);
        element = erase(element,' ');
        Map.(element) = Img;
    end
end

function h = uxrf_montage(Map,type,gamma)
    elements = fieldnames(Map);
    switch nargin
        case 3
            if length(gamma)==1
                gamma = gamma.*ones(1,length(elements));
            end
        case 2
            gamma = ones(1,length(elements));
        case 1
            gamma = ones(1,length(elements));
            type = 'raw';
    end

    for i = 1:length(elements)
        s(i) = subplot(ceil(sqrt(length(elements))),ceil(sqrt(length(elements))),i);
        % imshow(Map.(elements{i}).(type),[]);
        imshow(histeq(imadjust(Map.(elements{i}).(type),[],[],gamma(i))),Map.(elements{i}).Ref);
        % title(elements{i});
        hold on;
        text(0.01,0.99,elements{i},'Units','Normalized','BackgroundColor','white','VerticalAlignment','top','FontSize',6);
        
        %set(gca, 'Position', [0 0 1 1]);
        set(gca, 'LooseInset', [0,0,0,0]);
        ax = gca;
        outerpos = ax.OuterPosition;
        ti = ax.TightInset; 
        left = outerpos(1) + ti(1);
        bottom = outerpos(2) + ti(2);
        ax_width = outerpos(3) - ti(1) - ti(3);
        ax_height = outerpos(4) - ti(2) - ti(4);
        ax.Position = [left bottom ax_width ax_height];
        
    end
    
    h = s;
end

function h = uxrf_labeled_montage(Map,type,gamma)
    % requires Computer Vision Toolbox
    elements = fieldnames(Map);
    switch nargin
        case 3
            if length(gamma)==1
                gamma = gamma.*ones(1,length(elements));
            end
        case 2
            gamma = ones(1,length(elements));
        case 1
            gamma = ones(1,length(elements));
            type = 'raw';
    end

    imgs = zeros([size(Map.(elements{1}).(type)) length(elements)]);
    for i = 1:length(elements)
        img = Map.(elements{i}).(type);
        img = imadjust(img,stretchlim(img),[],gamma(i));
        img = insertText(img,[2 2],elements{i},'BoxColor','white','FontSize',36);
        imgs(:,:,i) = img(:,:,1);
    end

    I = imtile(imgs);

    figure();
    s = imshow(I);
    h = s;
end
