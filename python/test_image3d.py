"""
test_image3d.py  -  prove ANY photo becomes a tiltable, sliceable 3D relief,
using the zero-dependency luminance depth (no torch, no monitor).

    python test_image3d.py
Also writes a reusable sample photo to ../assets/images/sample.png
"""

import os
import numpy as np
import cv2

import object_lab
from object_lab import Scene3D
import image3d

HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "..", "assets", "images")
SAMPLE = os.path.join(ASSETS, "sample.png")
OUT = os.path.join(HERE, "_render_out")


def make_sample():
    os.makedirs(ASSETS, exist_ok=True)
    img = np.zeros((240, 320, 3), np.uint8)
    for y in range(240):                         # sky gradient
        img[y, :] = (200 - y // 2, 120 + y // 3, 60 + y // 4)
    cv2.circle(img, (230, 70), 40, (60, 230, 255), -1)   # bright "sun" -> rises
    cv2.rectangle(img, (30, 150), (120, 220), (40, 160, 90), -1)
    cv2.putText(img, "3D", (140, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)
    cv2.imwrite(SAMPLE, img)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    cv2.imwrite(os.path.join(OUT, name), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    return cond


def main():
    ok = True
    make_sample()
    ok &= check("sample image written", os.path.exists(SAMPLE))

    # force the no-dependency path so this test never needs torch/network
    object_lab.IMAGE_DEPTH_PROVIDER = "luminance"

    mesh, tex = image3d.build_relief(SAMPLE, provider="luminance", max_size=160)
    zmin, zmax = mesh.bounds[4], mesh.bounds[5]
    ok &= check("relief has many points", mesh.n_points > 1000)
    ok &= check("relief has real height variation", (zmax - zmin) > 0.05)

    scene = Scene3D(SAMPLE)                       # load a photo AS a model
    ok &= check("Scene3D loaded the photo", scene.title.startswith("IMG:"))
    base = scene.render()
    scene.slice(0.2, 0.5, 0.8, 0.5)
    sliced = scene.render()
    diff = float(np.mean(np.abs(base.astype(int) - sliced.astype(int))))
    ok &= check("relief renders", base.shape[2] == 3)
    ok &= check("relief can be sliced", diff > 1.0)

    save(base, "image3d_1_base.png")
    save(sliced, "image3d_2_sliced.png")
    print(f"\nsample photo: {os.path.normpath(SAMPLE)}")
    print("RESULT:", "IMAGE->3D OK" if ok else "SOMETHING WRONG")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
