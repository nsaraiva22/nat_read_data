# -*- coding: utf-8 -*-
"""
############################### READ TOWER DATA ###############################
Created on Mon Mar 21 11:22:29 2022
@author: N.P.Saraiva

This script reads the 20 Hz files generated by the Campebell datalogger, which
records the data from the micrometeorological station, after its conversion into
a "CSV compatible array" with the ".dat" extension.

ABOUT:
-> Data is in 20 Hz intervals.
-> This script creates two dataframes:
1. df_sonic - organizes the original data, from the 3D sonic anemometer, with
an interval of 20 Hz.
2. df_tower_s - selects a row every 0.2 s, generating a dataframe of one
data per second.

INSTRUCTIONS:
-> for clean all variables use: %reset -f;
-> check the address of the folder where the data is, in PATH;

"""

from IPython import get_ipython
get_ipython().magic('reset -sf')    # clear all variables

import datetime as dt
import os
from glob import glob
import pandas as pd
import numpy as np

startTime = dt.datetime.now()       # know the start time

# enter the path of the files here:
PATH = 'D:/natalia_read_data/to_read/data'
os.chdir(PATH)

# create PATH2, which is a previous directory
PATH2, tail = os.path.split(PATH)

# create the folder "result", if it does not exist
if os.path.exists(os.path.join(PATH2, 'results')) == False:
    os.mkdir(os.path.join(PATH2, 'results'))

##############################################################################
# read files (all) ###########################################################
files = sorted(glob('*20Hz_*.dat'))     # enter with all data in PATH

# 22 titles of columns
header = ['panel_tmpr', 'batt_volt', 'Ts', 'Ux', 'Uy', 'Uz',\
'sonic_checksum_flg', 'diag_sonic', 'in_bytes_str', 'Vx_1', 'Vy_1', 'diag_1',\
'Vx_2', 'Vy_2', 'diag_2', 'Vx_3', 'Vy_3', 'diag_3', 'T_probe', 'RH_probe',\
'press', 'P']

dfs = [pd.read_csv(f, header = None, sep = ',', names =\
['x', 'year', 'j_day', 'h_min', 'sec'] + header, dtype = str) for f in files]

##############################################################################
# read data (df_tower) #######################################################    
df_tower = pd.concat(dfs, ignore_index = True)

# organize date colunm
df_tower['date'] = pd.to_datetime(df_tower['j_day'], format = '%j')
df_tower['date'] = df_tower['date'].dt.strftime('%m-%d')
df_tower['dt1'] = df_tower[['year', 'date']].agg('-'.join, axis=1)

# set the first and the last files
file_i = df_tower.loc[df_tower.index[0], 'dt1'][2:].replace('-','_')   # fist
file_l = df_tower.loc[df_tower.index[-1], 'dt1'][2:].replace('-','_')  # last

# organize hour, minute, and second colunms
df_tower['hour'] = df_tower['h_min'].str[-4:-2]
df_tower['hour'] = df_tower['hour'].apply(lambda x: '{0:0>2}'.format(x))
df_tower['min'] = df_tower['h_min'].str[-2:]
df_tower['dt2'] = df_tower[['hour', 'min', 'sec']].agg(':'.join, axis=1)

# organize datetime colunm
df_tower['datetime'] = df_tower[['dt1', 'dt2']].agg(' '.join, axis=1)
df_tower['datetime'] = pd.to_datetime(df_tower['datetime'],\
format = '%Y-%m-%d %H:%M:%S.%f')

df_tower = df_tower.drop(columns=['x', 'year', 'j_day', 'h_min', 'date',\
'dt1', 'hour', 'min', 'dt2'])
    
df_tower = df_tower[['datetime', 'sec'] + header]

# some columns are "float"
df_tower[['sec', 'panel_tmpr', 'batt_volt', 'Ts', 'Ux', 'Uy', 'Uz',\
'sonic_checksum_flg', 'diag_sonic', 'Vx_1', 'Vy_1', 'diag_1', 'Vx_2', 'Vy_2',\
'diag_2', 'Vx_3', 'Vy_3', 'diag_3', 'T_probe', 'RH_probe', 'press', 'P']]\
= df_tower[['sec', 'panel_tmpr', 'batt_volt', 'Ts', 'Ux', 'Uy', 'Uz',\
'sonic_checksum_flg', 'diag_sonic', 'Vx_1', 'Vy_1', 'diag_1', 'Vx_2', 'Vy_2',\
'diag_2', 'Vx_3', 'Vy_3', 'diag_3', 'T_probe', 'RH_probe', 'press', 'P']]\
.astype('float64')

##############################################################################
# for filling the missing rows information ###################################
# finding the datetime inicial and final
d_start = df_tower.loc[df_tower.index[0], 'datetime']
d_end = df_tower.loc[df_tower.index[-1], 'datetime']

# change type to column date for PeriodIndex
df_tower['datetime'] = pd.PeriodIndex(df_tower['datetime'], freq = '50ms')

# set 'date' as an index
df_tower = df_tower.set_index(['datetime'])

# filling the missing dates, hours, and minures
idx = pd.DataFrame({'datetime':pd.date_range(start = d_start, end = d_end,\
freq = '50ms')})
idx = pd.PeriodIndex(idx['datetime'], freq = '50ms')
df_tower = df_tower.reindex(idx, fill_value = np.nan)
del idx, d_start, d_end                 # clean some variables

##############################################################################
# saving sonic anemometer 3D data (df_sonic) #################################
df_sonic = df_tower[['Ts', 'Ux', 'Uy', 'Uz']]

df_sonic.to_csv(PATH2 + '/results/%(first)s_to_%(last)s_ane_sonic_3d_20hz.csv'\
    %{'first':file_i, 'last':file_l}, na_rep = np.nan, index = True)
    
##############################################################################
# dt_tower_s #################################################################
# creates a dataframe with one data every 0.2 seconds
alfa = []
cont = 0
while cont < 60:
    for i in range(len(df_tower)):
        if df_tower['sec'].iloc[i] == cont:
            alfa.append(df_tower.iloc[i])
    cont = cont + 1

df_tower_s = pd.DataFrame(alfa)
df_tower_s = df_tower_s.sort_index()  # sort object by labels
del alfa, cont, dfs, i, tail          # clean some variables

df_tower_s = df_tower_s.drop(columns=['sec'])

##############################################################################
# save data per second --> 1 Hz (df_tower_s) #################################
df_tower_s.to_csv(PATH2 + '/results/%(first)s_to_%(last)s_tower_1hz.csv'\
    %{'first':file_i, 'last':file_l}, na_rep = np.nan, index = True)

##############################################################################
print('runtime: ', dt.datetime.now() - startTime)
print('Number of file(s):', len(files))
