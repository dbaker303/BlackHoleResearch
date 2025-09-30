import numpy as np                     # imports library for math
import matplotlib.pyplot as plt        # import library for plots
from scipy import stats                # import binning statistics
from matplotlib import rcParams        # import to change plot parameters
import pandas as pd                    # import pandas for reading data

from EHT_Data.Plots.readarray import readSMA, readALMA
from matplotlib.ticker import FixedLocator, LogLocator, LogFormatterMathtext


###################################
#   EHT scatter+line plot style 
###################################
rcParams['text.usetex']=True

# axes and tickmarks
rcParams['axes.labelsize']=15
rcParams['axes.linewidth']=1.5

rcParams['xtick.labelsize']=8
rcParams['xtick.top']=False
rcParams['xtick.direction']='in'
rcParams['xtick.major.size']=6
rcParams['xtick.minor.size']=3
rcParams['xtick.major.width']=1.2
rcParams['xtick.minor.width']=1.2
rcParams['xtick.minor.visible']=True

rcParams['ytick.labelsize']=8
rcParams['ytick.right']=False
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

# Create two horizontal plots
fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(6, 5),       # slightly taller than wide
    sharey=True,
    sharex = True,
    gridspec_kw={'wspace': 0}  # no space between plots
)

def sliding_structFunc_opt(time, value, error=None, dt0=None, dt_max=None):
    """
    Compute the first-order structure function (SF) using a sliding window,
    following the definition from Simonetti et al. (1985).

    The SF at time lag Δt is defined as
        D(Δt) = (1 / M_Δt) * Σ_{i,j} (x_j - x_i)^2
    where the sum is over all pairs (i, j) with 
        Δt - Δt0/2 <= |t_j - t_i| <= Δt + Δt0/2,
    and M_Δt is the number of such pairs. The SF measures the variance of the
    signal on timescale Δt. Optionally, an error estimate can be computed.

    Parameters
    ----------
    time : array-like
        Times of the measurements.
    value : array-like
        Measured values at those times. Values are internally normalized by their mean.
    error : array-like or None, optional
        Measurement errors. Used to estimate uncertainty in sqrt(D(Δt)).
    dt0 : float, optional
        Width of the sliding window (Δt0). If None, defaults to the minimum time difference.
    dt_max : float, optional
        Maximum Δt at which to evaluate the SF. If None, defaults to max(time) - min(time).

    Returns
    -------
    target_dts : array
        Time lags Δt at which the SF is evaluated.
    sqrtD1 : array
        Square root of the structure function √D(Δt) at each Δt.
    sigmaD1 : array or None
        Uncertainty of sqrtD1 due to measurement error, if `error` is provided.
    """

    time = np.array(time)
    value = value / np.mean(value)   # normalize flux
    N = len(time)

    if dt0 is None:
        dt0 = np.min(np.diff(np.sort(time)))

    if dt_max is None:
        dt_max = np.max(time) - np.min(time)

    target_dts = np.arange(0, dt_max + dt0, dt0)
    sqrtD1 = np.zeros(len(target_dts))
    sigmaD1 = np.zeros(len(target_dts)) if error is not None else None

    # Normalize error if provided
    if error is not None:
        error = np.array(error) / np.mean(value)
        ave_error = np.mean(error)

    # Loop over target Δt values
    for idx, dt in enumerate(target_dts):
        diffs = []

        # Loop over all pairs (i < j)
        for i in range(N):
            for j in range(i + 1, N):
                tau = np.abs(time[j] - time[i])
                if dt - dt0/2 <= tau <= dt + dt0/2:
                    diffs.append((value[j] - value[i])**2)

        if diffs:
            D1 = np.mean(diffs)
            sqrtD1[idx] = np.sqrt(D1)
            if error is not None:
                sigmaD = np.sqrt(8 * ave_error**2 * D1 / len(diffs))
                sigmaD1[idx] = sigmaD / (2 * np.sqrt(D1))
        else:
            sqrtD1[idx] = np.nan
            if error is not None:
                sigmaD1[idx] = np.nan

    return target_dts, sqrtD1, sigmaD1



def structFunction(time, value):
    pass
    

##########################################
        ## SIMULATION DATA ##
##########################################
"""
inclinationsall=['10.0','30.0','50.0','70.0']
fieldall=['S','M']
bhallspin=[-0.94,-0.5,0.0,0.5,0.94]
bhallspin=[-0.94,-0.5,0.0]
Rratioall=[10,40,160]

for field in fieldall:
    structall=np.array([])
    
    for incl in inclinationsall:
        for bhspin in bhallspin:
            for Rratio in Rratioall:

                # make a filename based on the input parameters
                if (field=='S'):
                    filename="Simulations/SANE/"+field+"a"+str(bhspin)+".i"+incl+".R"+str(Rratio)+"_var.out"
                elif (field=='M'):
                    filename="Simulations/MAD/"+field+"a"+str(bhspin)+".i"+incl+".R"+str(Rratio)+"_var.out"
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
                
                # make a set of equdistant bins between 0 and 8 hours
                tlag, sqrtD1, sigmad1 = sliding_structFunc_opt(ctime, flux, error=None, dt0=None, dt_max=None)
                print(field,incl,bhspin,Rratio)

                
                ax1.plot(tlag, sqrtD1, linestyle='-', alpha=0.2)
                
"""
##########################################
        ## EHT DATA ##
##########################################

dataset=['Apr05','Apr06','Apr07','Apr10']
dates=['April 5','April 6','April 7','April 10']

for iSet in [0,1,2,3]:
    #read the SMA file data
    SMAfname='EHT_Data/SMA/SM_STAND_HI_'+dataset[iSet]+'.dat'
    SMActime,SMAflux,SMAflux_err=readSMA(SMAfname)
    
    #represent the time as a span of multiple days of data
    if (iSet<3):
        SMActime+=iSet*24
    else:
        SMActime+=(iSet+2)*24
            
    SMAtlag, SMAsqrtD1, SMAerrorD1 = sliding_structFunc_opt(SMActime, SMAflux, SMAflux_err)
    ax2.plot(SMAtlag, SMAsqrtD1, linestyle='-', label=f"{SMAfname}")

    print("SMA" + dates[iSet])

"""for iSet in [1,2]:
    #read the ALMA file data
    ALMAfname='EHT_Data/ALMA/AA_STAND_HI_'+dataset[iSet]+'.dat'
    ALMActime,ALMAflux,ALMAflux_err=readALMA(ALMAfname)
    
    #represent the time as a span of multiple days of data
    if (iSet<3):
        ALMActime+=iSet*24
    else:
        ALMActime+=(iSet+2)*24
        
    
    ALMAtlag, ALMAsqrtD1, ALMAerrorD1 = sliding_structFunc_opt(ALMActime, ALMAflux, ALMAflux_err)
    ax2.plot(ALMAtlag, ALMAsqrtD1, linestyle='-', label=f"{ALMAfname}")

    print("ALMA" + dates[iSet])"""
    
##########################################
        ## PLOT CHARACERISTICS ##
##########################################

             
# Top subplot: simulation data
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_ylabel(r'Log $[D^1(\tau)]^{1/2}$')
ax1.set_title("Simulation Data")
ax1.grid(True, which='major', ls='--', alpha=0.3)

# Bottom subplot: second dataset
ax2.set_xscale('log')
ax2.set_yscale('log')
ax2.set_title("EHT Data")
ax2.grid(True, which='major', ls='--', alpha=0.3)
ax2.legend(
    frameon=False,      # no box around legend
    loc='upper left',  # position inside the plot
    fontsize=6.5,         # smaller font so it fits
    ncol=1,             # number of columns in legend
    handlelength=2,     # length of line samples
    labelspacing=0.15,   # vertical spacing between labels
    borderaxespad=0.5   # padding between legend and axes
)

fig.supxlabel(r'Log $\Delta \tau$ (hours)', fontsize=14)

"""for ax in [ax1, ax2]:
    ax.set_xlim([0.005, 5])
    ax.set_ylim([0.00008, 1])"""

plt.tight_layout()
plt.show()


                
                
                
                
                
                
                


