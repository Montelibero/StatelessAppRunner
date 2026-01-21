import sys
from pathlib import Path

# Add app directory to path so tests can import from app modules
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))
