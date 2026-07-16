<div align="center">

<img src="https://img.shields.io/badge/gym--bot-Autonomous%20Reservation%20Engine-0d1117?style=for-the-badge&logo=playwright&logoColor=white" alt="gym-bot" height="60"/>

# gym-bot

**Unattended gym-class reservations. OS-level power orchestration. Telegram-based remote recovery.**

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-sync_API-2EAD33?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![Pydantic](https://img.shields.io/badge/Pydantic-typed_config-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Loguru](https://img.shields.io/badge/Loguru-dual_sink_logging-informational?style=flat-square)](https://github.com/Delgan/loguru)
[![systemd](https://img.shields.io/badge/systemd-timers_%2B_RTC_wake-262577?style=flat-square&logo=linux&logoColor=white)](https://www.freedesktop.org/wiki/Software/systemd/)
[![mypy](https://img.shields.io/badge/mypy-strict-2A6DB2?style=flat-square)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/License-Personal_Use-lightgrey?style=flat-square)](#license)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Logging](#logging)
- [Usage](#usage)
- [OS Integration](#os-integration)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**gym-bot** is a Python automation system that handles recurring gym class reservations on the [Compensar / DeportesCompensar](https://deportescompensar.com) platform — fully unattended.

Beyond simple task scheduling, the bot integrates deeply with the Linux OS to manage the host machine's power cycle autonomously: it suspends the machine between reservation windows, wakes it precisely before each booking, executes the reservation, and suspends again — without human intervention.

When errors occur, the bot does not crash silently. It notifies you via Telegram, pauses execution, and waits for your remote command to resume or retry — giving you a configurable intervention window to diagnose and resolve any issue from anywhere.

The codebase follows a **Page Object** style for browser automation and **explicit dependency injection** throughout: every class declares exactly what it needs in its constructor (typed config, a `Recovery` instance, a `TelegramClient`, etc.), and `src/main.py` is the single place where all of that is wired together. Nothing reads global state or instantiates its own dependencies behind the scenes.

---

## Features

### 🤖 Intelligent Scheduling

- YAML-driven weekly schedule with per-day class configuration
- Reservations open 2 days in advance — the bot calculates the correct booking window automatically
- Force-run mode for on-demand execution with a specific class, hour, and day
- Configurable execution time adjustment for fine-tuning trigger precision

### 🧠 Human Behavior Simulation

Designed to avoid bot detection through realistic interaction patterns:

- Variable mouse trajectories with randomized steps and micro-deviations
- Randomized click offsets within element bounding boxes
- Per-character typing delays with occasional typo-and-correction sequences
- Random scroll amounts and directions between interactions
- Non-uniform delays between all actions

### 🛡️ Anti-Detection

- Real browser profile (cookies, history, extensions)
- Removes automation flags (`--enable-automation`, `AutomationControlled`)
- JavaScript injection to mask `navigator.webdriver`, spoof plugins, and emulate real browser fingerprint
- Geolocation set to match the user's city

### 🔁 Layered Error Recovery

`Recovery` is injected with a `TelegramClient` and exposes two recovery mechanisms for different severity levels:

**`with_soft_recovery`** — silent auto-retry for transient failures, configurable retries with delay between attempts.

**`with_recovery`** — full recovery pipeline for critical failures:

1. Automatically reloads the page and retries up to N times
2. If the error persists, sends a Telegram notification and pauses execution
3. Waits for a remote command via Telegram:
   - `0` → Resume from current state
   - `1` → Refresh page and retry
4. If no response within the timeout, aborts gracefully (`RecoveryAbortedError`)

**CAPTCHA detection** is treated as a special case — any detected active CAPTCHA (`CaptchaDetectedError`) immediately triggers a Telegram alert without auto-retries, since human intervention is always required.

Failures raise specific exceptions from `src/utils/exceptions.py` (all subclasses of `GymBotError`) instead of generic `RuntimeError`s, so callers can tell what actually went wrong — a missing element, a failed redirect, an unverifiable reservation, an exhausted retry budget, etc.

### 💤 OS-Level Power Management

The bot integrates with the Linux kernel to manage the host machine's power state autonomously:

- `ReservationScheduleCalculator` reads the class schedule and computes the next reservation timestamp
- `SystemPowerController` programs the system's **RTC wakealarm** to wake the machine minutes before the booking window, and suspends via `systemctl suspend`
- `PowerCycleManager` orchestrates both to decide, on each wake, whether to run the active reservation window or go back to sleep
- A **systemd-sleep hook** re-executes the power cycle manager on every resume

This enables the host to remain suspended (near-zero power consumption) between reservation cycles.

### 📲 Telegram Integration

`TelegramClient` wraps the Bot API and is injected wherever notifications are needed:

- Real-time error alerts with full context (action name, error message, retry count)
- Interactive remote control: resume, refresh, or abort directly from your phone
- Reservation confirmation messages

### ✅ Post-Reservation Verification

After each reservation, `ClassChecker` navigates to the user's upcoming sessions page and confirms the booking was recorded correctly — raising `ReservationVerificationError` (and triggering recovery) if not found.

### 📝 Dual-Sink Logging

`src/utils/logger.py` configures two Loguru sinks side by side:

- **stdout** — compact, colorized on a TTY; captured into the systemd journal automatically when run as a service (crash-proof safety net, zero extra code)
- **`logs/logger.txt`** — plain text, line-count-bounded (`LOG_MAX_LINES`), auto-created and auto-trimmed (oldest lines dropped first)

The journal stays as the supervisor-level record; `logs/logger.txt` is the fast, `journalctl`-free view for everyday debugging. See [Logging](#logging) for the full rationale and how to tail either one in real time.

---

## Tech Stack

| Layer                 | Technology                          |
| ---------------------- | ------------------------------------ |
| Language               | Python 3.11+                         |
| Browser Automation     | Playwright (sync API)                |
| Data validation        | Pydantic / pydantic-settings         |
| Scheduling             | systemd user timers                  |
| Power Management       | RTC wakealarm + systemd-sleep hooks  |
| Notifications          | Telegram Bot API                     |
| Configuration          | `.env` + YAML                        |
| Logging                | Loguru (dual sink: stdout + rotated file) |
| Timezone handling      | pytz / zoneinfo                      |
| CLI                    | argparse                             |
| Type checking / lint   | mypy (strict) / ruff / pyright (strict) |

---

## Project Structure

```
gym-bot/
├── src/
│   ├── main.py                       # Composition root: wires every dependency, CLI subcommands
│   ├── types/
│   │   └── config.py                 # Pydantic models for env vars and YAML config (typed, validated)
│   ├── settings/
│   │   ├── provider.py               # Settings: loads .env + YAML into typed config objects
│   │   ├── app_config.yaml           # App settings (URLs, selectors, power, browser paths)
│   │   └── schedule.yaml             # Weekly class schedule
│   ├── bot/
│   │   ├── browser.py                # Browser: Chromium/Firefox launcher with stealth config
│   │   └── scheduler.py              # Scheduler: force-run vs regular-run class resolution
│   ├── components/                   # Page Object classes — one responsibility each
│   │   ├── login.py                  # LoginPage
│   │   ├── post_login.py             # PostLoginPage
│   │   ├── logout.py                 # LogoutPage
│   │   ├── membership.py             # MembershipSelector
│   │   ├── day_selector.py           # DateSelector
│   │   ├── gym_class_booker.py       # ClassBooker (composes acceptance + checker)
│   │   ├── gym_class_acceptance.py   # ClassAcceptance
│   │   ├── gym_class_checker.py      # ClassChecker
│   │   └── reserve_process.py        # ReservationProcess (orchestrates the sub-flow above)
│   ├── notifications/
│   │   └── telegram.py               # TelegramClient: notify() / get_updates()
│   ├── os_integration/
│   │   ├── os_integration_utils.py   # ReservationScheduleCalculator, SystemPowerController
│   │   └── power_cycle.py            # PowerCycleManager
│   └── utils/
│       ├── exceptions.py             # GymBotError hierarchy (domain-specific exceptions)
│       ├── logger.py                 # Loguru config: stdout sink + line-bounded file sink
│       ├── strings.py                # Text normalization utilities
│       ├── time_utils.py             # Time format conversion, day mapping
│       ├── human_behavior.py         # Mouse, click, typing, scroll simulation
│       ├── page_utils.py             # Page waits, CAPTCHA detection, URL management
│       ├── recovery.py               # Recovery: with_recovery / with_soft_recovery
│       └── error_broadcast.py        # ErrorBroadcaster: screenshot + Telegram error notification
├── logs/                              # Rotated application log (gitignored, dir tracked via .gitkeep)
│   └── logger.txt                    # Plain-text log, auto-created, capped at LOG_MAX_LINES
├── debug/                             # Auto-generated screenshots on error (gitignored)
├── doc/
│   └── os_integration.md             # Full OS integration guide (also inlined in OS Integration below)
├── .env                                # Secrets and credentials (gitignored)
├── .python-version                    # 3.11.8
├── pyproject.toml                     # mypy + ruff configuration
├── pyrightconfig.json                 # pyright strict-mode configuration
└── requirements.txt
```

**Utility functions vs. classes.** Pure, stateless helpers (`human_behavior.py`, `page_utils.py`, `strings.py`, `time_utils.py`) stay as plain functions — wrapping them in classes would add ceremony without adding value. Anything that carries state or an external dependency (a `TelegramClient`, retry counters, browser handles) is a class that receives what it needs through its constructor.

**`logger.py` is the one intentional exception to constructor injection.** It self-configures at import time (like `logging.basicConfig` would), reading `.env` directly — `Settings` doesn't exist yet at the point the logger module is first imported.

---

## Requirements

- Python 3.11+
- Arch Linux (or any Linux distro with systemd)
- Chromium or Firefox installed
- A Telegram bot token and chat ID
- A Compensar account with an active gym membership

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/youruser/gym-bot.git
cd gym-bot
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium firefox
```

**4. Configure your environment**

```bash
cp .env.example .env   # if you keep one; otherwise create .env directly
```

Edit `src/settings/schedule.yaml` and `src/settings/app_config.yaml` to match your gym class schedule and system paths.

---

## Configuration

Configuration is loaded once by `Settings` (`src/settings/provider.py`) and validated with Pydantic — a malformed `.env` or YAML file fails fast with a readable error instead of surfacing as a `KeyError` deep in the automation flow.

### `.env`

```env
# USER DATA
COMPENSAR_DOC_TYPE=CC
COMPENSAR_DOC_NUM=your_id_number
COMPENSAR_PASSWORD=your_password

# NOTIFICATIONS
TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id

# BROWSER PROFILE (optional)
# FIREFOX_PROFILE_NAME=abc12345.gym-bot

# LOGGING (optional — see Logging section)
LOG_DIR=logs
LOG_FILENAME=logger.txt
LOG_MAX_LINES=5000
```

### `src/settings/app_config.yaml`

```yaml
environment:
  login_url: https://seguridad.compensar.com/sign-in?...
  inside_system_url: https://sistemaplanbienestar.deportescompensar.com/...
  gym_class_verification_url: https://sistemared.deportescompensar.com/...
  inside_system_url_pattern: "**compensar.com/**"

os:
  home_user: "~"
  chromium_path: /usr/bin/chromium
  firefox_path: /usr/bin/firefox

power_autonomous:
  wake_minutes_before: 5
  sleep_minutes_after: 10
  wakealarm_path: /sys/class/rtc/rtc0/wakealarm

execution:
  bot_force_run: false
  execution_adjustment: -1 # minutes offset for booking trigger
  bot_headless: false
```

### `src/settings/schedule.yaml`

Classes are booked **2 days in advance**. A `monday` entry triggers on Saturday.

```yaml
timezone: America/Bogota

# Used when bot_force_run: true
forcedClass:
  name: PD Yoga
  hour: 08:00 - 09:00
  day: tuesday

days:
  monday:
    - name: Pilates
      hour: 06:00 - 07:00
    - name: Estiramiento
      hour: 07:00 - 08:00
  tuesday:
    - name: PD Yoga
      hour: 06:00 - 07:00
```

---

## Logging

gym-bot deliberately logs in **two independent places at once**: the systemd journal and its own file at `logs/logger.txt`. Neither replaces the other — they answer different questions and fail independently of each other.

| Log                | Written by                          | Survives                                              | Best for                                          |
| ------------------- | ------------------------------------ | ------------------------------------------------------ | --------------------------------------------------- |
| **journal**          | systemd, capturing the unit's `stdout`/`stderr` (default behavior — nothing in the unit files overrides it) | import errors, crashes before `logger.py` even runs, OOM kills, service restarts | `journalctl -u gym-bot.service`, correlating with suspend/resume, "did the service even start" |
| **`logs/logger.txt`** | `src/utils/logger.py`, a second Loguru sink added next to the existing `stdout` one | app-level events, in a format the app controls | `tail -f`, `grep`, `cat` — the fast day-to-day view, no systemd tooling needed |

This is standard practice for anything running under a process supervisor (systemd, Docker, k8s): always emit to `stdout`/`stderr` so the supervisor's own capture acts as a crash-proof safety net, independent of whether the app's own logging code ever gets a chance to run — and *additionally* keep an app-level log when you want something friendlier than journal syntax for daily use. It costs nothing extra here: systemd already captures `stdout` for every unit by default, so the journal side needs zero code — it "just works". The `stdout` sink also auto-detects that it isn't a TTY under systemd and drops ANSI color codes on its own (Loguru's default), so nothing garbles `journalctl`'s output either.

If you don't run the bot under systemd at all (plain manual `python -m src.main`), only `logs/logger.txt` (and your terminal) applies — there's no journal to speak of.

### What each sink looks like

`src/utils/logger.py` configures two sinks on the same Loguru instance:

| Sink       | Destination         | Format                                    | Purpose                                  |
| ---------- | -------------------- | ------------------------------------------ | ----------------------------------------- |
| `stdout`   | terminal / journal (when run as a service) | colorized on a TTY, plain when piped; timestamp + message | interactive runs, and — via systemd's capture — the journal |
| file       | `logs/logger.txt`     | plain text, timestamp + level + message    | fast, `journalctl`-free inspection        |

### Why `logs/logger.txt` instead of reading the journal directly

`journalctl` prefixes every line with its own (long) timestamp and unit metadata, on top of the timestamp the app already writes — two timestamps per line, non-configurable, and not readable with plain `cat`/`tail`. The file sink writes exactly what the app intends, nothing else, so it's the better tool for quick day-to-day checks; the journal remains the tool for "why didn't the service start at all".

### Behavior

- `logs/` and `logs/logger.txt` are created automatically on first import if they don't exist; if the file already exists, new lines are simply appended to it.
- The file is capped at `LOG_MAX_LINES` (default `5000`). Once the limit is exceeded, the **oldest lines are dropped first** (FIFO) so the file never grows unbounded.
- Both sinks currently log at `INFO` and above.
- The journal has its own independent retention policy, governed by `journald` (`/etc/systemd/journald.conf`, e.g. `SystemMaxUse`) — gym-bot doesn't touch it.

### Configuration (`.env`)

| Variable        | Default        | Description                                   |
| ---------------- | -------------- | ---------------------------------------------- |
| `LOG_DIR`         | `logs`         | Directory for the log file, relative to the project root |
| `LOG_FILENAME`    | `logger.txt`   | Log file name                                  |
| `LOG_MAX_LINES`   | `5000`         | Max lines kept in the file before trimming     |

### Reading the log

```bash
# App-level file — fast day-to-day view
cat logs/logger.txt          # full history
tail -f logs/logger.txt      # real-time, no extra timestamp column

# Journal — service lifecycle / crash-proof view
journalctl --user -u gym-bot.service -f
```

`tail -f logs/logger.txt` is the direct replacement for the "watching things happen live" workflow `journalctl -f` was used for — same real-time behavior, cleaner output, and it works identically whether the bot is run manually or via `gym-bot.timer`. Reach for `journalctl` instead when you need to know whether the *service itself* started, crashed, or was killed — see [OS Integration](#os-integration) for the full picture.

---

## Usage

All commands are executed from the project root using `python -m src.main`.

### Reserve classes (default)

```bash
python -m src.main
# or explicitly:
python -m src.main run
```

### Force-run a specific class

Set `bot_force_run: true` in `app_config.yaml` and configure `forcedClass` in `schedule.yaml`, then:

```bash
python -m src.main run
```

### Power management

```bash
# Program RTC wake alarm and suspend immediately
python -m src.main suspend-now

# Manage full power cycle (active window → suspend → next cycle)
python -m src.main power-cycle
```

### Recommended shell aliases (`~/.zshrc`)

```zsh
alias gym-bot="cd /home/user/gym-bot && python -m src.main"
alias suspend-now="cd /home/user/gym-bot && sudo -n /home/user/gym-bot/.venv/bin/python -m src.main suspend-now"
alias power-cycle="cd /home/user/gym-bot && sudo -n /home/user/gym-bot/.venv/bin/python -m src.main power-cycle"
alias gym-bot-logs="tail -f /home/user/gym-bot/logs/logger.txt"
```

---

## OS Integration

The bot is designed to run as a **systemd-managed service**, with a companion timer and RTC-based wake scheduling so the whole cycle (wake → reserve → sleep) runs unattended — systemd services, timers, sudoers configuration, RTC wake management, and shell aliases, all covered below. Also kept as a standalone file: [`doc/os_integration.md`](doc/os_integration.md).

---

### Architecture Overview

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

> **Logging note:** every unit below runs as a plain systemd service, so its stdout is captured into the journal automatically (`StandardOutput=journal` is systemd's default — nothing below overrides it). On top of that, the bot writes its own bounded log to `logs/logger.txt` (see [Logging](#logging) above). Both exist by design: the journal is the crash-proof, supervisor-level record (`journalctl`), and `logs/logger.txt` is the fast, `tail -f`-friendly day-to-day view. See [§4](#4-bot-service--gym-botservice) and [§9](#9-quick-verification) for how to read each.

---

### 1. Shell Aliases (`.zshrc`)

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

### 2. sudoers Configuration

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

### 3. Bot Timer — `gym-bot.timer`

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

### 4. Bot Service — `gym-bot.service`

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

### 5. Power Autonomous Service — `power-autonomous.service`

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

### 6. systemd-sleep Hook (Post-Resume)

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

### 7. Disable USB Wakeup Sources

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

#### Make it persistent across reboots

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

### 8. Complete Autonomous Power Cycle

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

### 9. Quick Verification

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

### 10. Troubleshooting

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

---

### Execution Flow

```
RTC wakealarm fires
       ↓
systemd-sleep hook → python -m src.main power-cycle
       ↓
gym-bot.timer fires every minute → python -m src.main run
       ↓
Scheduler evaluates schedule → finds matching class
       ↓
Browser launches → LoginPage → PostLoginPage → DateSelector
       ↓
ClassBooker selects class → ClassAcceptance confirms → ClassChecker verifies
       ↓
Telegram: "✅ Reservation complete"
       ↓
PowerCycleManager programs next RTC wake → suspends
```

### Error Recovery Flow

```
Exception raised in any step
       ↓
Recovery.with_recovery: auto-refresh × 2 (silent)
       ↓
Telegram alert via TelegramClient → wait up to 10 minutes
       ↓
User replies: 0 (resume) or 1 (refresh & retry)
       ↓
Bot continues from current state, or raises RecoveryAbortedError
```

---

## Architecture

The project follows a **layered architecture with a single composition root**:

```
src/main.py                          ← entry point: builds every object, wires dependencies, CLI subcommands
    ↓
src/bot/scheduler.py (Scheduler)     ← decides what to run and when
    ↓
src/components/                      ← Page Object classes, one browser step each
    ↓
src/utils/                           ← cross-cutting concerns (recovery, page waits, human behavior, logging)
    ↓
src/settings/provider.py (Settings)  ← single source of truth for all config, typed via src/types/config.py
```

**Key design decisions:**

- **Dependency injection everywhere.** Every class takes its config and collaborators (typed Pydantic models, `Recovery`, `TelegramClient`) through its constructor. Nothing does `Settings()` or reads a global at import time — `main.py` is the only place that constructs `Settings` and wires the object graph. `logger.py` is the deliberate exception, documented in [Project Structure](#project-structure).
- **Page Object pattern for browser automation.** Each `components/` class owns one step of the flow (`LoginPage`, `DateSelector`, `ClassBooker`, ...) and exposes a small, intention-revealing public method. `ReservationProcess` composes them into the full reservation sub-flow.
- **Typed configuration, not dicts.** `src/types/config.py` defines Pydantic models for every section of `.env` and the YAML files. Config errors surface at startup, with a readable validation message, instead of as a `KeyError`/`AttributeError` mid-flow.
- **Domain-specific exceptions.** All custom exceptions inherit from `GymBotError` (`src/utils/exceptions.py`), so recovery logic and logging can distinguish a missing element from a failed redirect from an unverifiable reservation, instead of catching bare `RuntimeError`.
- **All page interactions go through `Recovery.with_recovery` or `with_soft_recovery`** — no bare `try/except` swallowing errors in business logic.
- **Human behavior simulation is fully decoupled from automation logic** — `human_behavior.py` has no knowledge of login, reservations, or scheduling.
- **Power management is a separate concern** (`os_integration/`), triggered via its own CLI subcommands, not hardcoded into the reservation flow.
- **Logging is dual-sink and bounded.** `logger.py` writes to `stdout` for interactive runs and to a line-capped `logs/logger.txt` for persistent, `journalctl`-free inspection — see [Logging](#logging).

---

## Contributing

This is a personal project. Feel free to fork and adapt it for your own automation needs. The recovery system, human behavior layer, and power management integration are designed to be reusable across different web automation scenarios.

---

## License

Personal use. Not affiliated with Compensar or DeportesCompensar.

---

<div align="center">

_Automating the routine, so humans can shine._

</div>
