from typing import Optional, Dict, Any, List
import yaml
from datetime import datetime, timedelta
import pytz


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


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_activation_schedule(config) -> List[Dict[str, Any]]:
    """
    Construye lista completa de activaciones
    respetando orden del YAML.
    """

    tz = pytz.timezone(config["timezone"])
    now = datetime.now(tz)

    activaciones = []

    for day_name, clases in config["dias"].items():
        target_weekday = DAYS_MAP[day_name.lower()]

        # Agrupar por hora manteniendo orden YAML
        clases_por_hora = {}

        for clase in clases:
            start_hour = clase["hora"].split(" - ")[0]
            if start_hour not in clases_por_hora:
                clases_por_hora[start_hour] = []
            clases_por_hora[start_hour].append(clase)

        for hora_str, lista_clases in clases_por_hora.items():
            hour, minute = map(int, hora_str.split(":"))

            days_ahead = (target_weekday - now.weekday()) % 7
            target_date = now.date() + timedelta(days=days_ahead)

            class_dt = tz.localize(
                datetime(
                    target_date.year,
                    target_date.month,
                    target_date.day,
                    hour,
                    minute,
                )
            )

            # 🔥 CAMBIO CLAVE: +2 días en vez de -2
            base_activation = class_dt + timedelta(days=2, minutes=1)

            for index, clase in enumerate(lista_clases):
                activation_dt = base_activation + timedelta(minutes=index)

                activaciones.append({
                    "activation": activation_dt,
                    "clase": {
                        **clase,
                        "dia": day_name
                    },
                })

    return activaciones


def should_run_now(
    config_path="config/classes.yaml",
    force=False
) -> Optional[Dict[str, Any]]:

    config = load_config(config_path)
    tz = pytz.timezone(config["timezone"])
    now = datetime.now(tz)

    activaciones = build_activation_schedule(config)
    activaciones.sort(key=lambda x: x["activation"])

    if force:
        for item in activaciones:
            if item["activation"] >= now:
                return item["clase"]
        return None

    for item in activaciones:
        activation_dt = item["activation"]

        if 0 <= (now - activation_dt).total_seconds() < 60:
            return item["clase"]

    return None