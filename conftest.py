"""Root conftest — make platform_core, governance, and each agent importable in tests."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for p in (_ROOT / "platform_core", _ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
