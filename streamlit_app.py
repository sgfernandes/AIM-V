"""Root Streamlit entrypoint for local runs and hosted deployments."""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    # Remove cached ui.app so Streamlit re-executes the UI code on
    # every script rerun instead of silently skipping the import.
    for _mod_name in list(sys.modules):
        if _mod_name == "ui.app" or _mod_name.startswith("ui.app."):
            del sys.modules[_mod_name]

    from ui.app import *  # noqa: F401,F403,E402
except Exception as exc:
    import traceback

    import streamlit as st

    st.set_page_config(page_title="AIM-V — Error", page_icon="⚠️")
    st.error(f"Application failed to load: {exc}")
    st.code(traceback.format_exc())
    st.info(f"Python {sys.version}")
    st.stop()
