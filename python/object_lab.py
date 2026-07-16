"""
object_lab.py  -  the 3D dissection engine.

A Scene3D holds a model made of PARTS. With your hands you can:
    rotate   (grab + drag)          -> scene.rotate(dx, dy)
    zoom     (pinch / two-hand)     -> scene.zoom(factor)
    explode  (two hands apart)      -> scene.set_explode(0..1)   parts fly apart
    slice    (scalpel gesture)      -> scene.slice(nx1,ny1, nx2,ny2)  cut it open
    reset                           -> scene.reset()

It renders OFF-SCREEN to a normal image (numpy array), so it drops straight
into the OpenCV window next to the camera - and it can be tested with no
monitor at all.

Built-in science models (no download needed):  "cell", "atom", "earth".
You can also load your own file:  Scene3D(model="path/to/thing.obj").
Supported files: .obj .stl .ply .vtk   (glb/gltf: see README notes).
"""

import os
import math
import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True

# depth engine for photo -> 3D reliefs: "auto" | "luminance" | "midas"
IMAGE_DEPTH_PROVIDER = "auto"


# ---------------------------------------------------------------- a model part
class Part:
    def __init__(self, mesh, color, name, direction, texture=None):
        self.base = mesh                    # untouched original
        self.color = color
        self.name = name
        self.direction = np.array(direction, dtype=float)  # explode direction
        self.texture = texture              # pyvista Texture for photo reliefs


# ---------------------------------------------------------------- model makers
def _spread_dirs(n):
    """n roughly-even directions on a sphere (for exploding parts outward)."""
    dirs = []
    for i in range(n):
        y = 1 - (i / max(n - 1, 1)) * 2
        r = math.sqrt(max(0.0, 1 - y * y))
        theta = i * 2.399963              # golden angle
        dirs.append((r * math.cos(theta), y, r * math.sin(theta)))
    return dirs


def make_cell():
    """A biological cell: membrane, cytoplasm, nucleus + a few organelles."""
    parts = [
        Part(pv.Sphere(radius=1.0), "#88ccffaa", "membrane", (0, 1, 0)),
        Part(pv.Sphere(radius=0.8), "#aef7c0", "cytoplasm", (1, 0.3, 0)),
        Part(pv.Sphere(radius=0.35, center=(0.2, 0.1, 0)), "#ff8f6b", "nucleus", (-1, 0.2, 0.3)),
        Part(pv.Sphere(radius=0.12, center=(-0.4, -0.3, 0.2)), "#ffd166", "mitochondrion", (0.2, -1, 0.4)),
        Part(pv.Sphere(radius=0.1, center=(0.3, -0.4, -0.2)), "#c39bd3", "ribosome", (0.5, -0.6, -1)),
    ]
    return parts, "Animal Cell"


def make_atom():
    """A simple atom: nucleus + electron shells (rings)."""
    parts = [Part(pv.Sphere(radius=0.35), "#ff6b6b", "nucleus", (0, 1, 0))]
    dirs = _spread_dirs(3)
    for i, r in enumerate((0.7, 1.0, 1.35)):
        ring = pv.ParametricTorus(ringradius=r, crosssectionradius=0.03)
        ring.rotate_x(90 * (i % 2), inplace=True)
        ring.rotate_y(35 * i, inplace=True)
        parts.append(Part(ring, "#4dd2ff", f"shell{i+1}", dirs[i]))
    return parts, "Atom"


def make_earth():
    """Layered planet: inner core, outer core, mantle, crust."""
    layers = [
        (0.35, "#fff275", "inner core"),
        (0.6,  "#ff9f45", "outer core"),
        (0.85, "#d35400", "mantle"),
        (1.0,  "#2e86de", "crust"),
    ]
    dirs = _spread_dirs(len(layers))
    parts = [Part(pv.Sphere(radius=r), c, n, dirs[i])
             for i, (r, c, n) in enumerate(layers)]
    return parts, "Earth Layers"


BUILTINS = {"cell": make_cell, "atom": make_atom, "earth": make_earth}


# ---------------------------------------------------------------- the 3D scene
class Scene3D:
    def __init__(self, model="cell", size=(900, 700)):
        self.size = size
        self.plotter = pv.Plotter(off_screen=True, window_size=list(size),
                                  lighting="none")
        self.plotter.set_background("#0b0f1a", top="#1a2238")
        # 3-point studio lighting so spheres/meshes read as truly 3D
        for pos, intensity in (((1, 1, 1), 0.9), ((-1, 0.5, 0.5), 0.5),
                               ((0, -1, 0.5), 0.35)):
            self.plotter.add_light(pv.Light(position=pos, intensity=intensity,
                                            light_type="scene light"))
        self.parts = []
        self.title = ""
        self.azim = 30.0
        self.elev = 20.0
        self.zoom_f = 1.0
        self.explode_amt = 0.0
        self.clip = None            # (origin, normal) or None
        self._diag = 2.0
        self.load(model)

    # ---- loading ----
    def load(self, model):
        import image3d
        if model in BUILTINS:
            self.parts, self.title = BUILTINS[model]()
        elif image3d.is_image(model):                  # a photo -> 3D relief
            mesh, tex = image3d.build_relief(model, provider=IMAGE_DEPTH_PROVIDER)
            self.parts = [Part(mesh, "#ffffff", "relief", (0, 1, 0), texture=tex)]
            self.title = "IMG:" + os.path.basename(model)
        else:
            mesh = pv.read(model)                      # a real 3D file (.obj/.stl/.ply)
            mesh = mesh.scale(1.0 / max(mesh.length, 1e-6), inplace=False)
            self.parts = [Part(mesh, "#9fd3ff", "model", (0, 1, 0))]
            self.title = os.path.basename(str(model))
        b = _bounds_of(self.parts)
        self._diag = math.dist(b[::2], b[1::2]) or 2.0
        self.reset_view()

    def reset_view(self):
        self.azim, self.elev, self.zoom_f = 30.0, 20.0, 1.0
        self.explode_amt, self.clip = 0.0, None

    # ---- gesture-driven controls ----
    def rotate(self, dx, dy, gain=220.0):
        self.azim += dx * gain
        self.elev = max(-89, min(89, self.elev + dy * gain))

    def zoom(self, factor):
        self.zoom_f = max(0.3, min(4.0, self.zoom_f * factor))

    def set_explode(self, amount):
        self.explode_amt = max(0.0, min(1.0, amount))

    def slice(self, nx1, ny1, nx2, ny2):
        """Cut with a plane defined by the on-screen scalpel stroke direction."""
        dx, dy = (nx2 - nx1), (ny2 - ny1)
        normal = (dy, -dx, 0.0)             # perpendicular to the drawn stroke
        n = math.hypot(*normal[:2]) or 1.0
        self.clip = ((0.0, 0.0, 0.0), (normal[0] / n, normal[1] / n, 0.0))

    def unslice(self):
        self.clip = None

    # ---- render one frame -> RGB image (numpy HxWx3 uint8) ----
    def render(self):
        p = self.plotter
        p.clear()
        step = self._diag * 0.6 * self.explode_amt
        for part in self.parts:
            m = part.base.copy()
            if step > 0:
                m.translate(part.direction * step, inplace=True)
            if self.clip is not None:
                try:
                    m = m.clip(normal=self.clip[1], origin=self.clip[0], invert=False)
                except Exception:
                    pass
            if m.n_points == 0:
                continue
            if part.texture is not None:
                p.add_mesh(m, texture=part.texture, smooth_shading=True,
                           ambient=0.35, diffuse=0.9)
            else:
                p.add_mesh(m, color=_rgb(part.color), opacity=_opacity(part.color),
                           smooth_shading=True, specular=0.6, specular_power=18,
                           ambient=0.25, diffuse=0.9)
        p.camera_position = "iso"
        p.camera.azimuth = self.azim
        p.camera.elevation = self.elev
        p.camera.zoom(self.zoom_f)
        return p.screenshot(return_img=True)


# ---------------------------------------------------------------- helpers
def _bounds_of(parts):
    b = list(parts[0].base.bounds)
    for part in parts[1:]:
        pb = part.base.bounds
        for i in range(0, 6, 2):
            b[i] = min(b[i], pb[i]); b[i + 1] = max(b[i + 1], pb[i + 1])
    return b


def _rgb(hexstr):
    h = hexstr.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _opacity(hexstr):
    h = hexstr.lstrip("#")
    return int(h[6:8], 16) / 255 if len(h) >= 8 else 1.0


# quick manual render:  python object_lab.py
if __name__ == "__main__":
    for name in BUILTINS:
        s = Scene3D(name)
        s.set_explode(0.6)
        img = s.render()
        print(name, "rendered", img.shape)
