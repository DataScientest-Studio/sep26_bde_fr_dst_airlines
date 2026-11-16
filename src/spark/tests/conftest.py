import sys
from pathlib import Path

# Insert le folder spark/ (../..) dans le path afin que les sources dans notebooks soient accessible
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))