import yaml
from pathlib import Path

# 📁 Ruta real al YAML
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = BASE_DIR / "core" / "classes.yaml"


def load_schedule():
    if not SCHEDULE_FILE.exists():
        return {}
    with open(SCHEDULE_FILE, "r") as f:
        return yaml.safe_load(f) or {}
