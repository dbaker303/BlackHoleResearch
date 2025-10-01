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
deltaTau = 0.5

#################################
#  Reading Simulation
#################################

axis_inclinationsall=['10.0','30.0','50.0','70.0']
axis_fieldall=['S','M']
axis_bhallspin=[-0.94,-0.5,0.0,0.5,0.94]
axis_Rratioall=[10,40,160]

inclinationsall=['10.0']
fieldall=['S']
bhallspin=[-0.94]
Rratioall=[160]

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
                
                    
# Set titles and labels
fieldPlot.set_title('Structure Function vs Magnetic Field Type')
fieldPlot.set_xlabel('Magnetic Field Type (S/M)')
fieldPlot.set_ylabel(f'Structure Function at {deltaTau} hr')
fieldPlot.set_xticks([0, 1])  # set x-ticks to field types
fieldPlot.set_xticklabels(['S', 'M'])
fieldPlot.grid(True)

inclPlot.set_title('Structure Function vs Inclination')
inclPlot.set_xlabel('Inclination (degrees)')
inclPlot.set_ylabel(f'Structure Function at {deltaTau} hr')
inclPlot.set_xticks([10, 30, 50, 70])  # set x-ticks to inclination values
inclPlot.grid(True)

bhspinPlot.set_title('Structure Function vs Black Hole Spin')
bhspinPlot.set_xlabel('Black Hole Spin')
bhspinPlot.set_ylabel(f'Structure Function at {deltaTau} hr')
bhspinPlot.set_xticks(axis_bhallspin)  # set x-ticks to BH spin values
bhspinPlot.grid(True)

rratioPlot.set_title('Structure Function vs Rratio')
rratioPlot.set_xlabel('Rratio')
rratioPlot.set_ylabel(f'Structure Function at {deltaTau} hr')
rratioPlot.set_xticks(axis_Rratioall)  # set x-ticks to Rratio values
rratioPlot.grid(True)


# x axis should be the values of the paremters,
# y axis should be the values of the structure function at a given time lag

plt.tight_layout()
plt.show()