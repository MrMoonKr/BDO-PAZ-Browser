from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from _bwp.registration import register_bwp_handlers


register_bwp_handlers()
