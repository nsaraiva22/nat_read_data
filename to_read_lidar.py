# -*- coding: utf-8 -*-
"""
############################### READ LIDAR DATA ###############################
Created on Tue Sep 14 11:44:18 2021
@author: N.P.Saraiva

This script reads files generated by WindCube LIDAR with the extension ".sta".

INSTRUCTIONS:
-> for clean all variables use: %reset -f;
-> check the address of the folder where the data is, in PATH;
-> script works only when all files are set to the same height ranges!

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
files = sorted(glob('*.sta'))       # enter with all data in PATH:

dfs = [pd.read_csv(f, header=None, sep=";", encoding= 'unicode_escape')\
       for f in files]
alldata = pd.concat(dfs, ignore_index=True)
read = alldata[0].astype(str).tolist()

# set the first and the last files
file_i = ''.join(files[0].split('_')[1:4]).replace('20','')   # fist file
file_l = ''.join(files[-1].split('_')[1:4]).replace('20','')  # last file

# set all lines who start with ('20')
alfa, line_number = [], []
for i, info1 in enumerate(read):
    if info1.startswith('20'):
        line_number.append(i)
for ii, info2 in enumerate(line_number):
    alfa.append(read[info2])

df = pd.DataFrame(alfa)
df = df[0].str.split('\t', expand=True)
del alfa, i, info1, ii, info2

# create a datetime column
df[0] = df[0].apply(lambda x: dt.datetime.strptime(x, '%Y/%m/%d %H:%M'))

# change type to datetime column for PeriodIndex
df[0] = pd.PeriodIndex(df[0], freq = 'S')

# set datetime column as an index
df = df.set_index([0])

# finding the datetime inicial and final
d_start = read[line_number[0]].split()
d_start = d_start[0]+ ' ' + d_start[1]

d_end = read[line_number[-1]].split()
d_end = d_end[0]+ ' ' + d_end[1]

# filling the missing dates, hours, and minutes
idx = pd.DataFrame({'datetime':pd.date_range(start = d_start, end = d_end,\
    freq = '10min')})
idx = pd.PeriodIndex(idx['datetime'], freq = 'S')
df = df.reindex(idx, fill_value = np.nan)

##############################################################################
# read data of the PTH sensor (df_pth) #######################################
df_pth = df.iloc[:, 0:6]
df_pth = df_pth.rename(columns = {1: 'Int Temp (°C)', 2: 'Ext Temp (°C)',\
3: 'Pressure (hPa)', 4: 'Rel Humidity (%)', 5: 'Wiper count', 6: 'Vbatt (V)'})

# change the type (df_2)
df_pth = df_pth.astype('float')    
    
# save the TPH senror data
df_pth.to_csv(PATH2 + '/results/%(first)s_to_%(last)s_lidar_pth.csv'\
    %{'first':file_i, 'last':file_l}, na_rep = np.nan, index = True)

##############################################################################
# criate files by height (df_lidar) ##########################################
# find heigths levels intervals
h_lidar = []
for iii, info3 in enumerate(read):
    if info3.startswith('Altitudes'):
        h_lidar.append(info3)

df_h_lidar = pd.DataFrame(h_lidar)
df_h_lidar = df_h_lidar[0].str.split('\t', expand=True)

h_lidar = list(map(int, df_h_lidar.loc[0, 1:].values.tolist()))
h_int = list(range(7,(len(h_lidar )*12)+11,12))

cont1 = 0
while cont1 <= len(h_lidar)-1:
    title = 'h_%i' %h_lidar[cont1]
    locals()[title] = df.loc[:, h_int[cont1]:h_int[cont1+1]-2]
    locals()[title].insert(0, 'h', h_lidar[cont1])
    locals()[title] = locals()[title].set_axis([list(range(0,12))], axis=1,\
                                               inplace=False)
    cont1 = cont1 + 1
del cont1

# join all data by height
df_lidar = pd.DataFrame()

cont2 = 0
while cont2 <= len(df)-1:
    for v, info5 in enumerate(h_lidar):
        bravo = 'h_%i' %info5
        df_lidar = df_lidar.append(locals()[bravo].iloc[cont2])
    cont2 = cont2 + 1
del cont2

# rename columns #############################################################
df_lidar.columns = ['h (m)', 'Wind Speed (m/s)', 'Wind Speed Dispersion (m/s)'\
, 'Wind Speed min (m/s)', 'Wind Speed max (m/s)', 'Wind Direction (°)',\
'Z-wind (m/s)', 'Z-wind Dispersion (m/s)', 'CNR (dB)', 'CNR min (dB)',\
'Dopp Spect Broad (m/s)', 'Data Availability (%)']
    
df_lidar = df_lidar.astype('float')          # change to float
df_lidar = df_lidar.replace({'NaN':np.nan})  # replace the nan's

# save all data by height ####################################################
df_lidar.to_csv(PATH2 + '/results/%(first)s_to_%(last)s_lidar_profile.csv'\
    %{'first':file_i, 'last':file_l}, na_rep = np.nan, index = True,\
    index_label = 'datetime')

# know time duration of the script ###########################################
print('runtime: ', dt.datetime.now() - startTime)
print('Number of file(s):', len(files))
print(len(h_lidar),'measuring heights:', h_lidar)