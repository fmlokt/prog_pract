"""Build spherinder_interactive.html: a cinematic WebGL one-pager of the 4D coin.

Three.js (vendored in vendor/three.module.js, inlined at build time) renders
the spherinder B^3 x [-h/2, h/2] with all 4D math on the GPU: the geometry is
static, and vertex shaders apply the 4D plane rotations, the perspective
projection (x,y,z)*d/(d-w), and the closed-form hyperplane slice from
spherinder.py, driven by uniforms.

The page is a single full-viewport scene with no text. An autonomous
choreography loops: double-rotation shadow -> tilt upright -> a glowing slice
sweeps through the ghost (the "family of shrinking coins") -> flat scan
(balls popping in and out, flipped: tails-first) -> back. Drag orbits,
scroll zooms. Append ?static=SECONDS to freeze the timeline at a moment;
window.__seek(SECONDS) jumps the running timeline.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spherinder_interactive.html")
THREE = os.path.join(HERE, "vendor", "three.module.js")

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>4D coin</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #04060c; }
  canvas { position: fixed; inset: 0; display: block; cursor: grab;
           opacity: 0; animation: reveal 2.2s ease 0.15s forwards; }
  canvas:active { cursor: grabbing; }
  @keyframes reveal { to { opacity: 1; } }
  #vignette {
    position: fixed; inset: 0; pointer-events: none;
    background: radial-gradient(115% 100% at 50% 45%,
      transparent 55%, rgba(2, 3, 8, 0.55) 100%);
  }
  #grain {
    position: fixed; inset: -100px; pointer-events: none; opacity: 0.07;
    mix-blend-mode: overlay;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    animation: grain 0.9s steps(3) infinite;
  }
  @keyframes grain {
    0% { transform: translate(0, 0); }
    33% { transform: translate(-30px, 18px); }
    66% { transform: translate(22px, -26px); }
    100% { transform: translate(0, 0); }
  }
</style>
</head>
<body>
<div id="vignette"></div>
<div id="grain"></div>
<script type="module">
@@THREE@@

/* ================= 4D coin: B^3(R) x [-H/2, H/2] ================= */
const R = 1.0, H = 0.28, D4 = 3.0;
const GLSL_R = R.toFixed(4), GLSL_HH = (H / 2).toFixed(4);

const shared = {
  uAxw:  { value: 0 },   // rotation angle in the xw-plane
  uAyz:  { value: 0 },   // rotation angle in the yz-plane (ordinary 3D)
  uAzw:  { value: 0 },   // tilt angle in the zw-plane
  uD:    { value: D4 },  // 4D perspective distance
  uWMax: { value: H / 2 },
  uTime: { value: 0 },
};

/* GLSL: 4D plane rotations, perspective projection, sequential blue ramp. */
const CHUNK = /* glsl */`
  uniform float uAxw, uAyz, uAzw, uD, uWMax, uTime;
  vec4 rot4(vec4 p) {
    float c, s, a, b;
    c = cos(uAxw); s = sin(uAxw); a = p.x; b = p.w;
    p.x = c*a - s*b; p.w = s*a + c*b;
    c = cos(uAyz); s = sin(uAyz); a = p.y; b = p.z;
    p.y = c*a - s*b; p.z = s*a + c*b;
    c = cos(uAzw); s = sin(uAzw); a = p.z; b = p.w;
    p.z = c*a - s*b; p.w = s*a + c*b;
    return p;
  }
  vec3 rampW(float x) {           /* x in [-1,1], light -> dark blue */
    x = clamp(x * 0.5 + 0.5, 0.0, 1.0);
    vec3 c0 = vec3(0.804, 0.886, 0.984);   /* #cde2fb */
    vec3 c1 = vec3(0.427, 0.655, 0.925);   /* #6da7ec */
    vec3 c2 = vec3(0.165, 0.471, 0.839);   /* #2a78d6 */
    vec3 c3 = vec3(0.063, 0.259, 0.506);   /* #104281 */
    return x < 0.34 ? mix(c0, c1, x / 0.34)
         : x < 0.67 ? mix(c1, c2, (x - 0.34) / 0.33)
                    : mix(c2, c3, (x - 0.67) / 0.33);
  }
`;

/* differential of p -> proj4(rot4(p)) along tangent t (for exact normals) */
const DIFF = /* glsl */`
  vec3 dProj(vec4 t, vec4 q, float s) {
    vec4 dq = rot4(t);
    return s * (dq.xyz + q.xyz * (dq.w / (uD - q.w)));
  }
`;

/* -------------------- background gradient -------------------- */
const bgVert = /* glsl */`
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = vec4(position.xy, 1.0, 1.0); }
`;
const bgFrag = /* glsl */`
  varying vec2 vUv;
  void main() {
    float d = length((vUv - vec2(0.5, 0.42)) * vec2(1.35, 1.15));
    vec3 col = mix(vec3(0.049, 0.084, 0.152),   /* #0c1526 */
                   vec3(0.016, 0.024, 0.047),   /* #04060c */
                   smoothstep(0.0, 0.85, d));
    gl_FragColor = vec4(col, 1.0);
  }
`;

/* ---------------- ghost: the two boundary spheres ---------------- */
const ghostVert = CHUNK + DIFF + /* glsl */`
  uniform float uCapW;
  varying vec3 vN, vV; varying float vW;
  void main() {
    vec4 q = rot4(vec4(position, uCapW));
    float s = uD / (uD - q.w);
    vec3 pos = q.xyz * s;
    vec3 n = normalize(position);
    vec3 up = abs(n.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 t1 = normalize(cross(up, n));
    vec3 t2 = cross(n, t1);
    vec3 d1 = dProj(vec4(t1, 0.0), q, s);
    vec3 d2 = dProj(vec4(t2, 0.0), q, s);
    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    vN = normalize(normalMatrix * normalize(cross(d1, d2)));
    vV = -mv.xyz;
    vW = q.w;
    gl_Position = projectionMatrix * mv;
  }
`;
const ghostFrag = CHUNK + /* glsl */`
  uniform float uOpacity;
  varying vec3 vN, vV; varying float vW;
  void main() {
    vec3 N = normalize(vN), V = normalize(vV);
    float fr = pow(1.0 - abs(dot(N, V)), 2.6);
    vec3 base = rampW(clamp(vW / uWMax, -1.0, 1.0));
    vec3 col = base * (0.05 + 1.9 * fr)
             + vec3(0.85, 0.93, 1.0) * pow(fr, 3.0) * 0.55;
    gl_FragColor = vec4(col * uOpacity, 1.0);
  }
`;

/* ------------- lines: rim generators + great circles ------------- */
const lineVert = CHUNK + /* glsl */`
  attribute float aW;
  varying float vW;
  void main() {
    vec4 q = rot4(vec4(position, aW));
    float s = uD / (uD - q.w);
    vW = q.w;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(q.xyz * s, 1.0);
  }
`;
const lineFrag = CHUNK + /* glsl */`
  uniform float uOpacity, uGain;
  varying float vW;
  void main() {
    vec3 col = rampW(clamp(vW / uWMax, -1.0, 1.0));
    gl_FragColor = vec4((col * 0.8 + 0.2) * uGain * uOpacity, 1.0);
  }
`;

/* ------------------- particles: boundary dust ------------------- */
const dustVert = CHUNK + /* glsl */`
  attribute float aW, aSeed;
  uniform float uPxScale;
  varying float vW, vTw;
  void main() {
    vec4 q = rot4(vec4(position, aW));
    float s = uD / (uD - q.w);
    vec4 mv = modelViewMatrix * vec4(q.xyz * s, 1.0);
    vW = q.w;
    vTw = 0.35 + 0.65 * (0.5 + 0.5 * sin(uTime * (0.6 + aSeed) + aSeed * 40.0));
    gl_PointSize = (1.6 + 2.8 * fract(aSeed * 7.31)) * uPxScale * (4.7 / -mv.z);
    gl_Position = projectionMatrix * mv;
  }
`;
const dustFrag = CHUNK + /* glsl */`
  uniform float uOpacity;
  varying float vW, vTw;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    float a = smoothstep(0.5, 0.08, d) * vTw * uOpacity;
    vec3 col = rampW(clamp(vW / uWMax, -1.0, 1.0)) * 0.85 + 0.15;
    gl_FragColor = vec4(col * a, 1.0);
  }
`;

/* --------- slice: cross-section w = t, computed in-shader ---------
   A point (x,y,z) at w = t pulls back through the zw-tilt to
   Z = z*ca + t*sa, W = t*ca - z*sa; it belongs to the coin iff
   x^2+y^2+Z^2 <= R^2 and |W| <= H/2, so the slice is a solid of
   revolution with radius sqrt(R^2 - Z(z)^2) over a z-interval. */
const SLICE = /* glsl */`
  uniform float uT;
  const float BIG = 1.0e6;
  void sliceInterval(out float z0, out float z1, out float valid) {
    float ca = cos(uAzw), sa = sin(uAzw), t = uT;
    float b0 = -BIG, b1 = BIG, h0 = -BIG, h1 = BIG;
    valid = 1.0;
    if (abs(ca) > 1.0e-6) {
      b0 = (-${GLSL_R} - t * sa) / ca; b1 = (${GLSL_R} - t * sa) / ca;
      if (b0 > b1) { float tmp = b0; b0 = b1; b1 = tmp; }
    } else if (abs(t * sa) > ${GLSL_R}) { valid = 0.0; }
    if (abs(sa) > 1.0e-6) {
      h0 = (t * ca - ${GLSL_HH}) / sa; h1 = (t * ca + ${GLSL_HH}) / sa;
      if (h0 > h1) { float tmp = h0; h0 = h1; h1 = tmp; }
    } else if (abs(t * ca) > ${GLSL_HH}) { valid = 0.0; }
    z0 = max(b0, h0); z1 = min(b1, h1);
    valid *= step(z0, z1);
    z1 = max(z1, z0);
  }
`;
const sliceVert = CHUNK + SLICE + /* glsl */`
  varying vec3 vN, vV; varying float vW;
  void main() {
    float z0, z1, valid;
    sliceInterval(z0, z1, valid);
    float ca = cos(uAzw), sa = sin(uAzw), t = uT;
    float z = mix(z0, z1, uv.x);
    float Zb = z * ca + t * sa;
    float rho = sqrt(max(${GLSL_R} * ${GLSL_R} - Zb * Zb, 0.0)) * valid;
    float phi = uv.y * 6.28318530718;
    vec3 pos = vec3(rho * cos(phi), rho * sin(phi), z)
             * (uD / (uD - t)) * valid;
    float drho = clamp(-Zb * ca / max(rho, 1.0e-4), -60.0, 60.0);
    vec3 nrm = normalize(vec3(cos(phi), sin(phi), -drho));
    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    vN = normalize(normalMatrix * nrm);
    vV = -mv.xyz;
    vW = t * ca - z * sa;
    gl_Position = projectionMatrix * mv;
  }
`;
const capVert = CHUNK + SLICE + /* glsl */`
  uniform float uEnd;                       /* 0 = z0 cap, 1 = z1 cap */
  varying vec3 vN, vV; varying float vW;
  void main() {
    float z0, z1, valid;
    sliceInterval(z0, z1, valid);
    float ca = cos(uAzw), sa = sin(uAzw), t = uT;
    float z = mix(z0, z1, uEnd);
    float Zb = z * ca + t * sa;
    float rho = sqrt(max(${GLSL_R} * ${GLSL_R} - Zb * Zb, 0.0)) * valid;
    float phi = uv.y * 6.28318530718;
    vec3 pos = vec3(uv.x * rho * cos(phi), uv.x * rho * sin(phi), z)
             * (uD / (uD - t)) * valid;
    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    vN = normalize(normalMatrix * vec3(0.0, 0.0, uEnd * 2.0 - 1.0));
    vV = -mv.xyz;
    vW = t * ca - z * sa;
    gl_Position = projectionMatrix * mv;
  }
`;
const sliceFrag = CHUNK + /* glsl */`
  uniform float uSliceOp;
  varying vec3 vN, vV; varying float vW;
  void main() {
    vec3 N = normalize(vN);
    if (!gl_FrontFacing) N = -N;
    vec3 V = normalize(vV);
    vec3 L = normalize(vec3(0.45, 0.75, 0.5));
    float dif = 0.5 + 0.5 * dot(N, L);
    float fr = pow(1.0 - abs(dot(N, V)), 2.0);
    /* keep the coin saturated: skip the palest end of the ramp */
    vec3 base = rampW(mix(-0.45, 1.0,
      clamp(vW / ${GLSL_HH}, -1.0, 1.0) * 0.5 + 0.5));
    vec3 col = base * (0.3 + 0.7 * dif)
             + base * fr * 0.55
             + vec3(0.7, 0.85, 1.0) * pow(fr, 3.0) * 0.3;
    gl_FragColor = vec4(col, uSliceOp);
  }
`;

/* ============================ scene ============================ */
const renderer = new WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.setClearColor(0x04060c, 1);
document.body.appendChild(renderer.domElement);

const scene = new Scene();
const camera = new PerspectiveCamera(32, innerWidth / innerHeight, 0.1, 60);

function mat(vert, frag, extra, opts) {
  return new ShaderMaterial(Object.assign({
    uniforms: Object.assign({}, shared, extra),
    vertexShader: vert, fragmentShader: frag,
  }, opts));
}

/* background gradient (fullscreen quad at the far plane) */
const bg = new Mesh(new PlaneGeometry(2, 2),
  new ShaderMaterial({ vertexShader: bgVert, fragmentShader: bgFrag,
                       depthWrite: false, depthTest: false }));
bg.renderOrder = -10;
bg.frustumCulled = false;
scene.add(bg);

/* ghost spheres (heads / tails boundary spheres of the flat cells) */
const ghostGeo = new SphereGeometry(R, 128, 80);
const ghostOp = { value: 1 };
for (const wc of [-H / 2, H / 2]) {
  const m = new Mesh(ghostGeo, mat(ghostVert, ghostFrag, {
    uCapW: { value: wc }, uOpacity: ghostOp,
  }, {
    transparent: true, depthWrite: false, side: DoubleSide,
    blending: AdditiveBlending,
  }));
  m.renderOrder = 2;
  m.frustumCulled = false;
  scene.add(m);
}

/* rim generators + three great circles per cap */
function lineGeometry() {
  const pos = [], w = [];
  const seg = (p, q, wa, wb) => { pos.push(...p, ...q); w.push(wa, wb); };
  for (let i = 1; i < 10; i++) {              /* rim generators */
    const th = Math.PI * i / 10;
    for (let j = 0; j < 22; j++) {
      const ph = 2 * Math.PI * j / 22;
      const p = [R * Math.sin(th) * Math.cos(ph),
                 R * Math.sin(th) * Math.sin(ph), R * Math.cos(th)];
      seg(p, p, -H / 2, H / 2);
    }
  }
  const N = 128;
  for (const wc of [-H / 2, H / 2]) {         /* great circles */
    for (const ax of [0, 1, 2]) {
      for (let k = 0; k < N; k++) {
        const a = 2 * Math.PI * k / N, b = 2 * Math.PI * (k + 1) / N;
        const pt = (t) => {
          const u = [R * Math.cos(t), R * Math.sin(t)];
          return ax === 0 ? [0, u[0], u[1]]
               : ax === 1 ? [u[0], 0, u[1]] : [u[0], u[1], 0];
        };
        seg(pt(a), pt(b), wc, wc);
      }
    }
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(pos, 3));
  g.setAttribute("aW", new Float32BufferAttribute(w, 1));
  return g;
}
const lines = new LineSegments(lineGeometry(), mat(lineVert, lineFrag, {
  uOpacity: ghostOp, uGain: { value: 0.16 },
}, {
  transparent: true, depthWrite: false, blending: AdditiveBlending,
}));
lines.renderOrder = 3;
lines.frustumCulled = false;
scene.add(lines);

/* dust: sparkles inside the two flat ball-faces and on the rim */
function dustGeometry(n) {
  const pos = [], w = [], seed = [];
  for (let i = 0; i < n; i++) {
    const u = Math.random(), v = Math.random(), s = Math.random();
    const th = Math.acos(2 * u - 1), ph = 2 * Math.PI * v;
    const dir = [Math.sin(th) * Math.cos(ph),
                 Math.sin(th) * Math.sin(ph), Math.cos(th)];
    if (s < 0.7) {                            /* inside a flat ball-face */
      const rr = R * Math.cbrt(Math.random());
      pos.push(dir[0] * rr, dir[1] * rr, dir[2] * rr);
      w.push(Math.random() < 0.5 ? -H / 2 : H / 2);
    } else {                                  /* on the curved rim */
      pos.push(dir[0] * R, dir[1] * R, dir[2] * R);
      w.push(H * (Math.random() - 0.5));
    }
    seed.push(Math.random() * 10);
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(pos, 3));
  g.setAttribute("aW", new Float32BufferAttribute(w, 1));
  g.setAttribute("aSeed", new Float32BufferAttribute(seed, 1));
  return g;
}
const pxScale = { value: renderer.getPixelRatio() * innerHeight / 800 };
const dust = new Points(dustGeometry(520), mat(dustVert, dustFrag, {
  uOpacity: ghostOp, uPxScale: pxScale,
}, {
  transparent: true, depthWrite: false, blending: AdditiveBlending,
}));
dust.renderOrder = 3;
dust.frustumCulled = false;
scene.add(dust);

/* the slice solid: lateral surface of revolution + two flat caps */
const sliceOp = { value: 0 }, sliceT = { value: 0 };
const sliceOpts = { transparent: true, side: DoubleSide };
const lateral = new Mesh(
  new PlaneGeometry(1, 1, 160, 96),
  mat(sliceVert, sliceFrag, { uT: sliceT, uSliceOp: sliceOp }, sliceOpts));
lateral.renderOrder = 1;
lateral.frustumCulled = false;
scene.add(lateral);
for (const end of [0, 1]) {
  const cap = new Mesh(
    new PlaneGeometry(1, 1, 24, 96),
    mat(capVert, sliceFrag, {
      uT: sliceT, uSliceOp: sliceOp, uEnd: { value: end },
    }, sliceOpts));
  cap.renderOrder = 1;
  cap.frustumCulled = false;
  scene.add(cap);
}

/* ======================= choreography ======================= */
const TAU = Math.PI * 2, LOOP = 40;
const easeC = (x) => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeS = (x) => -(Math.cos(Math.PI * x) - 1) / 2;
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const env = (x) => Math.min(clamp01(x / 0.08), clamp01((1 - x) / 0.08));
const tMax = (a) => R * Math.abs(Math.sin(a)) + (H / 2) * Math.abs(Math.cos(a));

const P1 = 0.28, P2 = 0.36, P3 = 0.68, P4 = 0.76, P5 = 0.88;
function pose(p, tau) {
  let axw = 0, azw = 0, t = 0, op = 0;
  if (p < P1) {                               /* double-rotation spin */
    axw = TAU * easeS(p / P1);
  } else if (p < P2) {                        /* tilt upright */
    azw = (Math.PI / 2) * easeC((p - P1) / (P2 - P1));
  } else if (p < P3) {                        /* scan: shrinking coins */
    azw = Math.PI / 2;
    const x = (p - P2) / (P3 - P2);
    t = (2 * easeS(x) - 1) * 0.999 * tMax(azw);
    op = env(x);
  } else if (p < P4) {                        /* tilt on through to flat */
    azw = Math.PI / 2 + (Math.PI / 2) * easeC((p - P3) / (P4 - P3));
  } else if (p < P5) {                        /* scan: balls pop in/out */
    azw = Math.PI;
    const x = (p - P4) / (P5 - P4);
    t = (2 * easeS(x) - 1) * 0.999 * tMax(azw);
    op = env(x);
  } else {                                    /* unwind to identity */
    azw = Math.PI + Math.PI * easeC((p - P5) / (1 - P5));
  }
  const dim = clamp01((p - P1) / (P2 - P1)) * (1 - clamp01((p - P5) / 0.08));
  return { axw, ayz: tau * 0.11, azw, t, op, ghost: 1 - 0.72 * dim };
}

/* ========================= interaction ========================= */
let az = 0.85, el = 0.3, dist = 5.3;
let tAz = az, tEl = el, tDist = dist, dragging = false;
addEventListener("pointerdown", (e) => {
  dragging = true; renderer.domElement.setPointerCapture(e.pointerId);
});
addEventListener("pointerup", () => { dragging = false; });
addEventListener("pointermove", (e) => {
  if (!dragging) return;
  tAz -= e.movementX * 0.005;
  tEl = Math.max(-1.25, Math.min(1.25, tEl + e.movementY * 0.005));
});
addEventListener("wheel", (e) => {
  tDist = Math.max(3.4, Math.min(8, tDist * Math.exp(e.deltaY * 0.0009)));
}, { passive: true });
addEventListener("resize", () => {
  renderer.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  pxScale.value = renderer.getPixelRatio() * innerHeight / 800;
});

/* ============================ loop ============================ */
const params = new URLSearchParams(location.search);
let frozen = params.has("static") ? parseFloat(params.get("static")) : null;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const clock = new Clock();
let tau = 0;
window.__seek = (s) => { tau = s; };          /* deterministic capture hooks */
window.__freeze = (s) => { frozen = s; };

function frame() {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (frozen !== null) tau = frozen;
  else if (reduced) tau = LOOP * (P2 + 0.45 * (P3 - P2));  /* a rich still */
  else tau += dt;

  const k = pose((tau % LOOP) / LOOP, tau);
  shared.uAxw.value = k.axw;
  shared.uAyz.value = k.ayz;
  shared.uAzw.value = k.azw;
  shared.uTime.value = tau;
  shared.uWMax.value = H / 2 + R * Math.min(1,
    Math.hypot(Math.sin(k.axw), Math.sin(k.azw)));
  ghostOp.value = k.ghost;
  sliceT.value = k.t;
  sliceOp.value = k.op;

  if (!dragging && frozen === null && !reduced) tAz += dt * 0.03;
  az += (tAz - az) * 0.06;
  el += (tEl - el) * 0.06;
  dist += (tDist - dist) * 0.08;
  const fit = Math.min(2.4, Math.max(1, 1.15 / camera.aspect));
  const d = dist * fit;
  camera.position.set(
    d * Math.cos(el) * Math.sin(az),
    d * Math.sin(el),
    d * Math.cos(el) * Math.cos(az));
  camera.lookAt(0, 0, 0);

  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
frame();
</script>
</body>
</html>
"""


def main():
    with open(THREE, encoding="utf-8") as f:
        three_src = f.read()
    html = PAGE.replace("@@THREE@@", three_src)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
