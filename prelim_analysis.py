
# coding: utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as mpl
path_csv = r'file_path_here'   
rides = pd.read_csv(path_csv, sep=',',parse_dates = ['convert_tz(rdd.created_date, \'UTC\', \'US/Central\')','convert_tz(r.started_on, \'UTC\', \'US/Central\')','convert_tz(r.completed_on, \'UTC\', \'US/Central\')'])
trial = rides.rename(columns = {'id':'driver_id','convert_tz(rdd.created_date, \'UTC\', \'US/Central\')':'dispatched_on','convert_tz(r.started_on, \'UTC\', \'US/Central\')':'started_on','convert_tz(r.completed_on, \'UTC\', \'US/Central\')':'completed_on'})
trial.dropna(axis=0,how='any',subset =['dispatch_location_lat','dispatch_location_long','start_location_lat', 'start_location_long','end_location_lat', 'end_location_long','dispatched_on','started_on','completed_on'],inplace=True)
#dropping rows where any locations or any time values are missing

trial.loc[:,'day_of_ride'] = pd.Series(trial['started_on'].dt.weekday_name)
trial.loc[:,'time_diff'] = pd.Series((trial['completed_on'] - trial['started_on']).astype('timedelta64[h]'))
#rides = rides[rides.time_diff < 10]
trial = trial[(trial.start_location_lat != trial.end_location_lat) & (trial.start_location_long != trial.end_location_long)]
#filtering out trips where the start and end locations are the same
#check what the index is here - filtering out rows means index goes missing, so will have to reset it before you do shift

trial = trial[(trial.started_on > trial.dispatched_on) | (trial.completed_on > trial.started_on)]

#removing the trips where the start and dispatch locations are the same - not interested in trips where no idle behavior is visible


# In[19]:


trial.dtypes


# In[7]:


get_ipython().run_line_magic('matplotlib', 'inline')
ridesperday = trial['day_of_ride'].value_counts().reset_index()
ridesperday.columns = ['day_of_ride', 'Number of rides']
days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday']
mapping = {day: i for i, day in enumerate(days)}
key = ridesperday['day_of_ride'].map(mapping)
ridesperday = ridesperday.iloc[key.argsort()].set_index('day_of_ride')
my_plot = ridesperday.plot(kind='bar', title ="Rides per Day", figsize=(6, 6), legend=True, fontsize=12)
my_plot.set_xlabel("Day of Ride", fontsize=12)
my_plot.set_ylabel("Number of Rides", fontsize=12)



# In[16]:


fareperday = trial.groupby(['day_of_ride'],as_index=False)['total_fare'].mean()
fareperday.columns = ['Day_of_Ride', 'Average Fare']
days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday']
mapping = {day: i for i, day in enumerate(days)}
key = fareperday['Day_of_Ride'].map(mapping)
fareperday = fareperday.iloc[key.argsort()].set_index('Day_of_Ride')
my_plot_fare = fareperday.plot(kind='bar', title ="Average Fare per Day", figsize=(6, 6), legend=True, fontsize=12)
my_plot_fare.set_xlabel("Day of Ride", fontsize=12)
my_plot_fare.set_ylabel("Average Fare per Day($)", fontsize=12)


# In[45]:


merged.loc[merged['time_diff'] > 10 , ['total_fare','start_location_long','start_location_lat','end_location_long','end_location_lat','time_diff']]


# In[21]:




