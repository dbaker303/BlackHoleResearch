#!/usr/bin/env python3
import os
import re
import argparse
import subprocess

import numpy as np
import h5py

import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter


FONTFILE_DEFAULT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


# ============================================================
# Filename parameter parsing (underscore-delimited safe)
# Example: 2022_sgra_230GHz_Ma+0.5_w5_i_10_PA_0_Rhigh_10
# ============================================================

def extract_parameters(name: str) -> dict:
    """
    Robust parsing for underscore-delimited tokens.
    Avoids regex word-boundary issues with '_' (underscore is a "word char").
    """
    params = {}

    # Frequency: 230GHz
    m = re.search(r"(\d+)\s*GHz", name, flags=re.IGNORECASE)
    if m:
        params["frequency"] = m.group(1)

    # Spin: token like _Ma+0.5_ or starts/ends
    m = re.search(r"(?:^|_)Ma([+\-]?\d*\.?\d+)(?:_|$)", name)
    if m:
        params["spin"] = m.group(1)

    # Inclination: _i_10_
    m = re.search(r"(?:^|_)i_(\d+)(?:_|$)", name, flags=re.IGNORECASE)
    if m:
        params["inclination"] = m.group(1)

    # Position angle: _PA_0_ (or pa)
    m = re.search(r"(?:^|_)(?:PA|pa)_([+\-]?\d*\.?\d+)(?:_|$)", name)
    if m:
        params["pa"] = m.group(1)

    # Rhigh: _Rhigh_10_
    m = re.search(r"(?:^|_)Rhigh_(\d+)(?:_|$)", name, flags=re.IGNORECASE)
    if m:
        params["rhigh"] = m.group(1)

    return params


# ============================================================
# HDF5 utilities: auto-detect a 2D image dataset
# ============================================================

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
            if not _is_numeric_dataset(ds):
                return
            if ds.ndim < 2:
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
        raise RuntimeError(
            f"Could not auto-detect a 2D image dataset in: {h5_file}\n"
            f"Try providing --dataset_path manually after inspecting keys."
        )

    candidates.sort(key=lambda x: x[0], reverse=True)

    print("Auto-detect dataset candidates (top 10):")
    for s, n, sh, dt in candidates[:10]:
        print(f"  score={s:7.2f}  path={n:45s}  shape={sh}  dtype={dt}")

    best = candidates[0]
    print(f"Selected dataset path: {best[1]} (shape={best[2]})")
    return best[1]


def read_image_from_h5(h5_file: str, dataset_path: str) -> np.ndarray:
    with h5py.File(h5_file, "r") as f:
        if dataset_path not in f:
            raise KeyError(f"Dataset path '{dataset_path}' not found in {h5_file}")
        arr = np.array(f[dataset_path])

    img = _as_2d_image(arr)
    if img is None:
        raise RuntimeError(f"Dataset '{dataset_path}' not convertible to 2D. Shape={arr.shape}")
    return img


# ============================================================
# Movie generation helpers
# ============================================================

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
    """if "pa" in params:
        lines.append(f"Position Angle: {params['pa']}°")"""
    if "rhigh" in params:
        lines.append(f"R_high: {params['rhigh']}")
    return lines


def make_simulation_movie_only(
    h5_files: list[str],
    dataset_path: str,
    outfile: str,
    fps: int,
    axis_mode: str = "pixels",
):
    img0 = read_image_from_h5(h5_files[0], dataset_path)
    H, W = img0.shape

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_axes([0.08, 0.08, 0.84, 0.84])
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    if axis_mode == "pixels":
        extent = [0, W, 0, H]
        ax.set_xlabel("X [pixels]", fontsize=10, color="black")
        ax.set_ylabel("Y [pixels]", fontsize=10, color="black")
        for spine in ax.spines.values():
            spine.set_color("black")
            spine.set_linewidth(1)
        ax.tick_params(axis="both", colors="black", direction="out", length=4, width=1, labelsize=9)
    else:
        extent = None
        ax.set_axis_off()

    im = ax.imshow(
        img0,
        origin="lower",
        cmap="afmhot",
        extent=extent
    )

    # Make overlays visible on dark image: white text with semi-transparent black box
    overlay_box = dict(facecolor="black", alpha=0.45, edgecolor="none", boxstyle="round,pad=0.25")

    frame_title = ax.text(
        0.5, 0.98, "",
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=14, color="white", zorder=200,
        bbox=overlay_box
    )

    fps_text = ax.text(
        0.98, 0.98, f"FPS: {fps}",
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=12, color="white", zorder=200,
        bbox=overlay_box
    )

    def update(i):
        img = read_image_from_h5(h5_files[i], dataset_path)
        im.set_array(img)
        frame_title.set_text(f"Frame {i+1}/{len(h5_files)}")
        return []

    ani = FuncAnimation(fig, update, frames=len(h5_files), blit=False, interval=1000 / fps)
    writer = FFMpegWriter(fps=fps, bitrate=1800)
    ani.save(outfile, writer=writer)
    plt.close(fig)


def _ff_escape_text(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    return s


def make_title_clip_ffmpeg(
    title_mp4: str,
    w: int,
    h: int,
    fps: int,
    duration_s: int,
    title_line: str,
    param_lines: list[str],
    credit_line: str,
    fontfile: str,
):
    """
    Title slide:
      - centered title
      - each parameter line centered
      - moved down a bit
      - evenly spaced parameter lines
    """
    if not os.path.exists(fontfile):
        raise FileNotFoundError(f"Font file not found: {fontfile}")

    # Layout tuning
    top_y = 0.28          # title y fraction (moved down)
    params_start = 0.42   # first param y fraction
    params_end = 0.60     # last param y fraction
    title_fs = 54
    param_fs = 30
    credit_fs = 24
    margin = 50

    filters = []

    title_e = _ff_escape_text(title_line)
    filters.append(
        f"drawtext=fontfile={fontfile}:text='{title_e}':fontcolor=white:fontsize={title_fs}:"
        f"x=(w-text_w)/2:y=h*{top_y}"
    )

    if param_lines:
        n = len(param_lines)
        if n == 1:
            y_fracs = [params_start]
        else:
            step = (params_end - params_start) / (n - 1)
            y_fracs = [params_start + step * i for i in range(n)]

        for line, y_frac in zip(param_lines, y_fracs):
            line_e = _ff_escape_text(line)
            filters.append(
                f"drawtext=fontfile={fontfile}:text='{line_e}':fontcolor=white:fontsize={param_fs}:"
                f"x=(w-text_w)/2:y=h*{y_frac}"
            )

    credit_e = _ff_escape_text(credit_line)
    filters.append(
        f"drawtext=fontfile={fontfile}:text='{credit_e}':fontcolor=white:fontsize={credit_fs}:"
        f"x=w-text_w-{margin}:y=h-{margin}"
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


# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser(description="Create a GRMHD movie from extracted .h5 frames with a title card.")
    ap.add_argument("folder", type=str, help="Folder containing extracted .h5 frames")
    ap.add_argument("--outfile", type=str, required=True, help="Output mp4")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--filename", type=str, default=None, help="Basename for parameter parsing")
    ap.add_argument("--title_seconds", type=int, default=5)
    ap.add_argument("--fontfile", type=str, default=FONTFILE_DEFAULT)
    ap.add_argument("--axis_mode", type=str, default="pixels", choices=["pixels", "none"])
    ap.add_argument("--dataset_path", type=str, default=None,
                    help="Optional: manually set image dataset path inside HDF5")
    args = ap.parse_args()

    h5_files = list_h5_files(args.folder)

    dataset_path = args.dataset_path
    if not dataset_path:
        dataset_path = detect_image_dataset_path(h5_files[0])

    params = extract_parameters(args.filename) if args.filename else {}
    out_abs = os.path.abspath(args.outfile)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)

    sim_tmp = out_abs + ".sim_only.mp4"
    title_tmp = out_abs + ".title.mp4"

    print(f"Using dataset_path = {dataset_path}")
    print(f"Axis mode        = {args.axis_mode}")
    print(f"Parsed params    = {params}")

    make_simulation_movie_only(
        h5_files=h5_files,
        dataset_path=dataset_path,
        outfile=sim_tmp,
        fps=args.fps,
        axis_mode=args.axis_mode
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
