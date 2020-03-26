from numpy import *
import pandas as pd
import matplotlib.pyplot as plt
import itertools
import sys
from forecast_methods import *

# Set params
year_start = 2019
week_start = 10
metric_list = ['revenue','units']
method = 'lag_comp' # can be 'lag_comp', 'decomp_LS', or 'decomp_arima'
input_file = 'sample_input_data.csv'

# Read data in and format data to have year-over-year mathcing week numbers (ie. Dec 25 is always in week 52).
day_exclude = (1,1)
month_days = array([31,28,31,30,31,30,31,31,30,31,30,31])
month_days = [[(i+1,k) for k in range(1,month_days[i]+1)] for i in arange(12)]
month_days = [item for sublist in month_days for item in sublist if item!=day_exclude]
week_nums = [7*[i] for i in range(1,53)]
week_nums = [item for sublist in week_nums for item in sublist]
week_df = pd.DataFrame()
week_df['month_day'] = month_days
week_df['week_num'] = week_nums

pds_data = pd.read_csv(input_file, header=0)
pds_data['year'] = [int(x.split('-')[0]) for x in pds_data['date_day'].values]
pds_data['month_day'] = [(int(x.split('-')[1]),int(x.split('-')[2])) for x in pds_data['date_day'].values]
pds_data = pd.merge(pds_data, week_df).groupby(['hierarchy','store_id','year','week_num']).sum()[['revenue','units']]
pds_data.reset_index(inplace=True)
pds_data.sort_values(['hierarchy','store_id','year','week_num'], inplace=True)
pds_data = pds_data[pds_data['units']>=1]


# Set up dataframe that matches every stores first year of sales for each category. This average
# will be used to make predictions for newly opened stores.
pds_data['total_week_num'] = 52*pds_data['year']+pds_data['week_num']
open_dates = pds_data.groupby(['hierarchy','store_id']).min()[['total_week_num']]
open_dates.columns = ['min_total_week_num']
open_dates.reset_index(inplace=True)
first_year_data = pd.merge(pds_data, open_dates, on=['hierarchy','store_id'])
first_year_data = first_year_data[first_year_data['total_week_num']<first_year_data['min_total_week_num']+52]
first_year_data['weeks_since_open'] = first_year_data['total_week_num']-first_year_data['min_total_week_num']+1

num_data_weeks = pd.DataFrame(first_year_data.groupby(['hierarchy','store_id']).max()['weeks_since_open'])
num_data_weeks.columns = ['num_data_weeks']
num_data_weeks.reset_index(inplace=True)
first_year_data = pd.merge(first_year_data, num_data_weeks, on=['hierarchy','store_id'])
first_year_data = first_year_data[first_year_data['num_data_weeks']==52]
first_year_data = first_year_data.groupby(['hierarchy','weeks_since_open']).mean()[['revenue','units']]
first_year_data.reset_index(inplace=True)

# Set up dataframe to store projections in.
real_df = pds_data[pds_data['year']<=year_start]
proj_df = pd.DataFrame(columns=['hierarchy','store_id','year','week_num','proj_revenue','proj_units'])


# Start projection loop, we will iterate through every hierarchy and store_id and make individual projections
# for the remainder of the year.
all_groups = sort(list(set(real_df['hierarchy'].values)))
for curr_group in all_groups:
	curr_group_data = pds_data[pds_data['hierarchy']==curr_group]
	curr_group_data = curr_group_data[curr_group_data['year']<=year_start]
	curr_group_data = curr_group_data[(curr_group_data['year']<year_start) | (curr_group_data['week_num']<week_start)]
	all_stores = sort(list(set(curr_group_data['store_id'])))
	temp_store_count = 0

	for curr_store in [x for x in all_stores if x!= 356]:
		train = curr_group_data[curr_group_data['store_id']==curr_store]
		curr_proj_df = pd.DataFrame(columns=['hierarchy','store_id','year','week_num','proj_revenue','proj_units'])
		if sum(train['units'].values)<1:
			print(curr_store)
			continue

		# get train data and zerofill between dates
		min_year = train.iloc[0]['year']
		all_dates = [(year_start,i) for i in range(1,week_start)]
		if min_year<year_start:
			all_dates += [(train.iloc[0]['year'],x) for x in arange(train.iloc[0]['week_num'],53)]
			all_dates += [x for x in itertools.product(arange(train.iloc[0]['year']+1,year_start),arange(1,53))]
		
		all_dates = pd.DataFrame(array(all_dates))
		all_dates.columns = ['year','week_num']

		# Remove leading zeros from before store opened.
		train = pd.merge(train, all_dates, how='right').sort_values(['year','week_num']).fillna(0)
		train = train.iloc[min(arange(len(train))[train[metric_list].min(axis=1)>0]):,:]
		
		# If the store has been open for less than a month, do not make projections.
		if len(train)<5:
			continue

		# If the store is closed (three consecutive weeks of zeros), do not make projections.
		if max(train.iloc[-3:,:][metric_list].values.reshape(-1))<0.001:
			continue

		# Make projections for remainder of year for each metric.
		for metric in metric_list:
			timeseries = train[metric].values

			# If we have less than a year of data, use the average first year sales
			if len(timeseries)<53:
				avg_first_year = first_year_data[first_year_data['hierarchy']==curr_group][metric].values
				curr_proj_df['proj_'+metric] = (mean(timeseries)/mean(avg_first_year))*avg_first_year
			else:
				if method == 'lag_comp':
					curr_proj_df['proj_'+metric] = forecast_lag_comp(timeseries, 20, 52-week_start+1)
				elif method == 'decomp_LS':
					curr_proj_df['proj_'+metric] = forecast_decomp_LS(timeseries, 2, 52-week_start+1)
				elif method == 'decomp_arima':
					curr_proj_df['proj_'+metric] = forecast_decomp_arima(timeseries, 52-week_start+1)
				else:
					print('No forecast method selected')
					sys.exit()

		

		curr_proj_df['hierarchy'] = curr_group
		curr_proj_df['year'] = year_start
		curr_proj_df['store_id'] = curr_store
		curr_proj_df['week_num'] = arange(1,53)
		proj_df = proj_df.append(curr_proj_df)

real_df.drop('total_week_num', axis=1, inplace=True)
real_df.sort_values(['hierarchy','store_id','year','week_num']).to_csv(f'Output/{year_start}_real.csv', header=True, index=False)
proj_df.sort_values(['hierarchy','store_id','year','week_num']).to_csv(f'Output/{year_start}_projected.csv', header=True, index=False)












