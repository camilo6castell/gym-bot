import yaml
import os
from typing import Any
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SCHEDULE_FILE = BASE_DIR / "core" / "classes.yaml"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def load_schedule() -> dict[str, Any]:
    if not SCHEDULE_FILE.exists():
        raise FileNotFoundError(
            f"❌ Archivo de schedule no encontrado: {SCHEDULE_FILE}"
        )

    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        schedule = yaml.safe_load(f)

    if not schedule:
        raise ValueError("❌ El archivo de schedule está vacío o mal formado.")

    missing = [field for field in ("timezone", "days") if field not in schedule]
    if missing:
        raise ValueError(
            f"❌ Configuración de schedule incompleta. "
            f"Campos requeridos faltantes: {', '.join(missing)}"
        )

    if not isinstance(schedule["days"], dict) or not schedule["days"]:
        raise ValueError("❌ 'days' debe ser un diccionario con al menos un día.")

    return schedule
