import numpy as np                     # imports library for math
import matplotlib.pyplot as plt        # import library for plots
from scipy import stats                # import binning statistics
from matplotlib import rcParams        # import to change plot parameters
import pandas as pd                    # import pandas for reading data
from scipy import signal

###################################
#   EHT scatter+line plot style 
###################################
figsize=(7.5,5.5) #size of the figure for general figures

rcParams['text.usetex']=True
#rcParams['font.family']='sans-serif'
#rcParams['font.sans-serif']='Latin Modern Roman'

# axes and tickmarks
rcParams['axes.labelsize']=15
#rcParams['axes.labelweight']=600
rcParams['axes.linewidth']=1.5

rcParams['xtick.labelsize']=14
rcParams['xtick.top']=True
rcParams['xtick.direction']='in'
rcParams['xtick.major.size']=6
rcParams['xtick.minor.size']=3
rcParams['xtick.major.width']=1.2
rcParams['xtick.minor.width']=1.2
rcParams['xtick.minor.visible']=True

rcParams['ytick.labelsize']=14
rcParams['ytick.right']=True
rcParams['ytick.direction']='in'
rcParams['ytick.major.size']=6
rcParams['ytick.minor.size']=3
rcParams['ytick.major.width']=1.2
rcParams['ytick.minor.width']=1.2
rcParams['ytick.minor.visible']=True

# points and lines
rcParams['lines.linewidth']=2.0
rcParams['lines.markeredgewidth']=0.5
rcParams['lines.markersize']=6

plt.figure(figsize=figsize)            # size of the figure


# numner of timelag bins
NumberofBins=64

# calculate the structure function of a time series.
# the times of the equidistant points is in array *time*
# the values is in array *value*
# the errors in the measurements are in *error*
# if NBINS is an integer, it calculates the structure function
#     at NBINS equdistant timelag bins
# if it is an array, it uses it for the edges of the bins
# it returns the bin centers, the square root of the 1st order
# structure function, and the error in it
def structFunc(time,value,error,nbins):
    Npoints=np.size(time)

    error=error/np.mean(value)
    value=value/np.mean(value)
    aveerror=np.mean(error)
    sigma=np.std(value)

    tau=np.array([])
    diff2=np.array([])
    for ipt in np.arange(Npoints):
          for jpt in np.arange(ipt):
            tauij=time[ipt]-time[jpt]
            tau=np.append(tau,tauij)
            diff2ij=(value[ipt]-value[jpt])*(value[ipt]-value[jpt])
            diff2=np.append(diff2,diff2ij)

    taumax=np.amax(tau)

    bin_means,bin_edges,binnumber=stats.binned_statistic(tau,diff2,statistic='mean',bins=nbins)
    bin_width = (bin_edges[1] - bin_edges[0])
    bin_centers = bin_edges[1:] - bin_width/2

    numberPerBin=np.zeros(NumberofBins)
    for index in np.arange(NumberofBins):
        numberPerBin[index]=np.size(binnumber[binnumber==index])

    D1=bin_means
    sigmaD=np.sqrt(8.*aveerror*aveerror*D1/(numberPerBin+1))
    sigmaSQRTD=sigmaD/2./np.sqrt(D1)

    # nan means no data found
    condition=~np.isnan(D1)
    return bin_centers[condition],np.sqrt(D1[condition]),sigmaSQRTD[condition]


# create the root for the filenames

inclinationsall=['10.0','30.0','50.0','70.0']
fieldall=['S','M']
bhallspin=[-0.94,-0.5,0.0,0.5,0.94]
Rratioall=[10,40,160]

for field in fieldall:
    structall=np.array([])

    
    for incl in inclinationsall:
        for bhspin in bhallspin:
            for Rratio in Rratioall:

                # make a filename based on the input parameters
                if (field=='S'):
                    filename="SANE/"+field+"a"+str(bhspin)+".i"+incl+".R"+str(Rratio)+"_var.out"
                elif (field=='M'):
                    filename="MAD/"+field+"a"+str(bhspin)+".i"+incl+".R"+str(Rratio)+"_var.out"
                # read all the data
                alldata=np.genfromtxt(filename)
                
                # first column is time in 5M, which is 0.00588 hrs for Sgr A* (@4.3 10^6 Msun)
                ctime=(alldata[:,0]-alldata[0,0])*0.02942
                # next column is flux
                flux=alldata[:,1]
                # makeup an error for later
                err=np.ones(np.size(flux))*0.001
                
                # thining
                thin=5
                ctime=ctime[::thin]
                flux=flux[::thin]
                err=err[::thin]
                
                # create a Butterworth filter of order 3 with a timescale of 2hours
                # (or cutoff frequency of 1/2/2)
                sos = signal.butter(3, 1./4., 'highpass', fs=1./0.02942, output='sos')
                
                # add the DC level of the flux to the filtered lightcurve
                meanfluxlevel=2.0
                filtered = signal.sosfilt(sos, flux)+meanfluxlevel
                
                # for the first *tinin* hours use the original data, to avoid boundary effects
                tinit=2.0
                # find the normalization of the initial data to avoid jumps at the stitching point
                filterrenorm=flux[ctime>tinit]/filtered[ctime>tinit]
                allfiltered=np.append(flux[ctime<=tinit]/filterrenorm[0],filtered[ctime>tinit])
                
                # plot the detrended data
                #plt.plot(ctime,allfiltered,label=filename[:-8])
                
                # make a set of equdistant bins between 0 and 8 hours
                nbins=np.linspace(0,8.,NumberofBins+1)
                
                # total duration
                duration=ctime[-1]
                
                # stop the individual values
                struct1hr=np.array([])
                
                # split this in 10h chunks, separated by half hour
                for starttime in np.arange(0.,duration-10.,0.25):
                    #print(starttime)
                    conditionC=(ctime>=starttime) & (ctime<starttime+10)
                    
                    tlag,sqrtD1,errorD1=structFunc(ctime[conditionC],flux[conditionC],err[conditionC],nbins)
                    
                    #save the structure function at 1hr
                    conditionp=((tlag>0.94) & (tlag<1.1))
                    structC=sqrtD1[conditionp]
                    struct1hr=np.append(struct1hr,structC)

                print(field,incl,bhspin,Rratio,np.size(struct1hr[struct1hr<0.10])/np.size(struct1hr))

                structall=np.append(structall,struct1hr)

            
    plt.hist(structall,25,lw=2,histtype='step',density=True,label='Illinois '+field)     

plt.ylabel(r"Count")
plt.xlabel(r"Structure Function $[D^1(\tau)]^{1/2}$ (1hr)")

plt.axis([0.0,0.6,0.,10.])

plt.fill_betweenx([0,10],[0.05,0.05],[0.1,0.1],color='green',alpha=0.2)

plt.legend(frameon=False)

plt.tight_layout()
plt.show()
