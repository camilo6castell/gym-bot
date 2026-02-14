import pytz
import yaml
from datetime import datetime
from pathlib import Path


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
    with open(SCHEDULE_FILE, "r") as f:
        return yaml.safe_load(f)


def should_run_now():
    config = load_config()

    tz = pytz.timezone(config["timezone"])
    now = datetime.now(tz)

    # 🔥 Siempre 2 días atrás
    target_weekday = (now.weekday() - 2) % 7

    clases_a_ejecutar = []

    for day_name, clases in config["dias"].items():
        if DAYS_MAP[day_name.lower()] != target_weekday:
            continue

        for clase in clases:
            start_hour = clase["hora"].split(" - ")[0]
            hour, minute = map(int, start_hour.split(":"))

            # activación = hora clase + 1 minuto
            activation_hour = hour

            # En el caso de que debe ser en hora exacta
            activation_minute = minute

            # En el caso que deba ser 1 minuto después
            # activation_minute = minute + 1

            # if activation_minute >= 60:
            #     activation_hour += 1
            #     activation_minute -= 60

            if now.hour == activation_hour and now.minute == activation_minute:
                clases_a_ejecutar.append({
                    **clase,
                    "dia": day_name
                })

    return clases_a_ejecutar
