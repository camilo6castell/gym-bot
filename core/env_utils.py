import yaml
from typing import Any
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SCHEDULE_FILE = BASE_DIR / "core" / "classes.yaml"
APP_CONFIG_FILE = BASE_DIR / "core" / "app_config.yaml"


def env_bool(name: str) -> bool:
    return name.lower() in ("1", "true", "yes", "on")


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


def load_app_config() -> dict[str, Any]:
    if not APP_CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"❌ Archivo de app config no encontrado: {APP_CONFIG_FILE}"
        )

    with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError("❌ El archivo app_config.yaml está vacío o mal formado.")

    required_sections = [
        "environment",
        "os",
        "selectors",
        "power_autonomous",
        "execution",
    ]

    missing = [section for section in required_sections if section not in config]

    if missing:
        raise ValueError(
            f"❌ Configuración incompleta. " f"Faltan secciones: {', '.join(missing)}"
        )

    return config
