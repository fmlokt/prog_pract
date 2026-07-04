"""Build spherinder_interactive.html: an interactive 4D-coin explorer.

The page embeds plotly.js (self-contained, works offline) and re-computes the
meshes in JavaScript as you drag the sliders:

  left scene  -- perspective shadow of the spherinder, with sliders for the
                 three 4D rotation planes (xw, yw, zw) and a spin toggle that
                 runs a double rotation (xw + yz simultaneously);
  right scene -- the cross-section w = t, with sliders for the tilt angle
                 alpha (zw-plane) and the slice position t.

The math mirrors spherinder.py exactly.
"""

import os

from plotly.offline import get_plotlyjs

import spherinder as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "spherinder_interactive.html")

RAMP_JS = "[" + ",".join(
    f"[{i / (len(sp.BLUE_RAMP) - 1):.4f},'{c}']"
    for i, c in enumerate(sp.BLUE_RAMP)
) + "]"

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The 4D coin (spherinder)</title>
<style>
  :root {
    --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b;
    --ink-2: #52514e; --muted: #898781; --hair: #e1e0d9;
    --accent: #2a78d6;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff;
      --ink-2: #c3c2b7; --muted: #898781; --hair: #2c2c2a;
      --accent: #3987e5;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--page); color: var(--ink);
    font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  main { max-width: 1180px; margin: 0 auto; padding: 24px 20px 48px; }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  h2 { font-size: 1.05rem; margin: 0 0 2px; }
  p.lead, p.note { color: var(--ink-2); max-width: 72ch; }
  p.note { font-size: 0.88rem; }
  .panels { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 18px; }
  .panel {
    flex: 1 1 460px; background: var(--surface);
    border: 1px solid var(--hair); border-radius: 10px; padding: 14px 16px;
  }
  .plot { width: 100%; height: 480px; }
  .controls { margin-top: 6px; }
  .ctl { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
  .ctl label { width: 11em; color: var(--ink-2); font-size: 0.88rem; }
  .ctl input[type=range] { flex: 1; accent-color: var(--accent); }
  .ctl output {
    width: 5.5em; text-align: right; font-variant-numeric: tabular-nums;
    color: var(--ink); font-size: 0.88rem;
  }
  button, .preset {
    font: inherit; font-size: 0.85rem; color: var(--ink);
    background: transparent; border: 1px solid var(--hair);
    border-radius: 6px; padding: 3px 10px; cursor: pointer;
  }
  button:hover, .preset:hover { border-color: var(--muted); }
  button[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); }
  .presets { display: flex; gap: 8px; margin: 8px 0 2px; flex-wrap: wrap; }
  footer { margin-top: 26px; color: var(--muted); font-size: 0.85rem; }
  code { font-size: 0.9em; }
</style>
</head>
<body>
<main>
  <h1>The 4D coin &mdash; a spherinder explorer</h1>
  <p class="lead">
    A 3D coin is a disk extruded a short distance: D&sup2; &times; [&minus;h/2, h/2].
    One dimension up, the coin becomes a <b>spherinder</b> &mdash; a solid
    3-ball extruded along the 4th axis <i>w</i>:
    &nbsp;B&sup3; &times; [&minus;h/2, h/2] =
    { (x,y,z,w) : x&sup2;+y&sup2;+z&sup2; &le; r&sup2;, |w| &le; h/2 }.
    Its two &ldquo;flat-ish faces&rdquo; are entire <b>solid 3D balls</b> lying in
    parallel hyperplanes (heads and tails), and its rim is the curved cell
    S&sup2; &times; [&minus;h/2, h/2]. Everywhere below, the 4th coordinate
    <i>w</i> is drawn as color, light &rarr; dark.
  </p>

  <div class="panels">
    <div class="panel">
      <h2>Shadow &mdash; perspective projection 4D &rarr; 3D</h2>
      <p class="note">4D rotations happen in <i>planes</i>, not around axes.
        The three sliders rotate the coin in the planes that mix space with
        <i>w</i>; the projection (x,y,z)&middot;d/(d&minus;w) then casts the
        result into 3D, so the two boundary spheres slide apart and through
        each other. Drag the scene itself to orbit in ordinary 3D.</p>
      <div id="proj" class="plot"></div>
      <div class="controls">
        <div class="ctl"><label for="axw">xw-plane angle</label>
          <input id="axw" type="range" min="0" max="360" step="1" value="50">
          <output id="oxw">50&deg;</output></div>
        <div class="ctl"><label for="ayw">yw-plane angle</label>
          <input id="ayw" type="range" min="0" max="360" step="1" value="0">
          <output id="oyw">0&deg;</output></div>
        <div class="ctl"><label for="azw">zw-plane angle</label>
          <input id="azw" type="range" min="0" max="360" step="1" value="0">
          <output id="ozw">0&deg;</output></div>
        <div class="presets">
          <button id="spin" aria-pressed="false">&#9654; spin (double rotation xw + yz)</button>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>Scan &mdash; slices by the hyperplane w = t</h2>
      <p class="note">Tilt the coin by &alpha; in the zw-plane, then sweep the
        slicing hyperplane. Lying flat (&alpha; = 0&deg;) every slice is a full
        ball that pops in and out; standing on its rim (&alpha; = 90&deg;) the
        slices are ordinary 3D coins that shrink as |t| grows. Color shows where
        each point sits between the two flat faces.</p>
      <div id="slice" class="plot"></div>
      <div class="controls">
        <div class="ctl"><label for="tilt">tilt &alpha; (zw-plane)</label>
          <input id="tilt" type="range" min="0" max="90" step="1" value="90">
          <output id="otilt">90&deg;</output></div>
        <div class="ctl"><label for="tfrac">slice position t</label>
          <input id="tfrac" type="range" min="-100" max="100" step="1" value="0">
          <output id="ot">0.00</output></div>
        <div class="presets">
          <button class="preset" data-tilt="0">lying flat</button>
          <button class="preset" data-tilt="45">tilted 45&deg;</button>
          <button class="preset" data-tilt="90">standing on rim</button>
        </div>
      </div>
    </div>
  </div>

  <footer>
    Geometry: r = @@R@@, h = @@H@@. Hypervolume (4/3)&pi;r&sup3;h; boundary
    3-volume 2&middot;(4/3)&pi;r&sup3; + 4&pi;r&sup2;h. Generated by
    <code>fourd_coin/build_interactive.py</code>; math in
    <code>fourd_coin/spherinder.py</code>. The page follows your light/dark
    system theme.
  </footer>
</main>

<script>@@PLOTLYJS@@</script>
<script>
"use strict";
const R = @@R@@, H = @@H@@, D = 3.0;
const RAMP = @@RAMP@@;
const NT = 33, NP = 49;          // sphere grid for the projection view
const NZ = 80, NPS = 49;         // slice: profile samples x revolution steps

/* ---------- theme ---------- */
const darkMq = window.matchMedia("(prefers-color-scheme: dark)");
function theme() {
  const dark = darkMq.matches;
  return {
    surface: dark ? "#1a1a19" : "#fcfcfb",
    ink:     dark ? "#ffffff" : "#0b0b0b",
    muted:   "#898781",
  };
}

/* ---------- small 4D linear algebra ---------- */
function rot4(i, j, a) {
  const m = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]];
  const c = Math.cos(a), s = Math.sin(a);
  m[i][i] = c; m[j][j] = c; m[i][j] = -s; m[j][i] = s;
  return m;
}
function mul4(A, B) {
  const m = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]];
  for (let i = 0; i < 4; i++)
    for (let j = 0; j < 4; j++)
      for (let k = 0; k < 4; k++) m[i][j] += A[i][k] * B[k][j];
  return m;
}
function apply4(m, p) {
  const q = [0, 0, 0, 0];
  for (let i = 0; i < 4; i++)
    for (let k = 0; k < 4; k++) q[i] += m[i][k] * p[k];
  return q;
}

/* ---------- projection view ---------- */
const sphereDir = [];            // unit sphere grid, computed once
for (let i = 0; i < NT; i++) {
  const th = Math.PI * i / (NT - 1), row = [];
  for (let j = 0; j < NP; j++) {
    const ph = 2 * Math.PI * j / (NP - 1);
    row.push([Math.sin(th) * Math.cos(ph), Math.sin(th) * Math.sin(ph),
              Math.cos(th)]);
  }
  sphereDir.push(row);
}

function projectionTraces(axw, ayw, azw, spinYZ) {
  const rot = mul4(rot4(0, 3, axw), mul4(rot4(1, 3, ayw),
              mul4(rot4(2, 3, azw), rot4(1, 2, spinYZ))));
  const caps = [], pts = [];
  [-H / 2, H / 2].forEach((wc, ci) => {
    const X = [], Y = [], Z = [], C = [], T = [], P3 = [];
    for (let i = 0; i < NT; i++) {
      const xr = [], yr = [], zr = [], cr = [], tr = [], pr = [];
      for (let j = 0; j < NP; j++) {
        const d = sphereDir[i][j];
        const q = apply4(rot, [R * d[0], R * d[1], R * d[2], wc]);
        const f = D / (D - q[3]);
        xr.push(q[0] * f); yr.push(q[1] * f); zr.push(q[2] * f);
        cr.push(q[3]); tr.push("w′ = " + q[3].toFixed(2));
        pr.push([q[0] * f, q[1] * f, q[2] * f]);
      }
      X.push(xr); Y.push(yr); Z.push(zr); C.push(cr); T.push(tr); P3.push(pr);
    }
    pts.push(P3);
    caps.push({
      type: "surface", x: X, y: Y, z: Z, surfacecolor: C, text: T,
      colorscale: RAMP, cmin: -1.05, cmax: 1.05, opacity: 0.85,
      hovertemplate: "%{text}<extra>" + (ci ? "tails" : "heads") +
                     " sphere</extra>",
      showscale: ci === 0,
      colorbar: { title: { text: "w′" }, thickness: 12, len: 0.6,
                  outlinewidth: 0, tickfont: { color: theme().muted } },
      lighting: { ambient: 0.9, diffuse: 0.3, specular: 0.05 },
    });
  });
  const lx = [], ly = [], lz = [];   // rim generators, null-separated
  for (let i = 0; i < NT; i += 4)
    for (let j = 0; j < NP; j += 6) {
      lx.push(pts[0][i][j][0], pts[1][i][j][0], null);
      ly.push(pts[0][i][j][1], pts[1][i][j][1], null);
      lz.push(pts[0][i][j][2], pts[1][i][j][2], null);
    }
  caps.push({ type: "scatter3d", mode: "lines", x: lx, y: ly, z: lz,
              line: { color: theme().muted, width: 1.5 }, opacity: 0.55,
              hoverinfo: "skip", showlegend: false });
  return caps;
}

/* ---------- slice view ---------- */
function tMax(a) {
  return R * Math.abs(Math.sin(a)) + (H / 2) * Math.abs(Math.cos(a));
}
function sliceTraces(a, frac) {
  const ca = Math.cos(a), sa = Math.sin(a);
  const t = 0.999 * frac * tMax(a);
  const BIG = 1e9, eps = 1e-9;
  let b0 = -BIG, b1 = BIG, h0 = -BIG, h1 = BIG;
  if (Math.abs(ca) > eps) {
    b0 = (-R - t * sa) / ca; b1 = (R - t * sa) / ca;
    if (b0 > b1) [b0, b1] = [b1, b0];
  } else if (Math.abs(t * sa) > R) return { traces: [], t: t };
  if (Math.abs(sa) > eps) {
    h0 = (t * ca - H / 2) / sa; h1 = (t * ca + H / 2) / sa;
    if (h0 > h1) [h0, h1] = [h1, h0];
  } else if (Math.abs(t * ca) > H / 2) return { traces: [], t: t };
  const z0 = Math.max(b0, h0), z1 = Math.min(b1, h1);
  if (z0 >= z1) return { traces: [], t: t };

  const zs = [], rho = [], W = [];
  for (let i = 0; i < NZ; i++) {
    const z = z0 + (z1 - z0) * i / (NZ - 1);
    const Zb = z * ca + t * sa;
    zs.push(z);
    rho.push(Math.sqrt(Math.max(R * R - Zb * Zb, 0)));
    W.push(t * ca - z * sa);
  }
  const traces = [];
  function revSurface(radii, zvals, wvals, isCap) {
    const X = [], Y = [], Z = [], C = [], T = [];
    for (let i = 0; i < radii.length; i++) {
      const xr = [], yr = [], zr = [], cr = [], tr = [];
      for (let j = 0; j < NPS; j++) {
        const ph = 2 * Math.PI * j / (NPS - 1);
        xr.push(radii[i] * Math.cos(ph)); yr.push(radii[i] * Math.sin(ph));
        zr.push(zvals[i]); cr.push(wvals[i]);
        tr.push("W = " + wvals[i].toFixed(3));
      }
      X.push(xr); Y.push(yr); Z.push(zr); C.push(cr); T.push(tr);
    }
    return {
      type: "surface", x: X, y: Y, z: Z, surfacecolor: C, text: T,
      colorscale: RAMP, cmin: -H / 2, cmax: H / 2,
      hovertemplate: "%{text}<extra>" +
                     (isCap ? "flat face" : "slice") + "</extra>",
      showscale: !isCap,
      colorbar: { title: { text: "W (thickness)" }, thickness: 12, len: 0.6,
                  outlinewidth: 0, tickfont: { color: theme().muted } },
      lighting: { ambient: 0.75, diffuse: 0.5, specular: 0.05 },
    };
  }
  traces.push(revSurface(rho, zs, W, false));
  [[0, rho[0], zs[0], W[0]], [NZ - 1, rho[NZ - 1], zs[NZ - 1], W[NZ - 1]]]
    .forEach(([_, r0, zc, wc]) => {
      if (r0 > 1e-3 * R) {
        const NS = 10, radii = [], zvals = [], wvals = [];
        for (let i = 0; i < NS; i++) {
          radii.push(r0 * i / (NS - 1)); zvals.push(zc); wvals.push(wc);
        }
        traces.push(revSurface(radii, zvals, wvals, true));
      }
    });
  return { traces: traces, t: t };
}

/* ---------- layout & wiring ---------- */
function makeLayout(lim) {
  const th = theme();
  const ax = { visible: false, range: [-lim, lim] };
  return {
    margin: { l: 0, r: 0, t: 0, b: 0 },
    paper_bgcolor: th.surface,
    uirevision: "keep",
    scene: {
      xaxis: ax, yaxis: { ...ax }, zaxis: { ...ax },
      aspectmode: "cube", bgcolor: th.surface, uirevision: "keep",
      camera: { eye: { x: 1.45, y: 1.45, z: 0.9 } },
    },
    font: { color: th.ink, family: "system-ui, sans-serif" },
  };
}
const CFG = { displayModeBar: false, responsive: true };

const el = (id) => document.getElementById(id);
let spinning = false, spinYZ = 0;

function redrawProjection() {
  const axw = +el("axw").value, ayw = +el("ayw").value, azw = +el("azw").value;
  el("oxw").innerHTML = axw + "&deg;";
  el("oyw").innerHTML = ayw + "&deg;";
  el("ozw").innerHTML = azw + "&deg;";
  const tr = projectionTraces(axw * Math.PI / 180, ayw * Math.PI / 180,
                              azw * Math.PI / 180, spinYZ);
  Plotly.react("proj", tr, makeLayout(1.65), CFG);
}
function redrawSlice() {
  const a = +el("tilt").value, f = +el("tfrac").value / 100;
  el("otilt").innerHTML = a + "&deg;";
  const res = sliceTraces(a * Math.PI / 180, f);
  el("ot").textContent = res.t.toFixed(2);
  Plotly.react("slice", res.traces, makeLayout(1.15), CFG);
}

["axw", "ayw", "azw"].forEach((id) =>
  el(id).addEventListener("input", redrawProjection));
["tilt", "tfrac"].forEach((id) =>
  el(id).addEventListener("input", redrawSlice));
document.querySelectorAll(".preset[data-tilt]").forEach((b) =>
  b.addEventListener("click", () => {
    el("tilt").value = b.dataset.tilt; redrawSlice();
  }));

el("spin").addEventListener("click", () => {
  spinning = !spinning;
  el("spin").setAttribute("aria-pressed", String(spinning));
  if (spinning) requestAnimationFrame(spinStep);
});
let lastTs = null;
function spinStep(ts) {
  if (!spinning) { lastTs = null; return; }
  const dt = lastTs === null ? 16 : Math.min(ts - lastTs, 100);
  lastTs = ts;
  const rate = 20 * dt / 1000;               // degrees per second
  el("axw").value = (+el("axw").value + rate) % 360;
  spinYZ = (spinYZ + rate * Math.PI / 180) % (2 * Math.PI);
  redrawProjection();
  requestAnimationFrame(spinStep);
}

darkMq.addEventListener("change", () => { redrawProjection(); redrawSlice(); });
redrawProjection();
redrawSlice();
</script>
</body>
</html>
"""


def main():
    html = (PAGE
            .replace("@@PLOTLYJS@@", get_plotlyjs())
            .replace("@@RAMP@@", RAMP_JS)
            .replace("@@R@@", f"{sp.R_COIN:g}")
            .replace("@@H@@", f"{sp.H_COIN:g}"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
