"""Root Streamlit entrypoint for local runs and hosted deployments."""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.app import *  # noqa: F401,F403,E402
