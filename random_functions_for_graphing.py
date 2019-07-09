def bar_and_line_chart(
    grouped_series_data,
    grouped_series_count_data,
    figsize, color,
    figtitle,
    axis1_ylabel,
    axis1_legend_text,
    axis2_ylabel,
    axis2_legend_text
):
    # Figure and axes creation
    figure, axis = plt.subplots(nrows=1, ncols=1, figsize=figsize)
    second_axis = figure.add_axes()
    figure.suptitle(figtitle, fontsize=20, y=1.02)
    
    # Data creation
    grp = grouped_series_data.copy()
    grp_counts = grouped_series_count_data.copy()
    
    # If the series is missing a decade, add it as an index and set the value to zero
    for decade in range(1910, 2020, 10):
        if decade not in grp.index:
            grp.loc[decade] = 0
            grp_counts.loc[decade] = 0
            
    # Sort the series by its index to have the decades in chronological order                
    grp.sort_index(ascending=True, inplace=True)
    grp_counts.sort_index(ascending=True, inplace=True)
    
    # Set up axis1 graph
    axis1 = grp.plot(kind='bar', xticks=range(1910, 2020, 10), linewidth=3, color=color)
    axis1.set_ylabel(axis1_ylabel, fontsize=12)
    axis1.legend([axis1_legend_text], loc=2, fontsize=15)

    axis2 = axis1.twinx()
    
    # Set up axis2 graph
    axis2.plot(axis1.get_xticks(), grp_counts.values, linewidth=3, color='k')
    axis2.set_ylabel(axis2_ylabel, fontsize=12)
    axis2.legend([axis2_legend_text], loc=1, fontsize=15)
    
    plt.tight_layout()


def multiple_bar_and_line_charts(
    groupby_data_needs_separator,
    groupby_data_for_counts_needs_separator,
    data_separator_list,
    first_axes_list,
    second_axes_list,
    colors_list,
    counter_list,
    figtitle,
    figsize, 
    axis1_ylabel,
    axis2_ylabel,
):
    for separator, first_axis, second_axis, color, count in zip(data_separator_list, first_axes_list, second_axes_list, colors_list, counter_list):
        figure, axis = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        second_axis = figure.add_axes()

        if count == 0:
            figure.suptitle(figtitle, fontsize=20, y=1.02)

        grp = groupby_data_needs_separator.copy()
        grp_counts = groupby_data_for_counts_needs_separator.copy()
    
        # If the series is missing a decade, add it as an index and set the value to zero
        for decade in range(1910, 2020, 10):
            if decade not in grp.index:
                grp.loc[decade] = 0
                grp_counts.loc[decade] = 0

        # Sort the series by its index to have the decades in chronological order                
        grp.sort_index(ascending=True, inplace=True)
        grp_counts.sort_index(ascending=True, inplace=True)
    
        first_axis = grp.plot(kind='bar', xticks=range(1910, 2020, 10), linewidth=3, color=color)
        first_axis.set_ylabel(axis1_ylabel, fontsize=12)
        first_axis.legend([separator], loc=2, fontsize=15)

        second_axis = first_axis.twinx()

        second_axis.plot(first_axis.get_xticks(), grp_counts.values, linewidth=3, color='k')
        second_axis.set_ylabel(axis2_ylabel, fontsize=12)
        second_axis.legend(['counts'], loc=1, fontsize=15)
        
        if count == len(counter) - 1:
            plt.tight_layout()


def multiple_bar_and_line_charts(
    groupby_data_needs_separator,
    groupby_data_for_counts_needs_separator,
    data_separator_list,
    first_axes_list,
    second_axes_list,
    colors_list,
    counter_list,
    figtitle,
    figsize, 
    axis1_legend_text,
    axis2_legend_text,
    genres_list,
    first_axes_list,
    second_axes_list,
):
    for separator, first_axis, second_axis, color, count in zip(data_separator_list, first_axes_list, second_axes_list, colors_list, counter_list):
        figure, axis = plt.subplots(nrows=1, ncols=1, figsize=(24, 5))
        second_axis = figure.add_axes()

        if count == 0:
            figure.suptitle('Mean Domestic Gross By Genre And Decade', fontsize=20, y=1.02)

        grp = (data[data[genre]].groupby('release_decade').mean() / 1000000)['domestic_adj'].copy()
        grp_counts = data[data[genre]].groupby('release_decade')['domestic_adj'].count().copy()
    
        # If the series is missing a decade, add it as an index and set the value to zero
        for decade in range(1910, 2020, 10):
            if decade not in grp.index:
                grp.loc[decade] = 0
                grp_counts.loc[decade] = 0

        # Sort the series by its index to have the decades in chronological order                
        grp.sort_index(ascending=True, inplace=True)
        grp_counts.sort_index(ascending=True, inplace=True)
    
        axis = grp.plot(kind='bar', xticks=range(1910, 2020, 10), linewidth=3, color=color)
        axis.set_ylabel('Domestic Gross In Millions', fontsize=12)
        axis.legend([genre], loc=2, fontsize=15)

        second_axis = axis.twinx()

        second_axis.plot(axis.get_xticks(), grp_counts.values, linewidth=3, color='k')
        second_axis.set_ylabel('Number of Movies', fontsize=12)
        second_axis.legend(['counts'], loc=1, fontsize=15)
        
        if count == len(counter) - 1:
            plt.tight_layout()

# Customized for adding the counts when a percentage height is used instead of the count
# Must send in an array of the corresponding counts for each bar
def autolabel_with_count(axis, counts):
    """
    Attach a text label above each bar displaying its count
    """
    for i, val in enumerate(axis.patches):
        height = counts[i]
        
        if height == 0:
            continue
        
        axis.text(val.get_x() + val.get_width()/2, val.get_height()*1.05, '%d' % int(height), ha='center', va='bottom', fontsize=20)

def autolabel_with_count_and_percentage(axis, counts):
    """
    Attach a text label above each bar displaying its count
    """
    for i, val in enumerate(axis.patches):
        height = val.get_height()
        count = counts[i]
        
        if height == 0:
            continue
        
        axis.text(val.get_x() + val.get_width()/2, val.get_height()*1.05, '{} ({})'.format(height, count), ha='center', va='bottom', fontsize=20)