import numpy as np                     # imports library for math
import matplotlib.pyplot as plt        # import library for plots
from matplotlib import rcParams        # import to change plot parameters
import mplcursors
import random


###############################
#   Plot parameters
###############################

# Create a 2x2 grid of subplots
fig, axes = plt.subplots(2, 2, figsize=(9, 6.5))
# axes is a 2x2 NumPy array, so unpack it
fieldPlot, inclPlot = axes[0]  # first row
bhspinPlot, rratioPlot = axes[1]  # second row

# time lag size in hours to compute structure function and compare results
deltaTau = 0.5 # hours

#################################
#  Reading Simulation
#################################

sim_data = []

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
                
                """fieldPlot.plot(field, D1_at_deltaTau, 'o', label=f'Field: {field}')
                inclPlot.plot(float(incl), D1_at_deltaTau, 'o', label=f'Incl: {incl}')
                bhspinPlot.plot(bhspin, D1_at_deltaTau, 'o', label=f'Spin: {bhspin}')
                rratioPlot.plot(Rratio, D1_at_deltaTau, 'o', label=f'Rratio: {Rratio}')"""
                
                sim_data.append({
                    "field": field,
                    "incl": float(incl),
                    "bhspin": bhspin,
                    "Rratio": Rratio,
                    "D1": D1_at_deltaTau,
                    "type": 'n'  # default type
                })
                
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

##################################
#  Connecting lines between points
##################################

POIs = [
    {'incl':10.0, 'bhspin':-0.5, 'Rratio':160, 'field':'S'},
    {'incl':30.0, 'bhspin':-0.5, 'Rratio':160, 'field':'S'},
    {'incl':10.0, 'bhspin':-0.5, 'Rratio':40, 'field':'S'}
]

for poi in POIs:
    for d in sim_data:
        if all(d[k] == poi[k] for k in poi):
            d['type'] = 'o'

def plot_points_with_outliers(ax, x_key, group_keys, max_normal_lines=10):
    scatter_x, scatter_y = [], []

    # Collect all groups
    groups = {}
    for d in sim_data:
        key = tuple(d[k] for k in group_keys)
        groups.setdefault(key, []).append(d)

    normal_groups = []
    outlier_groups = []

    for group in groups.values():
        if any(d['type']=='o' for d in group):
            outlier_groups.append(group)
        else:
            normal_groups.append(group)

    # Randomly keep a few normal lines
    if len(normal_groups) > max_normal_lines:
        normal_groups = random.sample(normal_groups, max_normal_lines)

    # Combine with outlier groups
    plot_groups = outlier_groups + normal_groups

    # Plot lines and gather scatter points
    for group in plot_groups:
        x_vals = [d[x_key] for d in group]
        y_vals = [d['D1'] for d in group]

        # Red if any outlier, else black
        line_color = 'red' if any(d['type']=='o' for d in group) else 'black'
        ax.plot(x_vals, y_vals, '-', color=line_color, alpha=0.8, linewidth=1.5, zorder=1)

        scatter_x.extend(x_vals)
        scatter_y.extend(y_vals)

    # Scatter all points
    sc = ax.scatter([d[x_key] for d in sim_data], [d['D1'] for d in sim_data], zorder=2)
    return sc

sc_field  = plot_points_with_outliers(fieldPlot, 'field', ['incl','bhspin','Rratio'])
sc_incl   = plot_points_with_outliers(inclPlot, 'incl', ['field','bhspin','Rratio'])
sc_spin   = plot_points_with_outliers(bhspinPlot, 'bhspin', ['field','incl','Rratio'])
sc_rratio = plot_points_with_outliers(rratioPlot, 'Rratio', ['field','incl','bhspin'])


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

def make_hover(scatter):
    cursor = mplcursors.cursor(scatter, hover=True)
    @cursor.connect("add")
    def on_hover(sel):
        d = sim_data[sel.index]
        sel.annotation.set_text(
            f"Field: {d['field']}\nIncl: {d['incl']}\nSpin: {d['bhspin']}\nRratio: {d['Rratio']}\nD1: {d['D1']:.4f}"
        )

for sc in [sc_field, sc_incl, sc_spin, sc_rratio]:
    make_hover(sc)

plt.tight_layout()
plt.show()