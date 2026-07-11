# gym-bot

> Autonomous gym class reservation bot with OS-level power management, human behavior simulation, and Telegram-based remote error recovery.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [OS Integration](#os-integration)
- [Architecture](#architecture)
- [Contributing](#contributing)

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

---

## Tech Stack

| Layer               | Technology                           |
| -------------------- | ------------------------------------ |
| Language              | Python 3.11+                         |
| Browser Automation    | Playwright (sync API)                |
| Data validation       | Pydantic / pydantic-settings         |
| Scheduling            | systemd user timers                  |
| Power Management      | RTC wakealarm + systemd-sleep hooks  |
| Notifications         | Telegram Bot API                     |
| Configuration         | `.env` + YAML                        |
| Logging               | Loguru                               |
| Timezone handling     | pytz / zoneinfo                      |
| CLI                   | argparse                             |
| Type checking / lint  | mypy (strict) / ruff                 |

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
│       ├── logger.py                 # Loguru configuration
│       ├── strings.py                # Text normalization utilities
│       ├── time_utils.py             # Time format conversion, day mapping
│       ├── human_behavior.py         # Mouse, click, typing, scroll simulation
│       ├── page_utils.py             # Page waits, CAPTCHA detection, URL management
│       ├── recovery.py               # Recovery: with_recovery / with_soft_recovery
│       └── error_broadcast.py        # ErrorBroadcaster: screenshot + Telegram error notification
├── debug/                            # Auto-generated screenshots on error (gitignored)
├── doc/
│   └── os_integration.md             # Full OS integration setup guide
├── .env                               # Secrets and credentials (gitignored)
├── pyproject.toml                     # mypy + ruff configuration
└── requirements.txt
```

**Utility functions vs. classes.** Pure, stateless helpers (`human_behavior.py`, `page_utils.py`, `strings.py`, `time_utils.py`) stay as plain functions — wrapping them in classes would add ceremony without adding value. Anything that carries state or an external dependency (a `TelegramClient`, retry counters, browser handles) is a class that receives what it needs through its constructor.

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
playwright install chromium
```

**4. Create your `.env` file**

There's no `.env.example` checked into the repo (secrets shouldn't live in git, even as a template with placeholder values) — create `.env` at the project root with the variables listed in [Configuration](#configuration) below.

**5. Configure your schedule and app settings**

Edit `src/settings/schedule.yaml` and `src/settings/app_config.yaml` to match your gym class schedule and system paths.

---

## Configuration

Configuration is loaded once by `Settings` (`src/settings/provider.py`) and validated with Pydantic — a malformed `.env` or YAML file fails fast with a readable error instead of surfacing as a `KeyError` deep in the automation flow.

### `.env`

```env
COMPENSAR_DOC_TYPE=CC
COMPENSAR_DOC_NUM=your_id_number
COMPENSAR_PASSWORD=your_password

TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id

# Optional: Firefox profile name (e.g. abc12345.gym-bot)
# FIREFOX_PROFILE_NAME=
```

### `src/settings/app_config.yaml`

```yaml
environment:
  login_url: https://seguridad.compensar.com/sign-in?...
  inside_system_url: https://sistemaplanbienestar.deportescompensar.com/...
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
```

---

## OS Integration

Full setup documentation for systemd services, timers, sudoers configuration, and RTC wake management is available in:

📄 [`doc/os_integration.md`](doc/os_integration.md)

This covers:

- sudoers rules for passwordless suspend (local and SSH)
- `gym-bot.timer` and `gym-bot.service` — triggers `main.py` every minute
- `power-autonomous.service` — runs power cycle on boot
- systemd-sleep hook — re-runs power cycle on every system resume
- USB wakeup source disabling (prevents premature wakeups)

### Execution flow

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

### Error recovery flow

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
src/utils/                           ← cross-cutting concerns (recovery, page waits, human behavior)
    ↓
src/settings/provider.py (Settings)  ← single source of truth for all config, typed via src/types/config.py
```

**Key design decisions:**

- **Dependency injection everywhere.** Every class takes its config and collaborators (typed Pydantic models, `Recovery`, `TelegramClient`) through its constructor. Nothing does `Settings()` or reads a global at import time — `main.py` is the only place that constructs `Settings` and wires the object graph.
- **Page Object pattern for browser automation.** Each `components/` class owns one step of the flow (`LoginPage`, `DateSelector`, `ClassBooker`, ...) and exposes a small, intention-revealing public method. `ReservationProcess` composes them into the full reservation sub-flow.
- **Typed configuration, not dicts.** `src/types/config.py` defines Pydantic models for every section of `.env` and the YAML files. Config errors surface at startup, with a readable validation message, instead of as a `KeyError`/`AttributeError` mid-flow.
- **Domain-specific exceptions.** All custom exceptions inherit from `GymBotError` (`src/utils/exceptions.py`), so recovery logic and logging can distinguish a missing element from a failed redirect from an unverifiable reservation, instead of catching bare `RuntimeError`.
- **All page interactions go through `Recovery.with_recovery` or `with_soft_recovery`** — no bare `try/except` swallowing errors in business logic.
- **Human behavior simulation is fully decoupled from automation logic** — `human_behavior.py` has no knowledge of login, reservations, or scheduling.
- **Power management is a separate concern** (`os_integration/`), triggered via its own CLI subcommands, not hardcoded into the reservation flow.

---

## Contributing

This is a personal project. Feel free to fork and adapt it for your own automation needs. The recovery system, human behavior layer, and power management integration are designed to be reusable across different web automation scenarios.

---

## License

Personal use. Not affiliated with Compensar or DeportesCompensar.
