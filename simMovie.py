import numpy as np
import h5py
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import argparse
import re

# --------------------------------------------------------------
# Extract parameters from filename
# --------------------------------------------------------------

def extract_parameters(filename):
    """Extract simulation parameters from filename."""
    params = {}
    
    # Extract spin (Ma value)
    ma_match = re.search(r'Ma([-\d.]+)', filename)
    if ma_match:
        params['spin'] = ma_match.group(1)
    
    # Extract inclination (i_ value)
    i_match = re.search(r'i_([-\d.]+)', filename)
    if i_match:
        params['inclination'] = i_match.group(1)
    
    # Extract Rhigh value
    rhigh_match = re.search(r'Rhigh_([-\d.]+)', filename)
    if rhigh_match:
        params['rhigh'] = rhigh_match.group(1)
    
    # Extract frequency if present
    freq_match = re.search(r'(\d+)GHz', filename)
    if freq_match:
        params['frequency'] = freq_match.group(1)
    
    # Extract PA (position angle) if present
    pa_match = re.search(r'PA_([-\d.]+)', filename)
    if pa_match:
        params['pa'] = pa_match.group(1)
    
    return params


# --------------------------------------------------------------
# Readers
# --------------------------------------------------------------

def readGRMHD_IL(file):
    """Reads a snapshot GRMHD image from harm+iPole (HDF5 format)."""
    with h5py.File(file, "r") as f:
        fov = f["header/camera/dx"][()]
        nx = f["header/camera/nx"][()]
        X = np.linspace(-fov / 2., fov / 2., nx)
        ny = nx
        Y = np.linspace(-fov / 2., fov / 2., ny)
        cgsToJy = f["header/scale"][()]
        I = np.copy(f["unpol"]).transpose((1, 0)) * cgsToJy

        if nx != ny:
            raise ValueError("nx != ny")

        Npts = nx
        I = I / np.amax(I)

    return Npts, X, Y, I


def readGRMHD_FRA(file):
    """Reads a snapshot GRMHD image from BHAC (HDF5 format)."""
    with h5py.File(file, "r") as f:
        fov = f["header/camera/dx"][()]
        nx = f["header/camera/nx"][()]
        X = np.linspace(-fov / 2., fov / 2., nx)
        ny = nx
        Y = np.linspace(-fov / 2., fov / 2., ny)
        cgsToJy = f["header/scale"][()]
        I = np.copy(f["unpol"]) * cgsToJy

        if nx != ny:
            raise ValueError("nx != ny")

        Npts = nx
        I = I / np.amax(I)

    return Npts, X, Y, I

# --------------------------------------------------------------
# Load a folder of .h5 files
# --------------------------------------------------------------

def load_h5_folder(folder_path, reader="IL"):
    """Loads all .h5 snapshot files in a directory."""
    h5_files = sorted(
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith(".h5")
    )

    if not h5_files:
        raise FileNotFoundError("No .h5 files found in folder: " + folder_path)

    print(f"Found {len(h5_files)} .h5 snapshot files")

    snapshots = []
    for fpath in h5_files:
        if reader == "IL":
            snapshots.append(readGRMHD_IL(fpath))
        else:
            snapshots.append(readGRMHD_FRA(fpath))

    print(f"Loaded all {len(snapshots)} snapshots")
    return snapshots

# --------------------------------------------------------------
# Make movie from snapshots
# --------------------------------------------------------------

def make_movie_from_snapshots(snapshots, outfile="movie.mp4", fps=10, params=None):
    """Create an mp4 movie from loaded GRMHD snapshots with title screen."""
    print(f"Creating movie with {len(snapshots)} frames...")

    Npts, X, Y, I0 = snapshots[0]

    fig = plt.figure(figsize=(10, 10))
    
    # Create axes with reduced padding (half the default)
    # [left, bottom, width, height] - tighter margins
    ax = fig.add_axes([0.08, 0.08, 0.84, 0.84])  # Reduced from default ~0.125 margins
    
    # Create image plot
    im = ax.imshow(
        I0,
        extent=[X.min(), X.max(), Y.min(), Y.max()],
        origin="lower",
        cmap="inferno",
        animated=True,
    )

    # Configure axes  
    ax.set_xlabel("X [GM/c²]", fontsize=10, color='black')
    ax.set_ylabel("Y [GM/c²]", fontsize=10, color='black')
    
    # Calculate evenly-spaced ticks based on data range
    x_min, x_max = X.min(), X.max()
    y_min, y_max = Y.min(), Y.max()
    
    # Create 5 evenly spaced ticks (fewer ticks = no overlap, cleaner)
    x_ticks = np.linspace(x_min, x_max, 5)
    y_ticks = np.linspace(y_min, y_max, 5)
    
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    
    # Format tick labels to avoid too many decimal places
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}' if abs(x) >= 1 else f'{x:.1f}'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0f}' if abs(y) >= 1 else f'{y:.1f}'))
    
    # Black spines and ticks for visibility on white background
    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1)
    
    # Black tick marks
    ax.tick_params(axis='both', colors='black', direction='out', length=4, width=1, labelsize=9)
    
    # Text objects for title screen - using figure coordinates
    title_text = fig.text(0.5, 0.75, "", 
                         ha='center', va='center', fontsize=24, 
                         weight='bold', color='white',
                         transform=fig.transFigure)
    
    param_text = fig.text(0.5, 0.50, "",
                         ha='center', va='center', fontsize=14, 
                         color='white', family='monospace',
                         transform=fig.transFigure)
    
    credit_text = fig.text(0.95, 0.05, "",
                          ha='right', va='bottom', fontsize=12,
                          color='white', style='italic',
                          transform=fig.transFigure)
    
    frame_title = fig.text(0.5, 0.98, "",
                          ha='center', va='top', fontsize=14,
                          color='white',
                          transform=fig.transFigure)

    # Number of frames for title screen (5 seconds)
    title_frames = int(5 * fps)
    total_frames = title_frames + len(snapshots)

    def update(i):
        if i < title_frames:
            # TITLE SCREEN
            # Hide axes
            ax.set_visible(False)
            
            # Set figure background to black
            fig.patch.set_facecolor('black')
            
            # Show title text
            title_text.set_text("GRMHD SgrA* Simulation")
            title_text.set_visible(True)
            
            # Build and show parameter text
            if params:
                param_lines = []
                if 'frequency' in params:
                    param_lines.append(f"Frequency: {params['frequency']} GHz")
                if 'spin' in params:
                    param_lines.append(f"Spin (a): {params['spin']}")
                if 'inclination' in params:
                    param_lines.append(f"Inclination (i): {params['inclination']}°")
                if 'pa' in params:
                    param_lines.append(f"Position Angle: {params['pa']}°")
                if 'rhigh' in params:
                    param_lines.append(f"R_high: {params['rhigh']}")
                
                param_text.set_text('\n'.join(param_lines))
                param_text.set_visible(True)
            
            # Show credit
            credit_text.set_text("Movie made by David Baker")
            credit_text.set_visible(True)
            
            # Hide frame title
            frame_title.set_visible(False)
            
        else:
            # SIMULATION FRAMES
            # Show axes
            ax.set_visible(True)
            
            # Set figure background to white
            fig.patch.set_facecolor('white')
            
            # Black spines and ticks for white background
            for spine in ax.spines.values():
                spine.set_color('black')
                spine.set_linewidth(1)
            
            ax.tick_params(axis='both', colors='black', direction='out', length=4, width=1)
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            
            # Update image data
            snapshot_idx = i - title_frames
            _, X, Y, I = snapshots[snapshot_idx]
            im.set_array(I)
            im.set_extent([X.min(), X.max(), Y.min(), Y.max()])
            
            # Hide title screen text
            title_text.set_visible(False)
            param_text.set_visible(False)
            credit_text.set_visible(False)
            
            # Show frame counter
            frame_title.set_text(f"GRMHD Frame {snapshot_idx+1}/{len(snapshots)}")
            frame_title.set_color('black')
            frame_title.set_visible(True)
        
        return [im, title_text, param_text, credit_text, frame_title]

    ani = FuncAnimation(fig, update, frames=total_frames, blit=True, interval=1000/fps)

    writer = FFMpegWriter(fps=fps, bitrate=1800)
    ani.save(outfile, writer=writer)

    plt.close(fig)
    print(f"Movie saved successfully: {outfile}")

# --------------------------------------------------------------
# MAIN
# --------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Create an mp4 movie from a folder of GRMHD .h5 snapshots."
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Path to the folder containing .h5 snapshot files"
    )
    parser.add_argument(
        "--reader",
        type=str,
        choices=["IL", "FRA"],
        default="IL",
        help="Type of reader to use (default: IL)"
    )
    parser.add_argument(
        "--outfile",
        type=str,
        default="simulation.mp4",
        help="Output movie filename (default: simulation.mp4)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Frames per second for the movie (default: 10)"
    )
    parser.add_argument(
        "--filename",
        type=str,
        default=None,
        help="Original filename for extracting parameters"
    )

    args = parser.parse_args()

    try:
        # Ensure output directory exists
        outdir = os.path.dirname(args.outfile)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        
        # Extract parameters from filename if provided
        params = None
        if args.filename:
            params = extract_parameters(args.filename)
        
        snapshots = load_h5_folder(args.folder, reader=args.reader)
        make_movie_from_snapshots(
            snapshots,
            outfile=args.outfile,
            fps=args.fps,
            params=params
        )
    except Exception as e:
        print(f"ERROR: {e}")
        import sys
        sys.exit(1)