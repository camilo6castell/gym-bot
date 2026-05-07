from utils.logger import logger


def should_add_a_minute_for_x(
    ADDITIONAL_MINUTE_FOR_EXECUTION: bool, hour: int, minute: int
) -> tuple[int, int]:
    if ADDITIONAL_MINUTE_FOR_EXECUTION:
        logger.warning("⚠️ → ¡Agregando minuto extra! ⚠️")
        minute += 1
        if minute >= 60:
            hour += 1
            minute -= 60

        if hour >= 24:
            hour = 0
    return hour, minute
