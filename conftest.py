"""Make the repository root importable so `tests/` can import `sentry`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
