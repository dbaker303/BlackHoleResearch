import numpy as np
import h5py
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import argparse

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

def make_movie_from_snapshots(snapshots, outfile="movie.mp4", fps=10):
    """Create an mp4 movie from loaded GRMHD snapshots."""
    print(f"\n🎬 Creating movie: {outfile}\n")

    Npts, X, Y, I0 = snapshots[0]

    fig, ax = plt.subplots()
    im = ax.imshow(
        I0,
        extent=[X.min(), X.max(), Y.min(), Y.max()],
        origin="lower",
        cmap="inferno",
        animated=True,
    )

    ax.set_xlabel("X [GM/c²]")
    ax.set_ylabel("Y [GM/c²]")

    def update(i):
        _, X, Y, I = snapshots[i]
        im.set_array(I)
        ax.set_title(f"GRMHD Frame {i+1}/{len(snapshots)}")
        return [im]

    ani = FuncAnimation(fig, update, frames=len(snapshots), blit=True)

    writer = FFMpegWriter(fps=fps)
    ani.save(outfile, writer=writer)

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

    args = parser.parse_args()

    try:
        snapshots = load_h5_folder(args.folder, reader=args.reader)
        make_movie_from_snapshots(
            snapshots,
            outfile=args.outfile,
            fps=args.fps
        )
    except Exception as e:
        print("Error:", e)
