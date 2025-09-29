import numpy as np
import matplotlib.pyplot as plt
from readarray import readSMA,readALMA

#observation days
dataset=['Apr05','Apr06','Apr07','Apr10','Apr11']
dates=['April 5','April 6','April 7','April 10','April 11']

#binning intervals
intervals=[0.5, 1, 1.5, 2, 2.5, 3]


# ----SMA ANALYSIS----
for iSet in [0,1,2,3,4]:
    #load and read SMA file for given day
    SMAfname='../SMA/SM_STAND_HI_'+dataset[iSet]+'.dat'
    SMActime,SMAflux,SMAflux_err=readSMA(SMAfname)
    
    
    fsds = [] #list that stores fractional standard deviation for each bin size
    
    #loops through different bin intervals
    for time in intervals:
        
        fsd_list = [] #list of FSD for each chunk in the data
        index_list = [] #marks indicides that split bins (edges)
        
        #determines the number of intervals the data set will have for this bin size
        num_intervals = int((SMActime.max() - SMActime.min()) / time)        
        
        # Find cut indices for splitting into bins
        for n in range(num_intervals):
            difference_array = np.absolute(SMActime - (time * (n + 1) + SMActime.min()))
            index = np.argmin(difference_array)
            index_list.append(index+1)

        # Split flux data into chunks
        SMAflux_arr = np.split(SMAflux, index_list)

        # Remove trailing empty chunk if it exists (if it splits at last entry)
        if len(index_list) < len(SMAflux_arr):
            del SMAflux_arr[-1]

        # Compute FSD = std/mean for each chunk directly
        for chunk in SMAflux_arr:
            fsd_list.append(np.std(chunk) / np.mean(chunk))

        # Average FSD across all chunks for this bin size
        fsds.append(sum(fsd_list) / len(fsd_list))

    plt.plot(intervals,fsds,label="SMA "+dates[iSet])
    print(dates[iSet],np.mean(SMAflux),np.std(SMAflux)/np.mean(SMAflux),"SMA")

# ----ALMA ANALYSIS----
# Only analyze specific datasets (Apr06, Apr07, Apr11)
for iSet in [1,2,4]:
    # Load and read ALMA file for given day
    ALMAfname = '../ALMA/AA_STAND_HI_' + dataset[iSet] + '.dat'
    ALMActime, ALMAflux, ALMAflux_err = readALMA(ALMAfname)

    fsds = []  # List to store average fractional standard deviation for each bin size

    # Loop through different time bin intervals
    for time in intervals:

        fsd_list = []    # FSD values for each chunk in this bin size
        index_list = []  # Indices that mark bin edges

        # Determine how many bins fit in the dataset for this interval size
        num_intervals = int((ALMActime.max() - ALMActime.min()) / time)

        # Find indices in time array closest to each bin edge
        for n in range(num_intervals):
            difference_array = np.absolute(ALMActime - (time * (n + 1) + ALMActime.min()))
            index = np.argmin(difference_array)  # Closest time point to the bin edge
            index_list.append(index+1)

        # Split flux data into chunks according to index_list
        ALMAflux_arr = np.split(ALMAflux, index_list)

        # Remove trailing empty chunk if it exists
        if len(index_list) < len(ALMAflux_arr):
            del ALMAflux_arr[-1]

        # Compute FSD = std/mean for each chunk
        for chunk in ALMAflux_arr:
            fsd_list.append(np.std(chunk) / np.mean(chunk))

        # Average FSD across all chunks for this bin size
        fsds.append(sum(fsd_list) / len(fsd_list))

    # Plot FSD vs bin size for this dataset
    plt.plot(intervals, fsds, label="ALMA " + dates[iSet])

    # Print global mean flux, global FSD, and telescope label
    print(dates[iSet], np.mean(ALMAflux), np.std(ALMAflux)/np.mean(ALMAflux), "ALMA")


plt.axis([0,3.5,0,.13])
plt.xlabel('Time Intervals (h)')
plt.ylabel('Fractional Standard Deviation (σ/μ)')

plt.legend(loc='upper left',fontsize='xx-small')

plt.show()