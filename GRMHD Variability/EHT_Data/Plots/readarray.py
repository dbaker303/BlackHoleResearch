################################################################
#
# functions to read SMA/ALMA only data in ascii format and return
# the measured flux from the array as a function of time
#
# DP July 4, 2019
#
################################################################
import numpy as np                    # imports library for math
import matplotlib.pyplot as plt       # import library for plots
import pandas as pd                   # import pandas for reading data


################################################################
#
# function readSMA(fname)
#
# Reads SMA data from the ascii file [fname] with the following columns
# ctime, flux, flux error
# Example line of the ascii file:
# 12.231944 2.319236 0.097707
#
# Returns three numpy arrays:
# ctime: UT time in hours
# flux : observed flux
# flux_err: flux error
#
# DP July 5, 2019
#
################################################################

def readSMA(fname):
    alldataRead1 = pd.read_csv(fname,sep=',') # read space-delimitted data from file

    alldataRead=alldataRead1.to_numpy()       # convert the pandas dataframe to array

    ctime=alldataRead[:,0]                 # time is column 1
    flux=alldataRead[:,1]                  # flux is column 2
    flux_err=alldataRead[:,2]              # flux error is column 3

    return ctime,flux,flux_err

################################################################
#
# function readALMA(fname)
#
# Reads SMA data from the ascii file [fname] with the following columns
# scan ID SPW time UT amp sth sth_err core_amp core_err Nant
# Example line of the ascii file:
# scan   21  3 time  8.4033  amp  1.525  0.011   2.327  0.034   31
#
# Returns three numpy arrays:
# ctime: UT time in hours
# flux : observed flux
# flux_err: flux error
#
# DP July 5, 2019
#
################################################################

def readALMA(fname):
#    alldataRead1 = pd.read_fwf(fname) # read space-delimitted data from file
#    alldataRead=alldataRead1.to_numpy()       # convert the pandas dataframe to array

    alldataRead=np.genfromtxt(fname,delimiter=',',skip_header=1)
    ctime=alldataRead[:,0]                 # time is column 1
    flux=alldataRead[:,1]                  # flux is column 2
    flux_err=alldataRead[:,2]              # flux error is column 3

    return ctime,flux,flux_err

