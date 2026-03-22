# gym-bot — OS Integration & Power Automation

Documentación de la integración del bot con el sistema operativo para gestión autónoma del ciclo de energía (suspend/wake) y ejecución automática de reservas.

---

## Arquitectura general

```
gym-bot.timer (cada minuto)
   ↓
gym-bot.service → main.py
   ↓
Evalúa si hay reserva → ejecuta o termina

RTC wakealarm
   ↓
Sistema despierta
   ↓
systemd hook post-resume
   ↓
power-autonomous.service → power_autonomous.py
   ↓
Evalúa ventana → programa siguiente wake → suspende
```

---

## 1. Alias en `.zshrc`

Permite ejecutar el scheduler de suspensión manualmente desde terminal o SSH sin password.

```zsh
# ~/.zshrc
alias suspend-auto="sudo -n /home/userx/Documents/gym-bot/venv/bin/python /home/userx/Documents/gym-bot/os_integration/start_power_autonomous.py"
```

Aplicar cambios:
```bash
source ~/.zshrc
```

---

## 2. Configuración de sudoers

Permite ejecutar `systemctl suspend` y el script Python sin contraseña, tanto desde terminal como desde SSH (sin TTY).

Editar con:
```bash
sudo visudo -f /etc/sudoers.d/bot-suspend
```

Contenido:
```
Defaults!/usr/bin/systemctl !requiretty
Defaults!/home/userx/Documents/gym-bot/venv/bin/python !requiretty

userx ALL=(root) NOPASSWD: /usr/bin/systemctl suspend
userx ALL=(root) NOPASSWD: /home/userx/Documents/gym-bot/venv/bin/python /home/userx/Documents/gym-bot/os_integration/start_power_autonomous.py
```

Verificar que las reglas están activas:
```bash
sudo -l | grep -E "suspend|python"
```

---

## 3. Servicio del bot — `gym-bot.service`

Ejecutado por el timer cada minuto. Evalúa si corresponde ejecutar una reserva.

```bash
# Ubicación
~/.config/systemd/user/gym-bot.service
```

```ini
[Unit]
Description=Gym Bot

[Service]
Type=oneshot
WorkingDirectory=/home/userx/Documents/gym-bot
ExecStart=/home/userx/.pyenv/versions/gym-bot-env/bin/python main.py
```

---

## 4. Timer del bot — `gym-bot.timer`

Dispara `gym-bot.service` cada minuto.

```bash
# Ubicación
~/.config/systemd/user/gym-bot.timer
```

```ini
[Unit]
Description=Run Gym Bot every minute

[Timer]
OnCalendar=*-*-* *:*:00
Persistent=true

[Install]
WantedBy=timers.target
```

Comandos de control:
```bash
systemctl --user daemon-reload
systemctl --user enable gym-bot.timer
systemctl --user start gym-bot.timer
systemctl --user stop gym-bot.timer
systemctl --user status gym-bot.timer
systemctl --user list-timers
```

Logs:
```bash
journalctl --user -u gym-bot.service
journalctl --user -u gym-bot.service -f  # tiempo real
```

---

## 5. Servicio de power automation — `power-autonomous.service`

Gestiona el ciclo suspend/wake autónomo.

```bash
# Ubicación
/etc/systemd/system/power-autonomous.service
```

```ini
[Unit]
Description=Power Autonomous Scheduler
After=multi-user.target

[Service]
Type=oneshot
WorkingDirectory=/home/userx/Documents/gym-bot
ExecStart=/home/userx/Documents/gym-bot/venv/bin/python /home/userx/Documents/gym-bot/os_integration/power_autonomous.py
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

> ⚠️ Este servicio solo se ejecuta en boot. Para el ciclo autónomo es necesario el hook de resume (ver sección 6).

---

## 6. Hook post-resume — systemd-sleep

Ejecuta el scheduler cada vez que el sistema vuelve de suspensión, garantizando el ciclo autónomo.

```bash
# Ubicación
/usr/lib/systemd/system-sleep/power-autonomous
```

```bash
#!/bin/bash

if [ "$1" = "post" ]; then
    systemctl start power-autonomous.service
fi
```

Aplicar permisos:
```bash
sudo chmod +x /usr/lib/systemd/system-sleep/power-autonomous
```

---

## 7. Fix: USB controller wakeup

El controlador USB (XHC) puede despertar el sistema prematuramente ante interrupciones de dispositivos conectados. Se desactiva esta fuente de wake.

Deshabilitar manualmente:
```bash
echo XHC | sudo tee /proc/acpi/wakeup
```

Verificar:
```bash
cat /proc/acpi/wakeup | grep XHC
# Debe mostrar: XHC   S3   *disabled
```

### Hacer el fix persistente

```bash
sudo nano /etc/systemd/system/disable-usb-wakeup.service
```

```ini
[Unit]
Description=Disable USB wakeup
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo XHC > /proc/acpi/wakeup"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable disable-usb-wakeup.service
```

---

## 8. Flujo completo de ciclo autónomo

```
1. Sistema suspendido
2. RTC wakealarm despierta el sistema (WAKE_MINUTES_BEFORE antes de la reserva)
3. systemd hook post-resume ejecuta power-autonomous.service
4. power_autonomous.py evalúa la ventana activa
5. Si está en ventana → espera hasta fin de ventana
6. gym-bot.timer ejecuta main.py → realiza la reserva
7. power_autonomous.py programa el siguiente RTC wake
8. Sistema vuelve a suspenderse
```

---

## 9. Verificación rápida del sistema

```bash
# Alias funciona sin password
suspend-auto --dry-run  # si lo tienes implementado

# Reglas sudo activas
sudo -l | grep -E "suspend|python"

# Wake sources activos
cat /proc/acpi/wakeup

# RTC wakealarm programado
cat /sys/class/rtc/rtc0/wakealarm

# Convertir timestamp a fecha legible
date -d @$(cat /sys/class/rtc/rtc0/wakealarm)

# Estado del timer del bot
systemctl --user status gym-bot.timer

# Logs recientes del bot
journalctl --user -u gym-bot.service --since "1 hour ago"
```
