import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "PAZ-Parser"))

from bdo_preview import BUNDLED_HANDLERS_DIR, use_handlers_dir  # noqa: E402

# bench.stages imports `_common` from the handlers folder.
use_handlers_dir(BUNDLED_HANDLERS_DIR)

from bench.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
