"""
test_object_lab.py  -  render every built-in model in normal / exploded /
sliced states off-screen and save PNGs, proving the 3D dissection works with
no monitor. Also checks that exploding/slicing actually change the image.

    python test_object_lab.py
Outputs PNGs into ./_render_out/
"""

import os
import numpy as np
from object_lab import Scene3D, BUILTINS

OUT = os.path.join(os.path.dirname(__file__), "_render_out")


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    try:
        import cv2
        cv2.imwrite(os.path.join(OUT, name), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    except Exception:
        from PIL import Image
        Image.fromarray(img).save(os.path.join(OUT, name))


def main():
    ok = True
    for name in BUILTINS:
        s = Scene3D(name)

        base = s.render()

        # rotation is a FUNCTIONAL check (a plain sphere looks the same spun)
        az0 = s.azim
        s.rotate(0.3, 0.1)
        rotated_ok = s.azim != az0

        s.set_explode(0.8); exploded = s.render()

        s.set_explode(0.0)
        s.slice(0.2, 0.5, 0.8, 0.5); sliced = s.render()

        save(base, f"{name}_1_base.png")
        save(exploded, f"{name}_2_exploded.png")
        save(sliced, f"{name}_3_sliced.png")

        diff_e = float(np.mean(np.abs(base.astype(int) - exploded.astype(int))))
        diff_s = float(np.mean(np.abs(base.astype(int) - sliced.astype(int))))
        print(f"[{name}] shape={base.shape}  rotate_applied={rotated_ok}  "
              f"explode_diff={diff_e:.1f}  slice_diff={diff_s:.1f}")
        ok &= base.shape[2] == 3
        ok &= rotated_ok            # rotate must change the camera angle
        ok &= diff_e > 1.0          # exploding must visibly change the picture
        ok &= diff_s > 1.0          # slicing must visibly cut the model

    print(f"\nPNGs saved in: {OUT}")
    print("RESULT:", "3D LAB OK" if ok else "SOMETHING WRONG")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
