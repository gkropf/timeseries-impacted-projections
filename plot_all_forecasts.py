from numpy import *
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import ensemble, linear_model
from statsmodels.tsa.seasonal import seasonal_decompose
import math, itertools

# Set params
year_start = 2019
week_start = 10
plot_metric = 'revenue'
metric_suffix = '$'


# Read data
real_df = pd.read_csv(f'Output/{year_start}_real.csv', header=0)
proj_df = pd.read_csv(f'Output/{year_start}_projected.csv', header=0)
all_hierarchies = list(sort(list(set(proj_df['hierarchy'].values))))

real_df = real_df[real_df['metric']==plot_metric]
proj_df = proj_df[proj_df['metric']==plot_metric]

num_columns = min(len(all_hierarchies),2)
num_rows = min(math.ceil(len(all_hierarchies)/2),3)
num_batchs = math.ceil(len(all_hierarchies)/6)


for batch in range(num_batchs):
	list_hierarchies = all_hierarchies[(batch*6):((batch+1)*6)]
	fig = plt.figure(figsize=(15*(num_columns/2),10*(num_rows/3)), dpi=200)
	for k in range(len(list_hierarchies)):
		plot_hierarchy = list_hierarchies[k]
		plot_real_df = real_df[real_df['hierarchy'] == plot_hierarchy]
		plot_proj_df = proj_df[proj_df['hierarchy'] == plot_hierarchy]

		all_stores = list(set(plot_real_df['store_id'].values))
		proj_stores = list(set(plot_proj_df['store_id'].values))
		plot_real_df = plot_real_df[plot_real_df['store_id'].isin(proj_stores)]

		plot_real_df = plot_real_df.groupby(['year','week_num']).sum()[['value']]
		plot_proj_df = plot_proj_df.groupby(['year','week_num']).sum()[['projected_value']]

		plot_real_df.reset_index(inplace=True)
		plot_proj_df.reset_index(inplace=True)
		plot_df = pd.merge(plot_real_df, plot_proj_df, how='outer')
		plot_df.index = [str(x)+'-WK'+('0'*(y<10))+str(y) for (x,y) in zip(plot_df['year'].values,plot_df['week_num'])]

		group_vals = real_df.groupby('hierarchy').sum()['value']
		perc_all = group_vals[plot_hierarchy]/group_vals.sum()

		# Match proj with actual on day of split
		for i in range(1,week_start-1):
			ind = plot_df[(plot_df['year']==year_start) & (plot_df['week_num']==i)].index.values[0]
			plot_df.at[ind,'projected_value'] = nan

		ind = plot_df[(plot_df['year']==year_start) & (plot_df['week_num']==week_start-1)].index.values[0]
		plot_df.at[ind,'projected_value'] = plot_df.loc[ind, 'value']

		ax = fig.add_subplot(num_rows,num_columns,k+1)
		ax.plot(arange(6,len(plot_df)),plot_df.iloc[6:,:]['value'].values,'-',color='#d45087',label=f'Actual {plot_metric}')
		ax.plot(arange(6,len(plot_df)),plot_df.iloc[6:,:]['projected_value'].values,'--',color='#003f5c',label=f'Projected {plot_metric}')
		ax.set_xticks(25*arange(0,len(plot_df)//25+1)-7)
		ax.set_xticklabels([plot_df.index[x] for x in ax.get_xticks()], rotation=30)
		ax.set_yticklabels([metric_suffix+str(int(x/1000))+'K' for x in ax.get_yticks()])

		ylim = ax.get_ylim()
		ax.plot([arange(len(plot_df))[plot_df.index==ind][0],arange(len(plot_df))[plot_df.index==ind][0]], ylim,'k--',linewidth=.6)
		ax.axvspan(0,arange(len(plot_df))[plot_df.index==ind][0],color="gray",alpha=.2)
		ax.set_ylim(ylim)
		ax.set_xlim([6,len(plot_df)])
		ax.set_title(plot_hierarchy+f' ({round(100*perc_all,1)}% of Total)')
		ax.legend(loc='upper left')

		fig.tight_layout()
		fig.savefig(f'Output/{year_start}_projected_{plot_metric}_batch{batch}.png')


