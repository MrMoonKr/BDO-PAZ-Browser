import multiprocessing
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "PAZ-Parser"))

from bdo_app import main  # noqa: E402

if __name__ == "__main__":
    # The exe's map build workers (world_map_build.py) start the exe again;
    # this runs their job and exits instead of opening a second app.
    multiprocessing.freeze_support()
    main()
