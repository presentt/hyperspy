% plot_maps.m -- code cells extracted from plot_maps.mlx (MATLAB Live Script).
% Figure output embedded in the .mlx was dropped to keep the repository small.

%% ---- cell 1 ----
blur_sd = 1; % pixel blurring radius
resolution = 20; % nominal pixel size, micron
dwell = 30; % average pixel dwell time, ms
fileprefix = 'rt_p4_whole_*.txt'; % pattern match to read in files

set(0,'DefaultFigureWindowStyle','normal');

map = import_uxrf(fileprefix,resolution,blur_sd); 
    % makes a nested structure that has maps of each element
    % for example, uxrf_struct.Ca.raw is the raw cps at each pixel
    % .norm is stretched from zero to one
    % .blur_raw is the gaussian blur given the blur_sd input to the function
    % .blur is the blurred map stretched from zero to one
    % .Ref is the image dimensions to scale according to the given pixel size

%% ---- cell 2 ----
element = "Ca";
figure;   
    imshow(map.(element).blur_raw,[]); % try to threshold for good counts?
    title(element);
figure;
        histogram(map.(element).blur_raw);
        xlabel('CPS'); ylabel('Number of Pixels');
        axis square;

figure;
    imshow(map.Mn.blur_raw,[],'ColorMap',parula); % plot the blurred version and make it pretty
    colorbar();

figure;
    imshow(map.Ca.blur,'ColorMap',parula);
    colorbar(); % note how the .blur and .norm structures are already normalized to one, not to max(cps)

%% ---- cell 3 ----
figure;
    gamma = ones(1,length(fieldnames(map))); % ;lower gamma is lighter
    %gamma(2) = .05;
    %s = uxrf_montage(map,'blur',gamma);
    s2 = uxrf_labeled_montage(map,'blur');
    imsave(s2);
    %imwrite(findobj(s2,'Type','image'),gray(),[fileprefix(1:end-6) '_montage.tiff']);
    
        % uxrf_montage plots all of the imported maps and adjust the gamma using a vector of gamma values
        % gamma can be a single value, or left out (defaults to 1)
        % the 2nd argument is the map type; it can be any of the sub-structures listed above

%% ---- cell 4 ----
    red = map.Mn.blur;
    green = map.Fe.blur;
    blue = map.Ca.blur;
    scale = map.Ca.Ref;
    rgb = cat(3,red,green,blue);
figure;
       rgbimg = imshow(imadjust(rgb,stretchlim(rgb),[],[1 1 1]),scale);
       %imsave(rgbimg);
       %montage(imadjust(rgb,stretchlim(rgb),[],[1 1 1]),'Size',[1,3])
       %xrftiles = imtile(imadjust(rgb,stretchlim(rgb),[],[1 1 1]));
       %imshow(xrftiles);
       
    % tri-color plot of the normalized maps
    % don't need the [] argument like above because the .blur and .norm maps are already normalized
    % providing the .Ref gives the image x and y axes in the same units as the pixel size (microns here)
    
    % imwrite(cat(3,map.Ca.blur,map.Fe.blur,map.Sr.blur),'test_RGB.tiff'); % save what you want
    
    red = map.S.blur;
    green = map.Fe.blur;
    blue = map.Ca.blur;
    scale = map.Ca.Ref;
    rgb = cat(3,red,green,blue);
figure;
    imshow(imadjust(rgb,stretchlim(rgb)),scale);

%% ---- cell 5 ----
figure;
    ratiomap = map.S.blur./map.Fe.blur;
    imshow(log10(ratiomap),[],'ColorMap',parula)
    colorbar;

%% ---- cell 6 ----

figure;
tiledlayout('flow');
    fields = fieldnames(map);
    for i = 1:length(fields)
        nexttile;
        histogram2(map.Ca.blur_raw(:),map.(fields{i}).blur_raw(:),'DisplayStyle','tile');
        % cross plot the blurred data
        ylabel(['Blurred ',fields{i}]); xlabel('Blurred Ca');
    end

%% ---- cell 7 ----
function Img = img_proc_uxrf(filename,px_size,blur_sd)
    counts = importdata(filename);
    Img.px_size = px_size;
    
    Img.Ref = imref2d(size(counts),px_size,px_size);
    Img.width = Img.Ref.ImageExtentInWorldX;
    Img.height = Img.Ref.ImageExtentInWorldY;
    
    Img.raw = counts;
    Img.total = sum(counts(:));
    Img.max = max(Img.raw(:));
    Img.min = min(Img.raw(:));

    Img.norm = Img.raw-min(Img.raw(:));
    Img.norm = Img.norm/max(Img.norm(:));

    Img.blur_sd = blur_sd;
    Img.blur_raw = imgaussfilt(Img.raw,Img.blur_sd);
    Img.blur = Img.blur_raw-min(Img.blur_raw(:));
    Img.blur = Img.blur/max(Img.blur(:));
end

function Map = import_uxrf(file_search,px_size,blur_sd)
    files = dir(file_search);
    for i = 1:length(files)
        Img = img_proc_uxrf(files(i).name,px_size,blur_sd);
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
        img = insertText(img,[2 2],elements{i},'BoxColor','white','FontSize',60);
        imgs(:,:,i) = img(:,:,1);
    end

    I = imtile(imgs);

    figure();
    s = imshow(I);
    h = s;
end
