from numpy import *
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import ensemble, linear_model
from statsmodels.tsa.seasonal import seasonal_decompose
import itertools


# Set params
year_start = 2019
week_start = 10
metric_list = ['revenue','traffic']

# Read in data
real_df = pd.read_csv(f'Output/{year_start}_real.csv', header=0)
proj_df = pd.read_csv(f'Output/{year_start}_projected.csv', header=0)
all_hierarchies = list(sort(list(set(proj_df['hierarchy'].values))))

# Remove all data that was used in training the model (data before the year-week start).
proj_df = proj_df[(52*proj_df['year']+proj_df['week_num']) >= (52*year_start+week_start)]

# Iterate through each hierarchy, aggregate projections across all stores, and compare against
# the aggregation of the observed data.
model_evaluation = zeros((len(all_hierarchies),4*len(metric_list)))
for k in range(len(all_hierarchies)):
	current_hierarchy = all_hierarchies[k]
	current_real_df = real_df[real_df['hierarchy'] == current_hierarchy]
	current_proj_df = proj_df[proj_df['hierarchy'] == current_hierarchy]
	combined_df = pd.merge(current_real_df,current_proj_df, on=['year','week_num','store_id']).groupby(['year','week_num']).sum()

	for i in range(len(metric_list)):
		metric = metric_list[i]
		metric_real = combined_df[metric].mean()
		metric_proj = combined_df['proj_'+metric].mean()
		metric_RMSE = sqrt(sum((combined_df['proj_'+metric].values-combined_df[metric].values)**2))
		metric_prcnt_err = 100*median(abs((combined_df['proj_'+metric].values-combined_df[metric].values)/combined_df[metric].values))
		model_evaluation[k,(4*i):(4*(i+1))] = [metric_real,metric_proj,metric_RMSE,metric_prcnt_err]

model_evaluation = pd.DataFrame(model_evaluation)
model_evaluation.columns = [x for metric in metric_list for x in \
	[f'{year_start}avg_weekly_{metric}', f'{year_start}avg_weekly_projected_{metric}', \
	f'{metric}_projection_RMSE',f'{metric}_avg_weekly_prcnt_err']]

model_evaluation.insert(0,'hierarchy',all_hierarchies)
model_evaluation.to_csv(f'Output/{year_start}_projection_errors.csv', header=True, index=False)


