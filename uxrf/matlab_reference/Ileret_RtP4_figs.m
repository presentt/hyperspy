blur_sd = 1.5; % pixel blurring radius
resolution = 25; % nominal pixel size
fileprefix = "Rt P4 nofilter_*.txt"; % pattern match to read in files

uxrf_struct = import_uxrf(fileprefix,resolution,blur_sd); 
    % makes a nested structure that has maps of each element
    % for example, uxrf_struct.Ca.raw is the raw cps at each pixel
    % .norm is stretched from zero to one
    % .blur_raw is the gaussian blur given the blur_sd input to the function
    % .blur is the blurred map stretched from zero to one
    % .Ref is the image dimensions to scale according to the given pixel size
    
% figure;
%     imshow(uxrf_struct.Ca.raw,[]); % just plot the raw data, the [] argument stretches the data automatically
%     
% figure;
%     imshow(uxrf_struct.Ca.blur_raw,[],'ColorMap',parula); % plot the blurred version and make it pretty
%     colorbar();
%     
figure;
    imshow(uxrf_struct.Ca.blur,'ColorMap',parula);
    colorbar(); % note how the .blur and .norm structures are already normalized to one, not to max(cps)
    
figure;
    gamma = 0.2.*ones(1,24);
    gamma(2) = 2;
    gamma(5) = 1;
    gamma(8) = 0.8;
    gamma(11) = 1;
    s = uxrf_montage(uxrf_struct,'blur',gamma);
        % uxrf_montage plots all of the imported maps and adjust the gamma using a vector of gamma values
        % gamma can be a single value, or left out (defaults to 1)
        % the 2nd argument is the map type; it can be any of the sub-structures listed above
    title(s(2),'KNM-ER64060 Rt P4 no filter, 20um, 40ms/pixel');
    
figure;
    imshow(cat(3,uxrf_struct.U.blur,uxrf_struct.Fe.blur,uxrf_struct.Sr.blur),uxrf_struct.Sr.Ref);
    % tri-color plot of the normalized maps
    % don't need the [] argument like above because the .blur and .norm maps are already normalized
    % providing the .Ref gives the image x and y axes in the same units as the pixel size (microns here)
    
    imwrite(cat(3,uxrf_struct.U.blur,uxrf_struct.Fe.blur,uxrf_struct.Sr.blur),'Rt P4 U-Fe-Sr.tiff'); % save what you want

figure;
    imshow(cat(3,uxrf_struct.Ca.blur,uxrf_struct.Si.blur,uxrf_struct.Y.blur),uxrf_struct.Ca.Ref);
    % tri-color plot of the normalized maps
    % don't need the [] argument like above because the .blur and .norm maps are already normalized
    % providing the .Ref gives the image x and y axes in the same units as the pixel size (microns here)
    
    imwrite(cat(3,uxrf_struct.Ca.blur./2,uxrf_struct.Si.blur.*2,uxrf_struct.Y.blur),'Rt P4 Ca-Si-Y.tiff'); % save what you want
    
imwrite(cat(3,uxrf_struct.Ba.blur.*2,uxrf_struct.S.blur,uxrf_struct.Y.blur),'Rt P4 Ba-S-Y.tiff'); % save what you want
% figure;
%     fields = fieldnames(uxrf_struct);
%     for i = 1:length(fields)
%         subplot(6,4,i)
%         histogram2(uxrf_struct.(fields{i}).blur_raw(:),uxrf_struct.U.blur_raw(:),'DisplayStyle','tile');
%         % cross plot the blurred data
%         xlabel(['Blurred ',fields{i}]); ylabel('Blurred U');
%     end
%     title('Rt P4 no filter')