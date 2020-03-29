from numpy import *
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import ensemble, linear_model
from statsmodels.tsa.seasonal import seasonal_decompose
import itertools


# Set params
year_start = 2019
week_start = 10

# Read in data
real_df = pd.read_csv(f'Output/{year_start}_real.csv', header=0)
proj_df = pd.read_csv(f'Output/{year_start}_projected.csv', header=0)
all_hierarchies = list(sort(list(set(proj_df['hierarchy'].values))))
metric_list = list(set(proj_df['metric'].values))

# Remove all data that was used in training the model (data before the year-week start).
proj_df = proj_df[(52*proj_df['year']+proj_df['week_num']) >= (52*year_start+week_start)]

# Iterate through each hierarchy, aggregate projections across all stores, and compare against
# the aggregation of the observed data.
model_evaluation = pd.DataFrame(columns=['year','hierarchy','metric','avg_weekly_value','avg_weekly_projected_value','projection_RMSE','avg_weekly_percent_err'])
df_row = 0 
for k in range(len(all_hierarchies)):
	current_hierarchy = all_hierarchies[k]
	current_real_df = real_df[real_df['hierarchy'] == current_hierarchy]
	current_proj_df = proj_df[proj_df['hierarchy'] == current_hierarchy]
	combined_df = pd.merge(current_real_df,current_proj_df, on=['year','week_num','store_id','metric']).groupby(['year','week_num','metric']).sum()[['value','projected_value']]
	combined_df = combined_df.reset_index().sort_values(['metric','year','week_num'])

	for i in range(len(metric_list)):
		metric = metric_list[i]
		combined_df_metric = combined_df[combined_df['metric']==metric]
		metric_real = combined_df_metric['value'].mean()
		metric_proj = combined_df_metric['projected_value'].mean()
		metric_RMSE = sqrt(sum((combined_df_metric['projected_value'].values-combined_df_metric['value'].values)**2))
		metric_prcnt_err = 100*median(abs((combined_df_metric['projected_value'].values-combined_df_metric['value'].values)/combined_df_metric['value'].values))
		model_evaluation.loc[df_row] = [year_start,current_hierarchy,metric,metric_real,metric_proj,metric_RMSE,metric_prcnt_err]
		df_row += 1


model_evaluation.to_csv(f'Output/{year_start}_projection_errors.csv', header=True, index=False)


