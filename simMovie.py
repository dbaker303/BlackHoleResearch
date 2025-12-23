#!/usr/bin/env python3
import os
import re
import argparse
import subprocess

import numpy as np
import h5py

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter


FONTFILE_DEFAULT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


# ----------------------------
# Filename parameter parsing
# ----------------------------
def extract_parameters(name: str) -> dict:
    params = {}

    m = re.search(r"(\d+)\s*GHz", name, flags=re.IGNORECASE)
    if m:
        params["frequency"] = m.group(1)

    m = re.search(r"(?:^|_)Ma([+\-]?\d*\.?\d+)(?:_|$)", name)
    if m:
        params["spin"] = m.group(1)

    m = re.search(r"(?:^|_)i_(\d+)(?:_|$)", name, flags=re.IGNORECASE)
    if m:
        params["inclination"] = m.group(1)

    m = re.search(r"(?:^|_)Rhigh_(\d+)(?:_|$)", name, flags=re.IGNORECASE)
    if m:
        params["rhigh"] = m.group(1)

    # Intentionally NOT parsing PA (you said you don't want it shown)
    return params


def build_param_lines(params: dict) -> list[str]:
    lines = []
    if not params:
        return lines

    if "frequency" in params:
        lines.append(f"Frequency: {params['frequency']} GHz")
    if "spin" in params:
        lines.append(f"Spin (a): {params['spin']}")
    if "inclination" in params:
        lines.append(f"Inclination (i): {params['inclination']}°")
    if "rhigh" in params:
        lines.append(f"R_high: {params['rhigh']}")
    return lines


# ----------------------------
# HDF5 frame discovery
# ----------------------------
def list_h5_files(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")

    h5s = sorted(
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith(".h5")
    )
    if not h5s:
        raise FileNotFoundError(f"No .h5 files found in: {folder}")
    return h5s


# ----------------------------
# Your professor’s guidance:
# Use header/camera/dx and header/camera/nx to set GM/c^2 axes
# ----------------------------
def read_grmhd_with_units(file: str):
    """
    Try to read harm+iPole/BHAC-style image using known keys:
      header/camera/dx, header/camera/nx, header/scale, unpol

    Returns:
      Npts, X, Y, I   where X,Y are GM/c^2 coordinates and I is normalized brightness
    """
    with h5py.File(file, "r") as f:
        # Required keys for physical axes
        dx_path = "header/camera/dx"
        nx_path = "header/camera/nx"
        scale_path = "header/scale"
        unpol_path = "unpol"

        if dx_path not in f or nx_path not in f or unpol_path not in f:
            return None  # signal: can't do physical axes

        fov = f[dx_path][()]     # per professor docstring: GM/c^2
        nx  = int(f[nx_path][()])

        X = np.linspace(-fov/2.0, fov/2.0, nx)
        Y = np.linspace(-fov/2.0, fov/2.0, nx)

        cgsToJy = f[scale_path][()] if scale_path in f else 1.0

        I = np.array(f[unpol_path]) * cgsToJy

        # Some files may need transpose (IL vs FRA)
        # If it looks swapped, fix by checking shape against nx
        if I.ndim == 2 and I.shape[0] == nx and I.shape[1] == nx:
            pass
        elif I.ndim == 2 and I.shape[0] == nx and I.shape[1] == nx:
            pass
        elif I.ndim == 2 and I.shape[::-1] == (nx, nx):
            I = I.T

        if I.ndim != 2:
            return None

        if nx != I.shape[0] or nx != I.shape[1]:
            # Still not square in expected way
            return None

        # Normalize to unit peak brightness
        mx = np.nanmax(I)
        if mx > 0:
            I = I / mx

        return nx, X, Y, I


# ----------------------------
# Auto-detect fallback (if units keys missing)
# ----------------------------
def _is_numeric_dataset(ds: h5py.Dataset) -> bool:
    return ds.dtype.kind in ("i", "u", "f")


def _as_2d_image(arr: np.ndarray) -> np.ndarray | None:
    if arr.ndim == 2:
        return arr
    if arr.ndim == 3:
        if arr.shape[0] == 1:
            return arr[0, :, :]
        if arr.shape[2] == 1:
            return arr[:, :, 0]
        if arr.shape[2] in (3, 4):
            return arr[:, :, 0]
    return None


def detect_image_dataset_path(h5_file: str) -> str:
    prefer_keywords = ("unpol", "ftot", "image", "img", "nulnu", "intensity")
    candidates = []

    with h5py.File(h5_file, "r") as f:
        def visitor(name, obj):
            if not isinstance(obj, h5py.Dataset):
                return
            ds = obj
            if not _is_numeric_dataset(ds) or ds.ndim < 2:
                return

            shape = ds.shape
            score = 0.0

            if ds.ndim == 2:
                score += 120.0
            elif ds.ndim == 3:
                if shape[0] == 1 or shape[2] == 1 or (shape[2] in (3, 4)):
                    score += 90.0
                else:
                    return

            h = shape[-2]
            w = shape[-1]
            score += 30.0 if h == w else 8.0
            score += min((h * w) / 1e5, 60.0)

            lname = name.lower()
            for kw in prefer_keywords:
                if kw in lname:
                    score += 15.0

            candidates.append((score, name, shape, ds.dtype))

        f.visititems(visitor)

    if not candidates:
        raise RuntimeError(f"Could not auto-detect a 2D image dataset in: {h5_file}")

    candidates.sort(key=lambda x: x[0], reverse=True)

    print("Auto-detect dataset candidates (top 10):")
    for s, n, sh, dt in candidates[:10]:
        print(f"  score={s:7.2f}  path={n:45s}  shape={sh}  dtype={dt}")

    best = candidates[0]
    print(f"Selected dataset path: {best[1]} (shape={best[2]})")
    return best[1]


def read_image_from_h5(h5_file: str, dataset_path: str) -> np.ndarray:
    with h5py.File(h5_file, "r") as f:
        arr = np.array(f[dataset_path])
    img = _as_2d_image(arr)
    if img is None:
        raise RuntimeError(f"Dataset '{dataset_path}' not convertible to 2D. Shape={arr.shape}")
    mx = np.nanmax(img)
    if mx > 0:
        img = img / mx
    return img


# ----------------------------
# ffmpeg helpers
# ----------------------------
def ffprobe_wh(video_path: str) -> tuple[int, int]:
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", video_path],
            capture_output=True, text=True, check=True
        )
        wh = p.stdout.strip()
        if "x" in wh:
            w, h = wh.split("x")
            return int(w), int(h)
    except Exception:
        pass
    return 1000, 1000


def _ff_escape_text(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    return s


def make_title_clip_ffmpeg(title_mp4: str, w: int, h: int, fps: int, duration_s: int,
                           title_line: str, param_lines: list[str],
                           credit_line: str, fontfile: str):
    if not os.path.exists(fontfile):
        raise FileNotFoundError(f"Font file not found: {fontfile}")

    top_y = 0.28
    params_start = 0.42
    params_end = 0.60
    title_fs = 54
    param_fs = 30
    credit_fs = 24
    margin = 50

    filters = []

    filters.append(
        f"drawtext=fontfile={fontfile}:text='{_ff_escape_text(title_line)}':"
        f"fontcolor=white:fontsize={title_fs}:x=(w-text_w)/2:y=h*{top_y}"
    )

    if param_lines:
        n = len(param_lines)
        if n == 1:
            y_fracs = [params_start]
        else:
            step = (params_end - params_start) / (n - 1)
            y_fracs = [params_start + step * i for i in range(n)]

        for line, y_frac in zip(param_lines, y_fracs):
            filters.append(
                f"drawtext=fontfile={fontfile}:text='{_ff_escape_text(line)}':"
                f"fontcolor=white:fontsize={param_fs}:x=(w-text_w)/2:y=h*{y_frac}"
            )

    filters.append(
        f"drawtext=fontfile={fontfile}:text='{_ff_escape_text(credit_line)}':"
        f"fontcolor=white:fontsize={credit_fs}:x=w-text_w-{margin}:y=h-{margin}"
    )

    vf = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={w}x{h}:r={fps}:d={duration_s}",
        "-vf", vf,
        "-pix_fmt", "yuv420p",
        title_mp4
    ]
    subprocess.run(cmd, check=True)


def concat_title_and_sim_reencode(title_mp4: str, sim_mp4: str, final_mp4: str, fps: int):
    cmd = [
        "ffmpeg", "-y",
        "-i", title_mp4,
        "-i", sim_mp4,
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
        "-map", "[v]",
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        final_mp4
    ]
    subprocess.run(cmd, check=True)


# ----------------------------
# Simulation movie
# ----------------------------
def make_simulation_movie_only(h5_files: list[str], outfile: str, fps: int, axis_mode: str,
                               dataset_path_override: str | None):
    """
    Uses physical GM/c^2 axes if header keys exist.
    Otherwise falls back to pixels + auto-detect dataset.
    """
    # Try physical-units reader first
    physical = read_grmhd_with_units(h5_files[0])

    use_physical = physical is not None
    dataset_path = None

    if use_physical:
        nx, X, Y, I0 = physical
        extent = [X.min(), X.max(), Y.min(), Y.max()]
        xlabel = r"X [$GM/c^2$]"
        ylabel = r"Y [$GM/c^2$]"
    else:
        # fallback
        if dataset_path_override:
            dataset_path = dataset_path_override
        else:
            dataset_path = detect_image_dataset_path(h5_files[0])

        I0 = read_image_from_h5(h5_files[0], dataset_path)
        H, W = I0.shape
        extent = [0, W, 0, H]
        xlabel = "X [pixels]"
        ylabel = "Y [pixels]"

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_axes([0.08, 0.08, 0.84, 0.84])
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    if axis_mode != "none":
        ax.set_xlabel(xlabel, fontsize=10, color="black")
        ax.set_ylabel(ylabel, fontsize=10, color="black")
        for spine in ax.spines.values():
            spine.set_color("black")
            spine.set_linewidth(1)
        ax.tick_params(axis="both", colors="black", direction="out", length=4, width=1, labelsize=9)
    else:
        ax.set_axis_off()

    im = ax.imshow(I0, origin="lower", cmap="afmhot", extent=extent)

    overlay_box = dict(facecolor="black", alpha=0.45, edgecolor="none", boxstyle="round,pad=0.25")

    frame_title = ax.text(
        0.5, 0.98, "",
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=14, color="white", zorder=200, bbox=overlay_box
    )

    fps_text = ax.text(
        0.98, 0.98, f"FPS: {fps}",
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=12, color="white", zorder=200, bbox=overlay_box
    )

    def update(i):
        if use_physical:
            out = read_grmhd_with_units(h5_files[i])
            if out is None:
                raise RuntimeError("Physical header keys disappeared mid-sequence.")
            _, _, _, Ii = out
        else:
            Ii = read_image_from_h5(h5_files[i], dataset_path)

        im.set_array(Ii)
        frame_title.set_text(f"Frame {i+1}/{len(h5_files)}")
        return []

    ani = FuncAnimation(fig, update, frames=len(h5_files), blit=False, interval=1000 / fps)
    writer = FFMpegWriter(fps=fps, bitrate=1800)
    ani.save(outfile, writer=writer)
    plt.close(fig)


# ----------------------------
# Main
# ----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=str)
    ap.add_argument("--outfile", type=str, required=True)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--filename", type=str, default=None)
    ap.add_argument("--title_seconds", type=int, default=5)
    ap.add_argument("--fontfile", type=str, default=FONTFILE_DEFAULT)
    ap.add_argument("--axis_mode", type=str, default="pixels", choices=["pixels", "none"])
    ap.add_argument("--dataset_path", type=str, default=None,
                    help="Override dataset path for fallback mode (when header keys missing)")
    args = ap.parse_args()

    h5_files = list_h5_files(args.folder)

    params = extract_parameters(args.filename) if args.filename else {}

    out_abs = os.path.abspath(args.outfile)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)

    sim_tmp = out_abs + ".sim_only.mp4"
    title_tmp = out_abs + ".title.mp4"

    print(f"Parsed params = {params}")

    make_simulation_movie_only(
        h5_files=h5_files,
        outfile=sim_tmp,
        fps=args.fps,
        axis_mode=args.axis_mode,
        dataset_path_override=args.dataset_path
    )

    w, h = ffprobe_wh(sim_tmp)
    make_title_clip_ffmpeg(
        title_mp4=title_tmp,
        w=w, h=h,
        fps=args.fps,
        duration_s=args.title_seconds,
        title_line="GRMHD SgrA* Simulation",
        param_lines=build_param_lines(params),
        credit_line="Created by David Baker",
        fontfile=args.fontfile
    )

    concat_title_and_sim_reencode(title_tmp, sim_tmp, out_abs, fps=args.fps)

    for fp in (sim_tmp, title_tmp):
        if os.path.exists(fp):
            os.remove(fp)

    print(f"Movie saved: {out_abs}")


if __name__ == "__main__":
    main()
