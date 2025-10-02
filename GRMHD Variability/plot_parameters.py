import numpy as np                     # imports library for math
import matplotlib.pyplot as plt        # import library for plots
from matplotlib import rcParams        # import to change plot parameters
import pandas as pd                    # import pandas for reading data

#from plotsf import sliding_structFunc_opt # import the structure function code
from EHT_Data.Plots.readarray import readSMA, readALMA # import readarray code


###############################
#   Plot parameters
###############################

# Create a 2x2 grid of subplots
fig, axes = plt.subplots(2, 2, figsize=(9, 6.5))
# axes is a 2x2 NumPy array, so unpack it
fieldPlot, inclPlot = axes[0]  # first row
bhspinPlot, rratioPlot = axes[1]  # second row

# time lag size in hours to compute structure function and compare results
deltaTau = 0.3 # hours

#################################
#  Reading Simulation
#################################


inclinationsall=['10.0','30.0','50.0','70.0'] #corresponds to shapes circle, square, diamond, triangle
fieldall=['S','M'] # size of marker
bhallspin=[-0.94,-0.5,0.0,0.5,0.94] # sets border color to different colors
Rratioall=[10,40,160] # sets fillstyle to unfilled, half-filled, or filled


for field in fieldall:
    for incl in inclinationsall:
        for bhspin in bhallspin:
            for Rratio in Rratioall:

                if (field=='S'):
                    infile="Simulations/SANEnpz/"+field+"a"+str(bhspin)+".i"+incl+".R"+str(Rratio)+"_sf.npz"
                elif (field=='M'):
                    infile="Simulations/MADnpz/"+field+"a"+str(bhspin)+".i"+incl+".R"+str(Rratio)+"_sf.npz"
                    
                data = np.load(infile)
                tlag = data["tlag"]
                D1 = data["D1"]
                
                idx = np.argmin(np.abs(tlag - deltaTau)) # find index of closest time lag to deltaTau
                D1_at_deltaTau = D1[idx] # get the structure function value at that index
                
                fieldPlot.plot(field, D1_at_deltaTau, 'o', label=f'Field: {field}')
                inclPlot.plot(float(incl), D1_at_deltaTau, 'o', label=f'Incl: {incl}')
                bhspinPlot.plot(bhspin, D1_at_deltaTau, 'o', label=f'Spin: {bhspin}')
                rratioPlot.plot(Rratio, D1_at_deltaTau, 'o', label=f'Rratio: {Rratio}')
                
                #Need to Work on customizing markers based on parameters
                """#customize marker based on parameters
                marker = 'o' if incl == '10.0' else 's' if incl == '30.0' else 'D' if incl == '50.0' else '^'
                color = 'red' if bhspin == -0.94 else 'orange' if bhspin == -0.5 else 'green' if bhspin == 0.0 else 'blue' if bhspin == 0.5 else 'purple'
                fillstyle = 'none' if Rratio == 10 else 'bottom' if Rratio == 40 else 'full'
                size = 1 if field == 'S' else 2

                # plot on respective subplot
                fieldPlot.plot(field, D1_at_deltaTau, marker=marker, markersize=size, color=color, fillstyle=fillstyle, label=f'Field: {field}')
                inclPlot.plot(float(incl), D1_at_deltaTau, marker=marker, markersize=size, color=color, fillstyle=fillstyle, label=f'Incl: {incl}')
                bhspinPlot.plot(bhspin, D1_at_deltaTau, marker=marker, markersize=size, color=color, fillstyle=fillstyle, label=f'Spin: {bhspin}')
                rratioPlot.plot(Rratio, D1_at_deltaTau, marker=marker, markersize=size, color=color, fillstyle=fillstyle, label=f'Rratio: {Rratio}')"""
                
                
#################################
#  Reading EHT Data
################################# 

dataset=['Apr05','Apr06','Apr07','Apr10']
dates=['April 5','April 6','April 7','April 10']

D1_list = []

for iSet in [0,1,2,3]:
    data = np.load(f"EHT_Data/SMAnpz/SMA_{dataset[iSet]}_sf.npz")
    tlag = data["tlag"]
    D1 = data["D1"]
    idx = np.argmin(np.abs(tlag - deltaTau)) # find index of closest time lag to deltaTau
    D1_at_deltaTau = D1[idx] # get the structure function value at that index
    D1_list.append(D1_at_deltaTau)
    
for iSet in [1,2]:
    data = np.load(f"EHT_Data/ALMAnpz/ALMA_{dataset[iSet]}_sf.npz")
    tlag = data["tlag"]
    D1 = data["D1"]
    idx = np.argmin(np.abs(tlag - deltaTau)) # find index of closest time lag to deltaTau
    D1_at_deltaTau = D1[idx] # get the structure function value at that index
    D1_list.append(D1_at_deltaTau)
    
EHT_D1_list = np.array(D1_list)
    

#################################
#  Final Plot Adjustments
#################################

for ax in [fieldPlot, inclPlot, bhspinPlot, rratioPlot]:
    ax.set_ylim([0.0008, 1])
    ax.set_ylabel(fr'Log $[D^1(\tau)]$ @ $\tau$={deltaTau} hr')
    ax.set_yscale('log')  # set y-axis to logarithmic scale
    ax.axhspan(
    ymin=EHT_D1_list.min(),
    ymax=EHT_D1_list.max(),
    color='red',
    alpha=0.3
)

fieldPlot.set_title('Structure Function vs Magnetic Field Type')
fieldPlot.set_xlabel('Magnetic Field Type (S/M)')

inclPlot.set_title('Structure Function vs Inclination')
inclPlot.set_xlabel('Inclination (degrees)')
inclPlot.set_xticks([10.0, 30.0, 50.0, 70.0])  # set x-ticks to inclination values

bhspinPlot.set_title('Structure Function vs Black Hole Spin')
bhspinPlot.set_xlabel('Black Hole Spin')
bhspinPlot.set_xticks([-0.94,-0.5,0.0,0.5,0.94])  # set x-ticks to BH spin values

rratioPlot.set_title('Structure Function vs Rratio')
rratioPlot.set_xlabel('Rratio')
rratioPlot.set_xticks([10,40,160])  # set x-ticks to Rratio values


plt.tight_layout()
plt.show()