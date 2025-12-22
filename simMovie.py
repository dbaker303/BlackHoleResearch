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

    print(f"\n📁 Found {len(h5_files)} .h5 snapshot files.\n")

    snapshots = []
    for fpath in h5_files:
        if reader == "IL":
            snapshots.append(readGRMHD_IL(fpath))
        else:
            snapshots.append(readGRMHD_FRA(fpath))
        print(f"✅ Loaded: {os.path.basename(fpath)}")

    return snapshots

# --------------------------------------------------------------
# Make movie from snapshots
# --------------------------------------------------------------

def make_movie_from_snapshots(snapshots, outfile="movie.mp4", fps=10, params=None):
    """Create an mp4 movie from loaded GRMHD snapshots with title screen."""
    print(f"\n🎬 Creating movie: {outfile}\n")

    Npts, X, Y, I0 = snapshots[0]

    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Initial blank frame for title screen
    im = ax.imshow(
        np.zeros_like(I0),
        extent=[X.min(), X.max(), Y.min(), Y.max()],
        origin="lower",
        cmap="inferno",
        animated=True,
    )

    ax.set_xlabel("X [GM/c²]", fontsize=12)
    ax.set_ylabel("Y [GM/c²]", fontsize=12)
    
    # Text objects for title screen with absolute positioning
    # Title at 75% of figure height (25% from top)
    title_text = ax.text(0.5, 0.75, "", transform=fig.transFigure, 
                        ha='center', va='center', fontsize=24, 
                        weight='bold', color='white')
    
    # Parameters at 50% of figure height (middle of remaining space) 
    param_text = ax.text(0.5, 0.50, "", transform=fig.transFigure,
                        ha='center', va='center', fontsize=14, 
                        color='white', family='monospace')
    
    credit_text = ax.text(0.95, 0.05, "", transform=fig.transFigure,
                         ha='right', va='bottom', fontsize=12,
                         color='white', style='italic')
    
    frame_title = ax.text(0.5, 0.98, "", transform=fig.transFigure,
                         ha='center', va='top', fontsize=14,
                         color='white')

    # Number of frames for title screen (5 seconds)
    title_frames = int(5 * fps)
    total_frames = title_frames + len(snapshots)

    def update(i):
        if i < title_frames:
            # Title screen
            im.set_array(np.zeros_like(I0))
            title_text.set_text("GRMHD SgrA* Simulation")
            
            # Build parameter text
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
            else:
                param_text.set_text("")
            
            credit_text.set_text("Movie made by David Baker")
            frame_title.set_text("")
            ax.set_facecolor('black')
            
        else:
            # Simulation frames
            snapshot_idx = i - title_frames
            _, X, Y, I = snapshots[snapshot_idx]
            im.set_array(I)
            title_text.set_text("")
            param_text.set_text("")
            credit_text.set_text("")
            frame_title.set_text(f"GRMHD Frame {snapshot_idx+1}/{len(snapshots)}")
            ax.set_facecolor('white')
        
        return [im, title_text, param_text, credit_text, frame_title]

    ani = FuncAnimation(fig, update, frames=total_frames, blit=True)

    writer = FFMpegWriter(fps=fps)
    ani.save(outfile, writer=writer)

    plt.close(fig)  # Clean up the figure
    print(f"\n✅ Movie saved to {outfile}\n")

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
            print(f"\n📊 Extracted parameters: {params}\n")
        
        snapshots = load_h5_folder(args.folder, reader=args.reader)
        make_movie_from_snapshots(
            snapshots,
            outfile=args.outfile,
            fps=args.fps,
            params=params
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import sys
        sys.exit(1)