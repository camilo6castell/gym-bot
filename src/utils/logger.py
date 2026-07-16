"""
Configuración de logging de gym-bot.

Se instancian dos sinks sobre el mismo `logger` de Loguru:

  - **stdout**: formato compacto y coloreado, para ejecución interactiva.
  - **archivo** (`logs/`): texto plano (sin códigos de color), pensado para
    reemplazar `journalctl` — `tail -f logs/<archivo>` muestra las líneas
    en tiempo real a medida que se generan, sin la marca de tiempo extra
    que antepone journald. El archivo tiene un límite de líneas
    configurable (`LOG_MAX_LINES` en `.env`): al superarlo, se recortan
    las líneas más antiguas para dar espacio a las nuevas (FIFO).

Nota de diseño: a diferencia del resto de clases de la aplicación (que
reciben su configuración por constructor), este módulo se configura a sí
mismo al importarse — igual que antes de este cambio. Es infraestructura
transversal (equivalente a `logging.basicConfig`), no un componente del
dominio, así que lee `.env` directamente en lugar de depender de
`Settings` (que aún no existe en el momento en que este módulo se importa).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from loguru import logger

if TYPE_CHECKING:
    from loguru import Message

load_dotenv()

# ─── Configuración del sink de archivo (vía .env) ───────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
_LOG_FILENAME = os.getenv("LOG_FILENAME", "logger.txt")
_LOG_FILE = _LOG_DIR / _LOG_FILENAME
_LOG_MAX_LINES = int(os.getenv("LOG_MAX_LINES", "5000"))

# _FILE_FORMAT = "{time:MM/DD HH:mm:ss} | {level: <8} | {message}"
_FILE_FORMAT = "{time:MM/DD HH:mm:ss} | {message}"

# Crea logs/ y el archivo si no existen (carga el existente si ya está ahí).
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE.touch(exist_ok=True)


def _file_sink(message: Message) -> None:
    """
    Sink de archivo con rotación por número de líneas.

    Añade la línea ya formateada por Loguru y, si el archivo supera
    `LOG_MAX_LINES`, lo recorta dejando solo las líneas más recientes.
    """
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(message))

    with open(_LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) > _LOG_MAX_LINES:
        with open(_LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines[-_LOG_MAX_LINES:])


# ─── Logger config ───────────────────────────────────────────────────────────
logger.remove()

# stdout — compacto y coloreado, para ejecución interactiva
logger.add(
    sys.stdout,
    level="INFO",
    format=("<green>{time:MM/DD HH:mm:ss}</green> | {message}"),
)

# archivo — texto plano, con nivel + timestamp, rotación por líneas
logger.add(
    _file_sink,
    level="INFO",
    format=_FILE_FORMAT,
)

# Ejemplo de línea en logs/logger.txt:
# 07/09 20:41:31 | INFO     | 🥁 → Iniciando iteraciones de clases.
#
# Ver en tiempo real (reemplaza a journalctl -f):
#   tail -f logs/logger.txt
