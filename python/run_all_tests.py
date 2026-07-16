"""
run_all_tests.py  -  run every headless test in one go.

    python run_all_tests.py

Needs NO Arduino and NO monitor. If they all say OK, the whole project is
wired correctly on this machine.
"""

import subprocess
import sys
import os

TESTS = [
    "smoke_test.py",        # imports + all 12 LED modes (mock)
    "test_gestures.py",     # gesture engine verbs
    "test_object_lab.py",   # 3D rotate / explode / slice
    "test_studio.py",       # live-3D integration logic
    "test_game.py",         # Slice Surgeon scoring
    "test_image3d.py",      # photo -> 3D relief
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    results = []
    for t in TESTS:
        print("\n" + "=" * 60 + f"\n RUNNING {t}\n" + "=" * 60)
        code = subprocess.call([sys.executable, os.path.join(here, t)])
        results.append((t, code == 0))

    print("\n" + "#" * 60 + "\n SUMMARY\n" + "#" * 60)
    for t, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {t}")
    allok = all(ok for _, ok in results)
    print("\n", "ALL TESTS PASSED" if allok else "SOME TESTS FAILED")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
