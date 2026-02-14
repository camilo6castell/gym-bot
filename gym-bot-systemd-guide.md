# Gym Bot -- Sistema de Disparo y Automatización con systemd --user

## 📌 Cómo funciona el disparo del sistema

El bot no está en ejecución permanente.\
Se ejecuta cada minuto mediante un **systemd user timer**.

El flujo es:

1.  El `gym-bot.timer` se activa cada minuto.
2.  El timer ejecuta `gym-bot.service`.
3.  El servicio ejecuta `main.py`.
4.  `main.py`:
    -   Evalúa si corresponde ejecutar una reserva (2 días después de la
        clase configurada).
    -   Si corresponde → lanza navegador y ejecuta la reserva.
    -   Si no corresponde → termina inmediatamente.

Esto evita procesos persistentes y hace el sistema más estable que usar
cron.

------------------------------------------------------------------------

# 📁 Ubicación de archivos systemd

Los archivos deben crearse en:

    ~/.config/systemd/user/

Ruta completa:

    /home/userx/.config/systemd/user/

------------------------------------------------------------------------

# 📄 gym-bot.service

Archivo:

    ~/.config/systemd/user/gym-bot.service

Contenido:

``` ini
[Unit]
Description=Gym Bot

[Service]
Type=oneshot
WorkingDirectory=/home/userx/Documents/gym-bot
ExecStart=/home/userx/.pyenv/versions/gym-bot-env/bin/python main.py
```

------------------------------------------------------------------------

# ⏱ gym-bot.timer

Archivo:

    ~/.config/systemd/user/gym-bot.timer

Contenido:

``` ini
[Unit]
Description=Run Gym Bot every minute

[Timer]
OnCalendar=*-*-* *:*:00
Persistent=true

[Install]
WantedBy=timers.target
```

------------------------------------------------------------------------

# 🚀 Comandos de control

## Recargar systemd después de crear o modificar archivos

    systemctl --user daemon-reload

------------------------------------------------------------------------

## Habilitar el timer (para que arranque automáticamente con tu sesión)

    systemctl --user enable gym-bot.timer

------------------------------------------------------------------------

## Iniciar el timer manualmente

    systemctl --user start gym-bot.timer

------------------------------------------------------------------------

## Detener el timer inmediatamente

    systemctl --user stop gym-bot.timer

------------------------------------------------------------------------

## Deshabilitar el timer (para que no arranque automáticamente)

    systemctl --user disable gym-bot.timer

------------------------------------------------------------------------

## Ver estado del timer

    systemctl --user status gym-bot.timer

------------------------------------------------------------------------

## Ver todos los timers activos

    systemctl --user list-timers

------------------------------------------------------------------------

# 📜 Logs

## Ver logs del servicio

    journalctl --user -u gym-bot.service

------------------------------------------------------------------------

## Ver logs en tiempo real

    journalctl --user -u gym-bot.service -f

------------------------------------------------------------------------

# 🎯 Ventajas de usar systemd --user

-   Hereda entorno gráfico (DISPLAY, DBUS)
-   No requiere hacks con xhost
-   No requiere headless
-   Más estable que cron para aplicaciones gráficas
-   Fácil de activar/desactivar

------------------------------------------------------------------------

# 🧠 Flujo recomendado de uso

Después de crear los archivos:

    systemctl --user daemon-reload
    systemctl --user enable gym-bot.timer
    systemctl --user start gym-bot.timer

Para apagarlo:

    systemctl --user stop gym-bot.timer

Para volver a encenderlo:

    systemctl --user start gym-bot.timer

------------------------------------------------------------------------

Sistema listo.
