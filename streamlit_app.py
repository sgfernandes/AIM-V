"""
Root Streamlit entrypoint for hosted deployments.

This file intentionally delegates to ui/app.py by executing it directly,
avoiding the Python module-cache problem where `from ui.app import *`
only runs the UI code once and produces a blank page on Streamlit reruns.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_app_file = os.path.join(ROOT, "ui", "app.py")
with open(_app_file, encoding="utf-8") as _f:
    _source = _f.read()

exec(compile(_source, _app_file, "exec"), {
    "__file__": _app_file,
    "__name__": "__main__",
    "__builtins__": __builtins__,
})
