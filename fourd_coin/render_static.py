"""Static renders of the 4D coin: PNG stills and animated GIFs (matplotlib).

Outputs (written next to this script):
  projection_stills.png  -- the 3D shadow of the spherinder at four 4D angles
  slices_stills.png      -- cross-sections at three tilt angles alpha
  rotation.gif           -- double rotation (xw + yz planes) of the shadow
  slicing.gif            -- the w = t scan of a standing coin (alpha = 90 deg)
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap, Normalize

import spherinder as sp

OUT = os.path.dirname(os.path.abspath(__file__))

CMAP = LinearSegmentedColormap.from_list("w_blues", sp.BLUE_RAMP)
W_NORM_PROJ = Normalize(-1.05, 1.05)          # w after arbitrary 4D rotation
W_NORM_SLICE = Normalize(-sp.H_COIN / 2, sp.H_COIN / 2)  # heads face -> tails face

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"


def _setup_axis(ax, lim=1.35):
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    ax.set_facecolor(SURFACE)


def draw_projection(ax, rotation, d=3.0, alpha_face=0.55):
    """Render the spherinder's shadow: two boundary spheres + rim generators."""
    cap_lo, cap_hi = sp.spherinder_caps(n_theta=41, n_phi=81)
    projected = []
    for cap in (cap_lo, cap_hi):
        pts4 = cap @ rotation.T
        p3, w = sp.project(pts4, d=d)
        projected.append((p3, w))
        fc = CMAP(W_NORM_PROJ(w))
        fc[..., 3] = alpha_face
        ax.plot_surface(
            p3[..., 0], p3[..., 1], p3[..., 2],
            facecolors=fc, shade=False, linewidth=0,
            rstride=1, cstride=1, antialiased=False,
        )
    # generators of the curved rim cell S^2 x [-h/2, h/2]
    (a3, _), (b3, _) = projected
    for i in range(0, a3.shape[0], 8):
        for j in range(0, a3.shape[1], 8):
            seg = np.stack([a3[i, j], b3[i, j]])
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2],
                    color=MUTED, linewidth=0.6, alpha=0.6)


def draw_slice(ax, t, tilt, alpha_face=0.95):
    """Render the cross-section w = t of the coin tilted by `tilt`."""
    sl = sp.slice_solid(t, tilt)
    if sl is None:
        return
    X, Y, Z = sp.revolution_mesh(sl["z"], sl["rho"], n_phi=81)
    fc = CMAP(W_NORM_SLICE(np.outer(sl["W"], np.ones(81))))
    fc[..., 3] = alpha_face
    ax.plot_surface(X, Y, Z, facecolors=fc, shade=True, linewidth=0,
                    rstride=1, cstride=1, antialiased=False)
    for z0, rho0, w0 in sl["caps"]:
        Xc, Yc, Zc = sp.disk_mesh(z0, rho0, n_phi=81)
        fc = CMAP(W_NORM_SLICE(np.full(Xc.shape, w0)))
        fc[..., 3] = alpha_face
        ax.plot_surface(Xc, Yc, Zc, facecolors=fc, shade=False, linewidth=0,
                        rstride=1, cstride=1, antialiased=False)


def projection_stills():
    fig = plt.figure(figsize=(12, 3.4), facecolor=SURFACE)
    angles = [0, 30, 60, 90]
    for k, deg in enumerate(angles):
        ax = fig.add_subplot(1, 4, k + 1, projection="3d")
        _setup_axis(ax)
        rot = sp.rot4("xw", np.radians(deg))
        draw_projection(ax, rot)
        ax.set_title(f"xw-rotation {deg}\N{DEGREE SIGN}",
                     color=INK, fontsize=11, pad=0)
    fig.suptitle("Shadow of the 4D coin: perspective projection 4D → 3D "
                 "(color = 4th coordinate w, light → dark)",
                 color=INK, fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "projection_stills.png"), dpi=110,
                facecolor=SURFACE)
    plt.close(fig)


def slices_stills():
    tilts = [0, 45, 90]
    fracs = [0.0, 0.45, 0.75, 0.95]
    fig = plt.figure(figsize=(11, 8.2), facecolor=SURFACE)
    for row, tilt_deg in enumerate(tilts):
        tilt = np.radians(tilt_deg)
        tmax = sp.slice_t_max(tilt)
        for col, f in enumerate(fracs):
            ax = fig.add_subplot(3, 4, row * 4 + col + 1, projection="3d")
            _setup_axis(ax, lim=1.2)
            draw_slice(ax, f * tmax * 0.999, tilt)
            if row == 0:
                ax.set_title(f"t = {f:.2f}·t_max", color=INK, fontsize=10)
            if col == 0:
                ax.text2D(-0.08, 0.5, f"tilt α = {tilt_deg}\N{DEGREE SIGN}",
                          transform=ax.transAxes, color=INK, fontsize=11,
                          rotation=90, va="center")
    fig.suptitle("Slices w = t of the 4D coin at three tilts\n"
                 "α = 0\N{DEGREE SIGN}: lying flat → balls;  "
                 "α = 90\N{DEGREE SIGN}: standing → shrinking coins;  "
                 "color = position between the two flat faces",
                 color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "slices_stills.png"), dpi=110,
                facecolor=SURFACE)
    plt.close(fig)


def rotation_gif(n_frames=48):
    fig = plt.figure(figsize=(4.6, 4.6), facecolor=SURFACE)
    ax = fig.add_subplot(projection="3d")

    def frame(k):
        ax.clear()
        _setup_axis(ax)
        th = 2 * np.pi * k / n_frames
        rot = sp.compose(sp.rot4("yz", th), sp.rot4("xw", th))
        draw_projection(ax, rot)
        ax.set_title("double rotation: xw + yz planes", color=INK, fontsize=10)

    anim = FuncAnimation(fig, frame, frames=n_frames)
    anim.save(os.path.join(OUT, "rotation.gif"),
              writer=PillowWriter(fps=12), savefig_kwargs={"facecolor": SURFACE})
    plt.close(fig)


def slicing_gif(n_frames=48):
    fig = plt.figure(figsize=(4.6, 4.6), facecolor=SURFACE)
    ax = fig.add_subplot(projection="3d")
    tilt = np.pi / 2
    tmax = sp.slice_t_max(tilt)

    def frame(k):
        ax.clear()
        _setup_axis(ax, lim=1.2)
        t = -tmax + 2 * tmax * (k + 0.5) / n_frames
        draw_slice(ax, t, tilt)
        ax.set_title(f"standing coin, slice w = {t:+.2f}", color=INK, fontsize=10)

    anim = FuncAnimation(fig, frame, frames=n_frames)
    anim.save(os.path.join(OUT, "slicing.gif"),
              writer=PillowWriter(fps=12), savefig_kwargs={"facecolor": SURFACE})
    plt.close(fig)


if __name__ == "__main__":
    projection_stills()
    print("projection_stills.png done")
    slices_stills()
    print("slices_stills.png done")
    rotation_gif()
    print("rotation.gif done")
    slicing_gif()
    print("slicing.gif done")
