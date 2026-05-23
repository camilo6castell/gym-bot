---
name: Gym Bot Engineering Rules
description: Reglas de ingeniería para el proyecto de automatización gym-bot
---

# Python y tipado

- Implementar tipado estático profesional usando type hints modernos.
- Preferir:
  - pathlib sobre os.path
  - dataclasses o pydantic cuando tenga sentido
  - enums para estados conocidos
- Evitar variables globales mutables.
- Preferir composición sobre herencia innecesaria.
- Mantener funciones pequeñas y enfocadas en una sola responsabilidad.

# Playwright y automatización

- Preferir waits explícitos sobre sleeps fijos.
- Minimizar el uso de time.sleep().
- Utilizar mecanismos robustos de espera:
  - wait_for_selector
  - locator assertions
  - wait_for_load_state
- Evitar selectores frágiles.
- Preferir:
  - data-testid
  - roles
  - labels
  - texto estable
    sobre selectores CSS complejos.
- Manejar correctamente:
  - timeouts
  - retries
  - errores de navegación
  - elementos inexistentes
- Mantener la automatización resiliente a cambios menores del DOM.

# Async y concurrencia

- Mantener consistencia entre código sync y async.
- No mezclar APIs sync y async de Playwright incorrectamente.
- Evitar bloquear el event loop.
- Usar async/await correctamente y propagar async de forma consistente.

# Logging y debugging

- Implementar logs útiles y concisos.
- Evitar prints innecesarios.
- Incluir suficiente contexto en errores para facilitar debugging.
- Mantener mensajes de error accionables.

# Refactorización

- Preservar comportamiento existente durante refactors.
- Priorizar legibilidad y mantenibilidad.
- Evitar sobreingeniería.
- Hacer refactors graduales y verificables.

# Calidad de código

- Preferir soluciones simples y mantenibles.
- Evitar introducir dependencias innecesarias.
- Mantener imports organizados y limpios.
- Escribir código preparado para producción.
- Si falta contexto del repositorio, indicarlo explícitamente antes de asumir comportamiento.
