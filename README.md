# Time Series Forecasting
We built this repository to help retailers prepare for, and evaluate the impact of, the COVID-19 epidemic. This repository can be used to forecast future timeseries values, and compare these forecasts against observed values to measure the impact-to-date of fleet-wide influences. For more detail on the motivation behind this project, please see https://marketdial.com/covid-19-model/.

The repository consists of python scripts that utilize various methods of forecasting, and a generic excel model that can be used to track and estimate effects at the store, department, and state level.

## 1. Code Usage
The forecast algorithm uses an input CSV in which each row represents the total sales for a given store, on a particular day, at a specified hierarchy level (Grocery/Infant etc.). The CSV must contain three index columns (hierarchy_id, store_id, date_day) followed by any number of tracked metric columns (revenue/units etc.). The date_day must be in YYYY-MM-DD format. The *sample_input_data.csv* illustrates the expected input data format. Along with the input data, the user will specify the year they want to make projections for. 

The forecast algorithm will iterate through every store-category pair, make individual weekly projections, and join all the data into a data frame that is saved into the Output folder. The data frame has four index columns: hierarchy, store_id, year, week, and an additional projected column for each metric column in the input file. An example output is given in *Output/2019_projected.csv*.

### 1.1 File descriptions and order of execution.
The first file to be executed is run_forecasts.py. This file will read data from a pre-defined location and, using the forecasting functions it imports from forecasts_methods.py, save two files containing the real and projected metric values into the Output folder. 

Before running the projections for your year of interest, we recommend running the projections for the same time last year to gauge the model's performance on your data. Once *run_forecasts.py* has been run with last year's data, you can run *evaluate_model_errors.py* which will output a CSV containing the model errors for each hierarchy. These errors are at the total fleet-level (i.e. the prediction errors for any individual store will be higher than for the total fleet).

You can then optionally run plot_all_forecasts.py which will read the output from run_forecasts.py, iterate through each hierarchy, aggregate the data across all stores, and save plots of the real vs. projected values into the Output folder. 

![alt text](Output/2019_projections0.png "Example of output from plot_all_forecasts.py")

### 1.2 File parameters.
There are only a few parameters that need to be adjusted within with each script to get started. 

For run_forecasts.py, the user must set:
```
year_start: the year the user wants to make projections for.
week_start: the week where the projections should start (i.e. a value of 10 means that you want to use the first 9 weeks of the year as part of the training data).
metric_list: should contain all the metrics that are present as columns in your data input file.
method: selects which of three methods should be used to make the projections. A description of each method is given below.
input_file: file location of the input data.
```

And for plot_all_forecasts.py, the user only needs to set:
```
year_start: same value that was used in run_forecasts.py
week_start: "                                          "
plot_metric: the metric to be plotted.
```


## 2. Methodology Review
### 2.1. Signal-Trend Decomposition and LS Regression
This method works by using pythons built-in decomposition algorithm to split the signal into its trend and seasonal components and then forecasting the components individually. 

The trend is extracted from the signal by computing a running mean with length equal to the expected seasonality (is this case we use a 52-week running average). Once the trend is removed from the original signal, the seasonal component is removed using a convolution filter. What remains after extracting the trend and seasonal components is the raw residuals.

We project future values for the trend using weighted linear regression (we weight the more recent data higher). The seasonal component is projected repetitively. And the residual component is projected using its mean. Finally, the individual components are added back together for our projection of the original signal.

![alt text](MethodologyExamples/decompose_LS_method.png "")

### 2.2. Signal-Trend Decomposition with ARIMA Model
To make predictions with an ARIMA model, the data must be stationary after differencing with the order specified in the model. This means that ARIMA cannot natively handle seasonal data. While there are many methods for removing the seasonality (including simple differences), we again use pythons built-in function. Similar to the prior method, we make projections on the individual components and then add them together.

Alternatively, we could use a SARIMA model which models the seasonal component concurrently with the elements of the ARIMA model. However, a general-purpose SARIMA model has multiple parameters that must be carefully tuned. This generally requires looking at partial autocorrelation plots and making judgment call's on the degree of the model. To make this method more generalizable, we stick with our simpler implementation of ARIMA.

![alt text](MethodologyExamples/decompose_ARIMA_method.png "")

### 2.3. Simple Lagged Yearly Comp Method

The last projection model we implemented is the simplest and performed the best across a variety of data. This method works iteratively. It projects the next value in a sequence by computing the average yearly change of the most recent 20 weeks, and adding this average to the value observed one year ago. The method is essentially a lagged version of the signal added to a running average of itself. The *run_forecasts.py* script defaults to this method. While there are certainly more advanced methodologies available, similar to SARIMA, they generally require advanced tuning specific to each data set.

![alt text](MethodologyExamples/lag_comp_method.png "")




## 3. Spreadsheet Scenario Planning
This spreadsheet tabs are colored by their purpose: (1) outputs = green (2) scenario-planning adjustable fields = orange (3) input data = blue.
### 3.1. Add Data
To use this spreadsheet, you will need prediction and actual data on the store-category-week level as produced from the above Python model (run_forecasts.py). The current spreadsheet is built around revenue and units sold metrics but could be updated for any other metrics of interest. Data can be copy and pasted into the "Raw Predictions" and "Actual Values" tabs. Columns for store, week, category and one or two metrics should retain the same ordering as the example spreadsheet.

Store-region information can be added to the "Store State Lookup" tab.

Once the raw data has been updated, the pivot tables in the last 3 tabs should be refreshed.
### 3.2. Adjust Other Fields as Necessary
There are a few fields which will need to be hand-adjusted based on your data. For instance, the number of category columns will need to be adjusted one most of the output and adjustable-value tabs. In addition, one with other metrics may wish to adjust the revenue/units toggle or the tab and column names. Such changes may require adjustments to dependent pivot tables, formulas, etc.

### 3.3. Scenario Planning
The "Adjust Impact by State" tab allows a user to suppose that certain regional effects will be greater than others. The values represent the hypothesized percent increase or decrease from predicted values based on the state alone.

The "Adjust Category Effects" tab allows the user to adjust hypothesized percent increase or decrease from predicted values at the category-week level.
### 3.4. Outputs
These tabs summarize projected effects and effects observed so far using the raw input data and the user-adjusted scenario planning fields. The projected impact can be viewed at an overall or individual store level. The "Impact To-Date" tab summarizes impact observed by comparing predicted vs. actual for available data.
