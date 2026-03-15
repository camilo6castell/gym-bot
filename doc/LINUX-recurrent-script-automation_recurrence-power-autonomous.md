# Incidente: El sistema no volvió a suspenderse después de una reserva

## Contexto

El sistema utiliza un script (`power_autonomous.py`) ejecutado mediante un servicio de **systemd** para gestionar automáticamente el ciclo de energía del equipo.

El comportamiento esperado es:

1. El sistema se suspende.
2. El **RTC wakealarm** despierta el equipo antes de la ventana de reserva.
3. El bot ejecuta la reserva.
4. El sistema vuelve a suspenderse hasta la siguiente ventana.

Este flujo permite que el equipo funcione de forma **autónoma para realizar reservas de clases** sin intervención manual.

---

# Descripción del incidente

El día **2026-03-06** ocurrió el siguiente comportamiento inesperado:

* El sistema despertó correctamente antes de la clase de las **07:00**.
* El usuario se conectó vía **SSH a las 07:02**.
* El sistema **no volvió a suspenderse** y permaneció activo hasta aproximadamente **08:30**.

El comportamiento esperado era que el equipo volviera a entrar en suspensión automáticamente después de finalizar la ventana de reserva.

---

# Evidencia en logs

Los logs del sistema muestran:

```
06:03:00 system will suspend now
06:03:00 PM: suspend entry
06:58:00 PM: suspend exit
```

Esto confirma que:

1. El script ejecutó correctamente la suspensión a las **06:03**.
2. El **RTC wakealarm despertó el sistema a las 06:58**.

Sin embargo, **no existe ningún log posterior que indique que el servicio `power-autonomous.service` se volvió a ejecutar después del wake**.

---

# Causa raíz

El servicio estaba definido así:

```ini
[Unit]
Description=Power Autonomous Scheduler
After=multi-user.target

[Service]
Type=oneshot
WorkingDirectory=/home/userx/Documents/gym-bot
ExecStart=/home/userx/Documents/gym-bot/venv/bin/python /home/userx/Documents/gym-bot/os-integration/power_autonomous.py
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Este tipo de servicio **solo se ejecuta durante el boot del sistema**.

Por lo tanto:

* Cuando el sistema **despertó del suspend a las 06:58**,
* **systemd no volvió a ejecutar el scheduler**.

Resultado:

```
Wake RTC
   ↓
Sistema despierta
   ↓
Scheduler NO se ejecuta
   ↓
No se vuelve a programar suspensión
   ↓
Sistema permanece activo
```

---

# Solución implementada

Se añadió un **hook de systemd que se ejecuta cada vez que el sistema vuelve de suspensión**.

Archivo creado:

```
/usr/lib/systemd/system-sleep/power-autonomous
```

Contenido:

```bash
#!/bin/bash

if [ "$1" = "post" ]; then
    systemctl start power-autonomous.service
fi
```

Permisos:

```
sudo chmod +x /usr/lib/systemd/system-sleep/power-autonomous
```

---

# Funcionamiento después de la solución

Con este hook, el flujo de ejecución es:

```
RTC wake
   ↓
Sistema despierta
   ↓
systemd ejecuta hook post-resume
   ↓
se inicia power-autonomous.service
   ↓
el script evalúa la ventana
   ↓
programa siguiente wake y suspensión
```

Esto garantiza que **cada vez que el sistema despierte**, el scheduler vuelva a evaluar si debe:

* permanecer despierto
* o suspenderse nuevamente.

---

# Resultado

Después de aplicar esta solución:

* El sistema mantiene un **ciclo autónomo de suspensión y wake por RTC**.
* El scheduler se ejecuta **en cada resume del sistema**.
* Se evita que el equipo quede activo indefinidamente después de un wake programado.

---

# Conclusión

El problema no estaba en el script de automatización sino en **cuándo se ejecutaba el servicio de systemd**.
Agregar un **hook de resume** garantiza que el scheduler vuelva a ejecutarse cada vez que el sistema despierta, restaurando completamente el comportamiento autónomo esperado.
