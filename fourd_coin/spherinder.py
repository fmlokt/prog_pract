"""Math core for visualizing a 4D coin (spherinder).

The spherinder is the 4D analog of a coin: a solid 3-ball extruded a short
distance along the 4th axis,

    B^3 x [-h/2, h/2] = { (x,y,z,w) : x^2+y^2+z^2 <= r^2, |w| <= h/2 }.

Its boundary consists of two *flat* cells (solid balls at w = -h/2 and
w = +h/2 -- the "heads" and "tails" faces, each lying inside a 3D hyperplane)
and one *curved* cell (the rim, a sphere S^2 x [-h/2, h/2]).

Two ways to show it in 3D:

* Projection ("shadow"): rotate in 4D, then map (x,y,z,w) -> (x,y,z)*d/(d-w).
* Slicing ("scan"): intersect with the hyperplane w = t. If the coin is
  tilted by angle alpha in the zw-plane, every slice is a solid of revolution
  about the z-axis, so it can be computed in closed form (see slice_solid).
"""

import numpy as np

R_COIN = 1.0    # ball radius
H_COIN = 0.28   # thickness along the 4th axis

_AXIS = {"x": 0, "y": 1, "z": 2, "w": 3}


def rot4(plane, angle):
    """Rotation matrix in one coordinate plane of R^4, e.g. rot4('xw', a).

    4D rotations happen in planes, not around axes; there are six coordinate
    planes (xy, xz, yz, xw, yw, zw).
    """
    i, j = _AXIS[plane[0]], _AXIS[plane[1]]
    c, s = np.cos(angle), np.sin(angle)
    m = np.eye(4)
    m[i, i] = c
    m[j, j] = c
    m[i, j] = -s
    m[j, i] = s
    return m


def compose(*mats):
    """Product of rotation matrices, applied right-to-left."""
    out = np.eye(4)
    for m in mats:
        out = m @ out
    return out


def sphere_grid(n_theta=25, n_phi=49, r=R_COIN):
    """Latitude/longitude mesh of a sphere, as (n_theta, n_phi) arrays."""
    theta = np.linspace(0.0, np.pi, n_theta)
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi)
    t, p = np.meshgrid(theta, phi, indexing="ij")
    return r * np.sin(t) * np.cos(p), r * np.sin(t) * np.sin(p), r * np.cos(t)


def spherinder_caps(n_theta=25, n_phi=49, r=R_COIN, h=H_COIN):
    """4D vertices of the two boundary spheres S^2(r) x {-h/2, +h/2}.

    Returns two arrays of shape (n_theta, n_phi, 4). These spheres bound the
    flat ball-cells of the spherinder; connecting corresponding points sweeps
    out the curved rim cell S^2 x [-h/2, h/2].
    """
    x, y, z = sphere_grid(n_theta, n_phi, r)
    caps = []
    for w in (-h / 2.0, h / 2.0):
        caps.append(np.stack([x, y, z, np.full_like(x, w)], axis=-1))
    return caps[0], caps[1]


def project(points4, d=3.0, perspective=True):
    """Project 4D points to 3D. Returns (points3, w) with w the 4D depth.

    Perspective projection scales by d/(d - w): parts of the object nearer
    in w appear larger -- the 4D analog of ordinary foreshortening.
    """
    w = points4[..., 3]
    f = d / (d - w) if perspective else np.ones_like(w)
    return points4[..., :3] * f[..., None], w


def slice_t_max(alpha, r=R_COIN, h=H_COIN):
    """Half-extent of the tilted spherinder along w (slices exist for |t| < this)."""
    return r * abs(np.sin(alpha)) + (h / 2.0) * abs(np.cos(alpha))


def _interval_intersect(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if lo < hi else None


def slice_solid(t, alpha, r=R_COIN, h=H_COIN, n_z=160, eps=1e-9):
    """Cross-section {w = t} of the spherinder tilted by alpha in the zw-plane.

    A point (x, y, z) of the slice pulls back to object coordinates
        Z = z*cos(alpha) + t*sin(alpha),   W = t*cos(alpha) - z*sin(alpha),
    and must satisfy x^2 + y^2 + Z^2 <= r^2 and |W| <= h/2. Since x, y enter
    only through x^2 + y^2, every slice is a solid of revolution about z with
    radius profile rho(z) = sqrt(r^2 - Z(z)^2).

    alpha = 0    -> a full ball that pops in and out ("coin lying flat");
    alpha = pi/2 -> an ordinary 3D coin of radius sqrt(r^2 - t^2)
                    ("coin standing on its rim" -- a family of shrinking coins).

    Returns None if the slice is empty, else a dict with:
      z    : (n_z,) axis samples
      rho  : (n_z,) revolution radii
      W    : (n_z,) original 4th coordinate of each ring (for coloring:
             W = -h/2 is the "heads" face, W = +h/2 the "tails" face)
      caps : list of (z_end, rho_end, W_end) where the slice is cut off by a
             flat face of the coin and needs a disk cap.
    """
    ca, sa = np.cos(alpha), np.sin(alpha)

    if abs(ca) < eps:  # ball condition on z degenerate in z? no: on t
        iv_ball = (-np.inf, np.inf) if abs(t * sa) <= r else None
    else:
        b0, b1 = (-r - t * sa) / ca, (r - t * sa) / ca
        iv_ball = (min(b0, b1), max(b0, b1))
    if abs(sa) < eps:
        iv_h = (-np.inf, np.inf) if abs(t * ca) <= h / 2.0 else None
    else:
        h0, h1 = (t * ca - h / 2.0) / sa, (t * ca + h / 2.0) / sa
        iv_h = (min(h0, h1), max(h0, h1))
    if iv_ball is None or iv_h is None:
        return None
    iv = _interval_intersect(iv_ball, iv_h)
    if iv is None:
        return None

    z = np.linspace(iv[0], iv[1], n_z)
    rho = np.sqrt(np.clip(r * r - (z * ca + t * sa) ** 2, 0.0, None))
    W = t * ca - z * sa

    caps = []
    for k in (0, n_z - 1):
        if rho[k] > 1e-3 * r:  # cut by a flat face, not tapered by the ball
            caps.append((z[k], rho[k], W[k]))
    return {"z": z, "rho": rho, "W": W, "caps": caps}


def revolution_mesh(z, rho, n_phi=49):
    """Mesh a solid-of-revolution profile into (X, Y, Z) surface grids."""
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi)
    return (
        np.outer(rho, np.cos(phi)),
        np.outer(rho, np.sin(phi)),
        np.outer(z, np.ones_like(phi)),
    )


def disk_mesh(z0, rho0, n_s=12, n_phi=49):
    """Mesh a flat disk cap of radius rho0 in the plane z = z0."""
    s = np.linspace(0.0, rho0, n_s)
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi)
    return (
        np.outer(s, np.cos(phi)),
        np.outer(s, np.sin(phi)),
        np.full((n_s, n_phi), z0),
    )


# Sequential single-hue blue ramp (light -> dark) used to encode the 4th
# coordinate w in every view.
BLUE_RAMP = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
    "#0d366b",
]
