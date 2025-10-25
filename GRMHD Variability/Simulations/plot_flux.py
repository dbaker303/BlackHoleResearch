import numpy as np                     # imports library for math
import matplotlib.pyplot as plt        # import library for plots
from scipy import stats                # import binning statistics
from matplotlib import rcParams        # import to change plot parameters

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

# list of black-hall inclinations
#possible values ['10.0','30.0','50.0','70.0']
inclinationsall=['10.0']

# list of magnetic field configurations
#possible values ['S','M']
fieldall=['S', 'M']

# list of black-hole spins 
#possible values [-0.94,-0.5,0.0,0.5,0.94]
bhallspin=[-0.5]

# list of temperature ratios
#possible values [10,40,160]
Rratioall=[10, 160]

# go through all lists of parameters
for field in fieldall:
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
                
                # first column is time in 5GM/c^3, which is 0.05883 hrs for Sgr A* (@4.3 10^6 Msun)
                ctime=(alldata[:,0]-alldata[0,0])*0.05883
                # next column is flux
                flux=alldata[:,1]

                # print overall standard deviation and mean flux
                print(filename," std:",np.std(flux)," mean:",np.mean(flux))
                
                plt.plot(ctime,flux,lw=1,label=filename[:-8])
                
plt.xlabel(r"Time (hr)")
plt.ylabel(r"Flux (Jy)")

plt.axis([0.0,300,0,5])

plt.legend(frameon=False,fontsize='xx-small')

plt.tight_layout()
plt.show()
