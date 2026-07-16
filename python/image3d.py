"""
image3d.py  -  turn ANY photo into a tiltable, sliceable 3D relief.

How: estimate a "height" for every pixel, then lift the image into a 3D surface
(a heightmap) with the original photo painted on top. Then you can rotate, zoom
and slice it like any other model in the 3D studio.

Two depth engines:
  * "luminance" (default)  - brighter pixels rise higher. ZERO extra installs,
                             runs on any laptop. Good enough for a fun relief.
  * "midas"     (optional) - real AI monocular depth (Intel MiDaS). Much more
                             realistic, but needs:  pip install torch timm
                             and downloads a model on first use.
  * "auto"                 - use MiDaS if it's installed, else luminance.

Everything renders off-screen, so it's testable with no monitor.
"""

import os
import numpy as np
import cv2
import pyvista as pv

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
_midas = None            # cached (model, transform, device) once loaded


def is_image(path) -> bool:
    return isinstance(path, str) and path.lower().endswith(IMAGE_EXTS)


# ------------------------------------------------------------------ depth
def _norm(a):
    a = a.astype(np.float32)
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


def _luminance_depth(bgr):
    """Cheap pseudo-depth: blurred brightness. No dependencies."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray = cv2.GaussianBlur(gray, (0, 0), 2.0)
    return _norm(gray)


def _midas_depth(bgr):
    """Real AI depth via MiDaS. Returns None if torch/timm not available."""
    global _midas
    try:
        import torch
        if _midas is None:
            model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            tfm = torch.hub.load("intel-isl/MiDaS", "transforms").small_transform
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            model.to(dev).eval()
            _midas = (model, tfm, dev)
        model, tfm, dev = _midas
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        with torch.no_grad():
            batch = tfm(rgb).to(dev)
            pred = model(batch)
            pred = torch.nn.functional.interpolate(
                pred.unsqueeze(1), size=rgb.shape[:2],
                mode="bicubic", align_corners=False).squeeze()
        return _norm(pred.cpu().numpy())
    except Exception as e:
        print(f"[image3d] MiDaS unavailable ({e}); using luminance depth.")
        return None


def get_depth(bgr, provider="auto"):
    if provider in ("auto", "midas"):
        d = _midas_depth(bgr)
        if d is not None:
            return d
        if provider == "midas":
            raise RuntimeError("MiDaS requested but not available. pip install torch timm")
    return _luminance_depth(bgr)


# ------------------------------------------------------------------ relief
def build_relief(path, provider="auto", max_size=200, relief=0.5):
    """Return (pyvista mesh with texture coords, pyvista Texture)."""
    bgr = cv2.imread(path)
    if bgr is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    h, w = bgr.shape[:2]
    scale = max_size / max(h, w)
    if scale < 1.0:
        bgr = cv2.resize(bgr, (max(1, int(w * scale)), max(1, int(h * scale))))
    H, W = bgr.shape[:2]

    depth = get_depth(bgr, provider)

    xs = np.linspace(-1.0, 1.0, W)
    ys = np.linspace(H / W, -H / W, H)          # flip so image isn't upside-down
    X, Y = np.meshgrid(xs, ys)
    Z = (depth - 0.5) * relief

    grid = pv.StructuredGrid(X, Y, Z)
    grid.texture_map_to_plane(inplace=True)
    tex = pv.Texture(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).copy())
    return grid, tex


# quick manual check:  python image3d.py path/to/image.png
if __name__ == "__main__":
    import sys
    pv.OFF_SCREEN = True
    p = sys.argv[1] if len(sys.argv) > 1 else None
    if not p:
        print("usage: python image3d.py <image>")
    else:
        m, t = build_relief(p, provider="auto")
        print("relief points:", m.n_points, "bounds:", [round(b, 2) for b in m.bounds])
