
# coding: utf-8

import pandas as pd
import numpy as np
path_csv = r'C:\Users\mital\Desktop\IOE 590 - Prof. Saigal\rides_withstartedon\rides.csv (1)\rides_.csv'   
rides = pd.read_csv(path_csv, sep=',',parse_dates = ['convert_tz(rdd.created_date, \'UTC\', \'US/Central\')','convert_tz(r.created_date, \'UTC\', \'US/Central\')','convert_tz(r.completed_on, \'UTC\', \'US/Central\')'])

trial = rides.rename(columns = {'id':'driver_id','convert_tz(rdd.created_date, \'UTC\', \'US/Central\')':'dispatched_on','convert_tz(r.created_date, \'UTC\', \'US/Central\')':'started_on','convert_tz(r.completed_on, \'UTC\', \'US/Central\')':'completed_on'})
trial.dropna(axis=0,how='any',subset =['dispatch_location_lat','dispatch_location_long','start_location_lat', 'start_location_long','end_location_lat', 'end_location_long','dispatched_on','started_on','completed_on'],inplace=True)
#dropping rows where any locations or any time values are missing

trial = trial[(trial.start_location_lat != trial.end_location_lat) & (trial.start_location_long != trial.end_location_long)]
#filtering out trips where the start and end locations are the same
#check what the index is here - filtering out rows means index goes missing, so will have to reset it before you do shift
trial = trial[(trial.started_on >= trial.dispatched_on) | (trial.completed_on >= trial.started_on)]
trial = trial[(trial.dispatch_location_lat != trial.start_location_lat) & (trial.dispatch_location_long != trial.start_location_long)]
#removing the trips where the start and dispatch locations are the same - not interested in trips where no idle behavior is visible
trial['date_of_ride'] = trial['dispatched_on'].dt.date
trial.sort_values(by = ['driver_id', 'dispatched_on'], inplace=True)
trial = trial.reset_index(drop=True) #resets index and keeps it in same column with continuous values

trial = trial[[ 'driver_id', 'rating', 'dispatch_location_lat','dispatch_location_long', 'dispatched_on', 'status', 'requested_car_category','start_location_lat', 'start_location_long', 'started_on','end_location_lat', 'end_location_long', 'completed_on', 'date_of_ride']]#filter out unnecessary columns with car details
trial['end_lat_prev'] = trial['end_location_lat'].shift(1)
trial['end_long_prev'] = trial['end_location_long'].shift(1)
#for all trips irrespective of the driver

trial['end_lat_prev'].fillna(trial.dispatch_location_lat, inplace=True)
trial['end_long_prev'].fillna(trial.dispatch_location_long, inplace=True)
#for all trips in the first row - there will be no end location of the previous trip

pd.options.mode.chained_assignment = None #to prevent Python from throwing a settingwithcopy warning
#taking the dispatch location of same trip where the driver changes or date changes as compared to the previous trip
for i in range(1,len(trial.index)):
    if (trial.driver_id[i-1] != trial.driver_id[i]) or (trial.date_of_ride[i-1] != trial.date_of_ride[i]):    
        trial['end_lat_prev'][i] = trial['dispatch_location_lat'][i]
        trial['end_long_prev'][i] = trial['dispatch_location_long'][i]

trial = trial[(trial.end_lat_prev != trial.end_location_lat) & (trial.end_long_prev != trial.end_location_long)]
trial = trial.reset_index(drop=True)
trial.reset_index(inplace=True) #new index which contains continuous values should be ride id to avoid issues in shift 
trial = trial.rename(columns = {'index':'ride_id'})

from datetime import datetime, timedelta
trial['actual_wait_time'] = (trial['dispatched_on'] - 
                             trial['completed_on'].shift(1))
trial['actual_wait_time'] = trial['actual_wait_time'].dt.seconds/60
#trial['actual_wait_time']=trial['actual_wait_time'].apply(lambda x: x + timedelta(days=1) if x < 0 else x)
#actual wait times

test = trial.head(n=10) #all points have been plotted for the test data set-actual file size is 1 million data points

import gmaps
gmaps.configure(api_key = "##enter API key here")
import googlemaps
gmaps = googlemaps.Client(key="##enter API key here")
import json
from googleplaces import GooglePlaces, types, lang
api_key = "##enter API key here"

google_places = GooglePlaces(api_key)

distance = []
for i in range(len(test.index)):
    origin = (test['end_lat_prev'][i], test['end_long_prev'][i])
    destin = (test['dispatch_location_lat'][i], test['dispatch_location_long'][i])
    matrix = gmaps.distance_matrix(origin, destin, mode="driving")
    distance.append(matrix['rows'][0]['elements'][0]['distance']['value'])
distance = [x*0.000621  for x in distance]
test['ed_dist'] = distance
#distance through fastest route in miles based on CURRENT traffic conditions, not on day when ride ACTUALLY took place
test['less_than_5'] = np.where(test['ed_dist']<=5, 'Y', 'N')

duration = []
for i in range(len(test.index)):
    origin = (test['end_lat_prev'][i], test['end_long_prev'][i])
    destin = (test['dispatch_location_lat'][i], test['dispatch_location_long'][i])
    matrix = gmaps.distance_matrix(origin, destin, mode="driving")
    duration.append(matrix['rows'][0]['elements'][0]['duration']['value'])
test['Google_waittime'] = duration

places = []
locations = []
for i in range(len(test.index)):
    sourceloc = (test['dispatch_location_lat'][i], test['dispatch_location_long'][i])
    query_result = google_places.nearby_search(lat_lng={'lat': sourceloc[0],  'lng': sourceloc[1]}, radius=1609, types = [types.TYPE_RESTAURANT] or [types.TYPE_PARKING])
    subplaces = []
    sublocations = []
    for subplace in query_result.places:
            subplaces.append(subplace.name)
    for subloc in query_result.places:
            sublocations.append(subloc.geo_location)
    places.append(subplaces) 
    locations.append(sublocations)

test['places_of_int'] = places
test['locations_of_int'] = locations
#both places and locations are stored as dictionary inside a list inside a Series
import gmaps.datasets

pd.options.mode.chained_assignment = None
test["dispatch_info"] = "Driver:" + test["driver_id"].map(str) + " Ride_ID:" + test["ride_id"].map(str)# + " Dispatched_on:" + test["dispatched_on"].map(str)
#Prepping for dispatch layer - plots dispatch points
test["start_info"] = "Driver:" + test["driver_id"].map(str) + " Ride_ID:" + test["ride_id"].map(str)# + " Started On:" + test["started_on"].map(str)
test["end_info"] = "Driver:" + test["driver_id"].map(str) + " Ride_ID:" + test["ride_id"].map(str)# + " Completed On:" + test["completed_on"].map(str)
#Prepping for start and end layers 
dispatch_loc = test[['dispatch_location_lat','dispatch_location_long']]
dispatch_info_lst = test['dispatch_info'].values.tolist()
dispatch_layer = gmaps.symbol_layer(dispatch_loc, fill_color = "rgba(200, 0, 0, 1)", stroke_color = "rgba(200, 0, 0, 1)", scale=3, info_box_content = dispatch_info_lst)
#Creating dispatch layer - plots dispatch points
start_loc = test[['start_location_lat','start_location_long']]
start_info_lst = test['start_info'].values.tolist()
start_layer = gmaps.symbol_layer(start_loc, fill_color = "rgba(0, 200, 0, 1)", stroke_color = "rgba(0, 200, 0, 1)", scale=3, info_box_content = start_info_lst)
#Creating Start Layer - plots start points
end_loc = test[['end_location_lat','end_location_long']]
end_info_lst = test['end_info'].values.tolist()
end_layer = gmaps.symbol_layer(end_loc, fill_color = "rgba(0,0, 200, 1)", stroke_color = "rgba(0, 0, 200, 1)", scale=3, info_box_content = end_info_lst)
#Creating End Layer - - plots end points

dispatch_lat =[]
dispatch_lng =[]
place_name = []
places_lat = []
places_lng = []

for j in range(len(test.index)):
    for i in range(len(test['locations_of_int'][0])): #this will be 20 coz there are 20 results
        dispatch_lat.append(test['dispatch_location_lat'][j])
        dispatch_lng.append(test['dispatch_location_long'][j])
        place_name.append(test['places_of_int'][j][i])
        places_lat.append(test['locations_of_int'][j][i]['lat']) #refers to the latitude in the jth row of df and ith element of list
        places_lng.append(test['locations_of_int'][j][i]['lng'])
test_place = pd.DataFrame({'dispatch_lat':dispatch_lat, 'dispatch_lng':dispatch_lng,'place_name':place_name,'latitude':places_lat,'longitude':places_lng})  

test_place['latitude'] = test_place['latitude'].map(float)
test_place['longitude'] = test_place['longitude'].map(float)
interest_loc = test_place[['latitude','longitude']]
interest_info_lst = test_place['place_name'].values.tolist()
interest_layer = gmaps.symbol_layer(interest_loc, fill_color = "rgba(255,140,0, 1)", stroke_color = "rgba(255,140,0, 1)", scale=3, info_box_content = interest_info_lst)
#Creating layer for places of interest - plots the places as points with tags on top

end_loc_prev = test[['end_lat_prev','end_long_prev']]
end_info_lst = test['end_info'].values.tolist()
prev_end_layer = gmaps.symbol_layer(end_loc_prev, fill_color = "rgba(238,130,238, 1)", stroke_color = "rgba(238,130,238, 1)", scale=3)

disp_lat = test['dispatch_location_lat'].tolist()
disp_long = test['dispatch_location_long'].tolist()
start_lat = test['start_location_lat'].tolist()
start_long = test['start_location_long'].tolist()
end_lat = test['end_location_lat'].tolist()
end_long = test['end_location_long'].tolist()
end_lat_prev = test['end_lat_prev'].tolist()
end_long_prev = test['end_long_prev'].tolist()

fig = gmaps.figure()
for i in range(5):
    prev_end = (end_lat_prev[i],end_long_prev[i])
    dispatch = (disp_lat[i], disp_long[i])
    start = (start_lat[i], start_long[i])
    end = (end_lat[i], end_long[i])
    route = gmaps.directions_layer(prev_end,end,waypoints = [dispatch,start])
    fig.add_layer(route)
    
fig.add_layer(prev_end_layer)
fig.add_layer(dispatch_layer)
fig.add_layer(start_layer)
fig.add_layer(end_layer)
fig.add_layer(interest_layer)

fig._map.layout.width = '1000px'
fig._map.layout.height = '1000px' 

fig
#red - dispatch
#green - start
#blue - end
#orange - places of interest

from ipywidgets.embed import embed_minimal_html
embed_minimal_html('export3.html', views=[fig])
#does not contain the directions layer - only plotted points




