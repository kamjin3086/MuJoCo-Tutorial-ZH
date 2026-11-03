"""Run each example headlessly for a few steps to verify no crashes."""

import importlib.util
import sys
import os
from pathlib import Path

# Force offscreen rendering. On Windows MuJoCo only accepts "glfw";
# "egl"/"osmesa" raise RuntimeError at import there.
os.environ.setdefault("MUJOCO_GL", "glfw" if sys.platform == "win32" else "egl")

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

# Examples that require special handling
SKIP = {"mjx_parallel.py"}  # Requires JAX + GPU


def test_example(path):
    """Import and run an example's main() with a patched viewer."""
    import mujoco
    import mujoco.viewer
    import unittest.mock as mock

    # Mock the viewer to run headlessly (just step N times)
    class FakeViewer:
        def __init__(self, *a, **kw):
            self._steps = 0
            self._max_steps = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def is_running(self):
            self._steps += 1
            return self._steps < self._max_steps

        def sync(self):
            pass

    with mock.patch("mujoco.viewer.launch_passive", FakeViewer):
        spec = importlib.util.spec_from_file_location("example", path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            if hasattr(mod, "main"):
                mod.main()
            return True
        except Exception as e:
            print(f"  ERROR: {e}")
            return False


def main():
    examples = sorted(EXAMPLES_DIR.glob("*.py"))
    passed, failed = 0, 0

    for path in examples:
        if path.name in SKIP:
            print(f"  SKIP: {path.name}")
            continue

        print(f"  Testing {path.name}...", end=" ")
        if test_example(path):
            print("OK")
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {len(SKIP)} skipped")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
