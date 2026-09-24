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
        imshow(imadjust(Map.(elements{i}).(type),[],[],gamma(i)),Map.(elements{i}).Ref);
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