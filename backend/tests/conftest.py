import os
import sys
from pathlib import Path

os.environ["DATA_MODE"] = "seed"  # tests never touch the network
sys.path.insert(0, str(Path(__file__).parents[1]))
