function Map = import_uxrf(file_search,px_size,blur_sd)
    files = dir(file_search);
    for i = 1:length(files)
        Img = img_proc_uxrf(files(i).name,px_size,blur_sd);
        element = files(i).name(find(files(i).name=='_',1,'last')+1:end-4);
        element = erase(element,' ');
        Map.(element) = Img;
    end
end