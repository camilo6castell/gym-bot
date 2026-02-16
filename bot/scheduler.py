import os
import pytz
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


# 🔄 Cargar variables de entorno
load_dotenv()

# 📁 Ruta real al YAML
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = BASE_DIR / "config" / "classes.yaml"


DAYS_MAP = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}


def load_config():
    if not SCHEDULE_FILE.exists():
        return {}
    with open(SCHEDULE_FILE, "r") as f:
        return yaml.safe_load(f) or {}


def should_run_now():
    config = load_config()

    if not config or "dias" not in config:
        return []

    # 🕒 Zona horaria segura
    timezone_str = config.get("timezone", "UTC")
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)

    # 🔥 Siempre 2 días atrás
    target_weekday = (now.weekday() - 2) % 7

    # 🔧 Leer variable booleana del .env
    additional_minute = os.getenv(
        "ADDITIONAL_MINUTE_FOR_EXECUTION",
        "false"
    ).lower() == "true"

    clases_a_ejecutar = []

    for day_name, clases in config.get("dias", {}).items():

        if DAYS_MAP.get(day_name.lower()) != target_weekday:
            continue

        if not clases:
            continue

        for clase in clases:
            try:
                start_hour = clase["hora"].split(" - ")[0]
                hour, minute = map(int, start_hour.split(":"))
            except Exception:
                # Si el formato de hora está mal, ignoramos esa clase
                continue

            activation_hour = hour
            activation_minute = minute

            # ➕ Agregar minuto adicional si está activado
            if additional_minute:
                activation_minute += 1
                if activation_minute >= 60:
                    activation_hour += 1
                    activation_minute -= 60

                if activation_hour >= 24:
                    activation_hour = 0

            # 🎯 Comparación exacta
            if now.hour == activation_hour and now.minute == activation_minute:
                clases_a_ejecutar.append({
                    **clase,
                    "dia": day_name
                })

    return clases_a_ejecutar
