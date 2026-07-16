# gym-bot — OS Integration & Power Management

Complete setup guide for integrating gym-bot with the Linux OS, including systemd services, timers, sudoers configuration, RTC wake management, and shell aliases.

---

## Architecture Overview

```
gym-bot.timer (every minute)
   ↓
python -m src.main run
   ↓
Evaluates schedule → reserves or exits immediately

─────────────────────────────────────

RTC wakealarm
   ↓
System wakes up
   ↓
systemd-sleep hook (post-resume)
   ↓
python -m src.main power-cycle
   ↓
Evaluates active window → waits → programs next wake → suspends
```

> **Logging note:** every unit below runs as a plain systemd service, so its stdout is captured into the journal automatically (`StandardOutput=journal` is systemd's default — nothing below overrides it). On top of that, the bot writes its own bounded log to `logs/logger.txt` (see [Logging](#logging) in the main README). Both exist by design: the journal is the crash-proof, supervisor-level record (`journalctl`), and `logs/logger.txt` is the fast, `tail -f`-friendly day-to-day view. See [§4](#4-bot-service--gym-botservice) and [§9](#9-quick-verification) for how to read each.

---

## 1. Shell Aliases (`.zshrc`)

Add to `~/.zshrc` for convenient manual control:

```zsh
# Run the bot manually
alias gym-bot="cd /home/user/gym-bot && python -m src.main"

# Suspend immediately after programming the next RTC wake
alias suspend-now="cd /home/user/gym-bot && sudo -n /home/user/gym-bot/.venv/bin/python -m src.main suspend-now"

# Run full power cycle (active window management)
alias power-cycle="cd /home/user/gym-bot && sudo -n /home/user/gym-bot/.venv/bin/python -m src.main power-cycle"
```

Apply changes:

```bash
source ~/.zshrc
```

> **Important:** the `cd` before each command is required — `python -m src.main` must run from the project root for imports to resolve correctly.

---

## 2. sudoers Configuration

Allows running `systemctl suspend` and the Python entry point without a password, both locally and over SSH (no TTY required).

Edit with:

```bash
sudo visudo -f /etc/sudoers.d/gym-bot
```

Content:

```
Defaults!/usr/bin/systemctl !requiretty
Defaults!/home/user/gym-bot/.venv/bin/python !requiretty

user ALL=(root) NOPASSWD: /usr/bin/systemctl suspend
user ALL=(root) NOPASSWD: /home/user/gym-bot/.venv/bin/python -m src.main *
```

Verify the rules are active:

```bash
sudo -l | grep -E "suspend|python"
```

Test passwordless suspend:

```bash
sudo -n systemctl suspend
```

---

## 3. Bot Timer — `gym-bot.timer`

Triggers `gym-bot.service` every minute. The service runs `main.py`, which evaluates the schedule and exits immediately if no reservation is due.

```bash
# Location
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

---

## 4. Bot Service — `gym-bot.service`

```bash
# Location
~/.config/systemd/user/gym-bot.service
```

```ini
[Unit]
Description=Gym Bot

[Service]
Type=oneshot
WorkingDirectory=/home/user/gym-bot
ExecStart=/home/user/gym-bot/.venv/bin/python -m src.main run
Environment="PYTHONUNBUFFERED=1"
```

Timer control commands:

```bash
systemctl --user daemon-reload
systemctl --user enable gym-bot.timer
systemctl --user start gym-bot.timer
systemctl --user stop gym-bot.timer
systemctl --user status gym-bot.timer
systemctl --user list-timers
```

Logs — two independent views, kept intentionally:

```bash
# Journal — systemd-level record: crash traces, exit codes, restarts,
# service lifecycle. Survives even if the app can't write to disk.
journalctl --user -u gym-bot.service
journalctl --user -u gym-bot.service -f   # real-time
journalctl --user -u gym-bot.service --since "1 hour ago"

# App log — plain text, line-bounded (LOG_MAX_LINES), no unit/timestamp
# noise. This is the one to reach for day to day.
tail -f /home/user/gym-bot/logs/logger.txt
```

Neither replaces the other: `journalctl` is systemd's own log of the *unit* (it works even if `logger.py` itself never runs, e.g. an import error before logging is configured), while `logs/logger.txt` is the app's own structured record, easy to `cat`/`tail`/`grep` without systemd tooling. Don't set `StandardOutput=null` in the unit file below — that would silence the journal safety net for no benefit.

---

## 5. Power Autonomous Service — `power-autonomous.service`

Runs the power cycle manager on boot.

```bash
# Location
/etc/systemd/system/power-autonomous.service
```

```ini
[Unit]
Description=Gym Bot Power Cycle Manager
After=multi-user.target

[Service]
Type=oneshot
WorkingDirectory=/home/user/gym-bot
ExecStart=/home/user/gym-bot/.venv/bin/python -m src.main power-cycle
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable power-autonomous.service
sudo systemctl daemon-reload
```

> This service only runs on boot. The systemd-sleep hook (section 6) ensures it also runs on every resume from suspend.

---

## 6. systemd-sleep Hook (Post-Resume)

Executes the power cycle manager every time the system returns from suspend, ensuring the autonomous cycle continues after each wake.

```bash
# Location
/usr/lib/systemd/system-sleep/gym-bot-power
```

```bash
#!/bin/bash

if [ "$1" = "post" ]; then
    cd /home/user/gym-bot && \
    /home/user/gym-bot/.venv/bin/python -m src.main power-cycle
fi
```

Apply permissions:

```bash
sudo chmod +x /usr/lib/systemd/system-sleep/gym-bot-power
```

Verify the hook is in place:

```bash
ls -la /usr/lib/systemd/system-sleep/
```

---

## 7. Disable USB Wakeup Sources

USB controllers can wake the system prematurely when connected devices generate hardware interrupts. This fix prevents that.

Check current wakeup sources:

```bash
cat /proc/acpi/wakeup
```

Disable manually:

```bash
echo XHC | sudo tee /proc/acpi/wakeup
```

Verify it's disabled:

```bash
cat /proc/acpi/wakeup | grep XHC
# Should show: XHC   S3   *disabled
```

### Make it persistent across reboots

```bash
sudo nano /etc/systemd/system/disable-wake-devices.service
```

```ini
[Unit]
Description=Disable ACPI wake devices
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "grep -q 'EHC1.*enabled' /proc/acpi/wakeup && echo EHC1 > /proc/acpi/wakeup || true"
ExecStart=/bin/sh -c "grep -q 'XHC.*enabled' /proc/acpi/wakeup && echo XHC > /proc/acpi/wakeup || true"
ExecStart=/bin/sh -c "grep -q 'LID0.*enabled' /proc/acpi/wakeup && echo LID0 > /proc/acpi/wakeup || true"
ExecStart=/bin/sh -c "grep -q 'PXSX.*enabled' /proc/acpi/wakeup && echo PXSX > /proc/acpi/wakeup || true"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable disable-wake-devices.service
sudo systemctl daemon-reload
```

---

## 8. Complete Autonomous Power Cycle

With all components in place, the full cycle works as follows:

```
1. System suspended
2. RTC wakealarm fires (wake_minutes_before the reservation)
3. System wakes up
4. systemd-sleep hook runs: python -m src.main power-cycle
5. power-cycle evaluates active window → stays awake
6. gym-bot.timer fires: python -m src.main run
7. Bot performs the reservation
8. sleep_minutes_after elapses
9. power-cycle programs next RTC wake
10. System suspends again
```

---

## 9. Quick Verification

Run these to confirm the full setup is working:

```bash
# Aliases work without password
suspend-now

# sudoers rules are active
sudo -l | grep -E "suspend|python"

# USB wakeup disabled
cat /proc/acpi/wakeup | grep -E "XHC|EHC|LID|PXSX"

# Current RTC wake alarm
cat /sys/class/rtc/rtc0/wakealarm
date -d @$(cat /sys/class/rtc/rtc0/wakealarm)

# Bot timer is running
systemctl --user status gym-bot.timer
systemctl --user list-timers | grep gym

# Power service is enabled
systemctl status power-autonomous.service

# Sleep hook is executable
ls -la /usr/lib/systemd/system-sleep/gym-bot-power

# Recent bot logs — journal (systemd/service level)
journalctl --user -u gym-bot.service --since "today"

# Recent bot logs — app-level file (day-to-day view)
tail -50 /home/user/gym-bot/logs/logger.txt

# System suspend/resume history
journalctl -b | grep -E "suspend entry|resume complete" | tail -10
```

---

## 10. Troubleshooting

**System wakes up too early**
Check for active wakeup sources beyond XHC:

```bash
cat /proc/acpi/wakeup | grep enabled
```

Disable any unexpected sources using the same pattern as section 7.

**Bot runs but `.env` not found**
The command must be run from the project root. Verify the `cd` is present in your alias and in the systemd `WorkingDirectory`.

**`sudo -n` still asks for password**
Confirm the sudoers rule path matches exactly, including the `.venv` path:

```bash
which python  # inside the venv
sudo -l | grep python
```

**power-cycle doesn't suspend after the reservation**
Check `sleep_minutes_after` in `app_config.yaml` — if the bot takes longer than this value to finish, power-cycle exits the active window and skips suspension. Increase the value to give more margin.

**Timer not firing**

```bash
systemctl --user status gym-bot.timer
journalctl --user -u gym-bot.timer -f
```

**`logs/logger.txt` is empty but `journalctl` shows activity**
Means the process is being launched but `src/utils/logger.py` never finished importing (e.g. `LOG_DIR` points somewhere unwritable, or `.env` isn't found because `WorkingDirectory` is wrong — see the `.env not found` entry above). Check the journal first; it's the one log that's independent of the app's own file-writing code.
