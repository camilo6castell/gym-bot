"""
Jerarquía de excepciones de dominio de gym-bot.

Usar excepciones específicas (en lugar de `RuntimeError`/`ValueError` genéricos)
permite que las capas superiores (`Recovery`, `main.py`) distingan qué falló
y decidan cómo reaccionar, además de dejar rastros de error más legibles.
"""

from __future__ import annotations


class GymBotError(Exception):
    """Excepción base para todos los errores de dominio de la aplicación."""


class CaptchaDetectedError(GymBotError):
    """Se lanza cuando se detecta un CAPTCHA activo que requiere intervención humana."""


class BrowserLaunchError(GymBotError):
    """Se lanza cuando el navegador no puede iniciarse por falta de configuración o entorno."""


class ElementNotFoundError(GymBotError):
    """Se lanza cuando un elemento obligatorio de la página no aparece a tiempo."""


class RedirectTimeoutError(GymBotError):
    """Se lanza cuando la página no redirige a la URL esperada dentro del timeout."""


class MembershipNotFoundError(GymBotError):
    """Se lanza cuando no hay botones de membresía/tiquetera disponibles o habilitados."""


class ReservationVerificationError(GymBotError):
    """Se lanza cuando no se puede confirmar que una clase quedó reservada."""


class ScheduleConfigError(GymBotError):
    """Se lanza cuando la configuración de horario (schedule.yaml) es inválida o incompleta."""


class RecoveryExhaustedError(GymBotError):
    """Se lanza cuando una acción agota sus reintentos automáticos sin recuperarse."""


class RecoveryAbortedError(GymBotError):
    """Se lanza cuando el usuario aborta el flujo durante una recuperación asistida."""
