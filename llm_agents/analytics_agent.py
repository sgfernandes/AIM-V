"""Compatibility wrapper for the analytics agent package."""

from pathlib import Path
import sys

# Support running directly from this monorepo without requiring a prior
# editable install of analytics-agent/.
ANALYTICS_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "analytics-agent"
if str(ANALYTICS_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYTICS_PACKAGE_ROOT))

from analytics_agent.analytics_agent import AnalyticsAgent  # noqa: E402,F401

__all__ = ["AnalyticsAgent"]
