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

Two recovery mechanisms handle failures at different severity levels:

**`with_soft_recovery`** — silent auto-retry for transient failures, configurable retries with delay between attempts.

**`with_recovery`** — full recovery pipeline for critical failures:

1. Automatically reloads the page and retries up to N times
2. If the error persists, sends a Telegram notification and pauses execution
3. Waits for a remote command via Telegram:
   - `0` → Resume from current state
   - `1` → Refresh page and retry
4. If no response within the timeout, aborts gracefully

**CAPTCHA detection** is treated as a special case — any detected active CAPTCHA immediately triggers a Telegram alert without auto-retries, since human intervention is always required.

### 💤 OS-Level Power Management

The bot integrates with the Linux kernel to manage the host machine's power state autonomously:

- Reads the class schedule and computes the next reservation timestamp
- Programs the system's **RTC wakealarm** to wake the machine minutes before the booking window
- Suspends the system via `systemctl suspend`
- A **systemd-sleep hook** re-executes the power cycle manager on every resume

This enables the host to remain suspended (near-zero power consumption) between reservation cycles.

### 📲 Telegram Integration

- Real-time error alerts with full context (action name, error message, retry count)
- Interactive remote control: resume, refresh, or abort directly from your phone
- Reservation confirmation messages

### ✅ Post-Reservation Verification

After each reservation, the bot navigates to the user's upcoming sessions page and confirms the booking was recorded correctly — raising an error and triggering recovery if not found.

---

## Tech Stack

| Layer              | Technology                          |
| ------------------ | ----------------------------------- |
| Language           | Python 3.11+                        |
| Browser Automation | Playwright (sync API)               |
| Scheduling         | systemd user timers                 |
| Power Management   | RTC wakealarm + systemd-sleep hooks |
| Notifications      | Telegram Bot API                    |
| Configuration      | `.env` + YAML                       |
| Logging            | Loguru                              |
| Timezone handling  | pytz                                |
| CLI                | argparse                            |

---

## Project Structure

```
gym-bot/
├── src/                            # Main application source
│   ├── main.py                     # Single entry point with subcommands
│   ├── config/
│   │   ├── config.py               # Centralized configuration loader
│   │   ├── app_config.yaml         # App settings (URLs, selectors, power, browser)
│   │   └── schedule.yaml           # Weekly class schedule
│   ├── bot/
│   │   ├── browser.py              # Chromium/Firefox launcher with stealth config
│   │   └── scheduler.py            # Schedule evaluation, force-run vs regular-run
│   ├── components/
│   │   ├── login.py                # Login flow with CAPTCHA detection
│   │   ├── logout.py               # Session cleanup
│   │   ├── post_login.py           # Post-login navigation flow
│   │   ├── membership.py           # Membership/tiquetera selection
│   │   ├── day_selector.py         # Booking date selection
│   │   ├── gym_class_booker.py     # Class search and selection
│   │   ├── gym_class_acceptance.py # Reservation confirmation modal
│   │   ├── gym_class_checker.py    # Post-reservation verification
│   │   └── reserve_process.py      # Orchestrates the full reservation sub-flow
│   ├── notifications/
│   │   └── telegram.py             # notify() and getUpdates() wrappers
│   ├── os_integration/
│   │   ├── os_integration_utils.py # RTC alarm, suspend, next reservation finder
│   │   └── power_cycle.py          # Power management commands
│   └── utils/
│       ├── exceptions.py           # Custom exceptions (CaptchaDetectedError)
│       ├── logger.py               # Loguru configuration
│       ├── strings.py              # Text normalization utilities
│       ├── time_utils.py           # Time format conversion, day mapping
│       ├── human_behavior.py       # Mouse, click, typing, scroll simulation
│       ├── page_utils.py           # Page waits, CAPTCHA detection, URL management
│       ├── recovery.py             # with_recovery / with_soft_recovery
│       └── error_broadcast.py      # Screenshot + Telegram error notification
├── debug/                          # Auto-generated screenshots on error (gitignored)
├── doc/
│   └── os_integration.md           # Full OS integration setup guide
├── .env                            # Secrets and credentials (gitignored)
├── .env.example                    # Template for environment variables
└── requirements.txt
```

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

```bash
cp .env.example .env
# Edit .env with your credentials
```

**5. Configure your schedule and app settings**

Edit `src/config/schedule.yaml` and `src/config/app_config.yaml` to match your gym class schedule and system paths.

---

## Configuration

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

### `src/config/app_config.yaml`

```yaml
environment:
  login_url: https://seguridad.compensar.com/sign-in?...
  inside_system_url: https://sistemaplanbienestar.deportescompensar.com/...
  inside_system_url_pattern: "**deportescompensar.com/**"

os:
  home_user: "~"
  chromium_path: /usr/bin/chromium
  firefox_path: /usr/bin/firefox

power_autonomous:
  wake_minutes_before: 2
  sleep_minutes_after: 10
  wakealarm_path: /sys/class/rtc/rtc0/wakealarm

execution:
  bot_force_run: false
  execution_adjustment: -1 # minutes offset for booking trigger
  bot_headless: false
```

### `src/config/schedule.yaml`

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

Set `bot_force_run: true` and configure `forcedClass` in `app_config.yaml`, then:

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
Evaluates schedule → finds matching class
       ↓
Launches browser → Login → Navigate → Select date
       ↓
Select class → Confirm → Verify booking
       ↓
Telegram: "✅ Reservation complete"
       ↓
power-cycle programs next RTC wake → suspends
```

### Error recovery flow

```
Exception raised in any step
       ↓
Auto-refresh × 2 (silent)
       ↓
Telegram alert → wait up to 10 minutes
       ↓
User replies: 0 (resume) or 1 (refresh & retry)
       ↓
Bot continues from current state
```

---

## Architecture

The project follows a **layered architecture** with a single entry point:

```
src/main.py                 ← entry point, CLI subcommands
    ↓
src/bot/scheduler.py        ← decides what to run and when
    ↓
src/components/             ← browser automation steps
    ↓
src/utils/                  ← cross-cutting concerns
    ↓
src/config/config.py        ← single source of truth for all config
```

**Key design decisions:**

- `Config` is instantiated once per module using an absolute path — never relative to `cwd`
- All page interactions go through `with_recovery` or `with_soft_recovery` — no bare try/except in business logic
- Human behavior simulation is fully decoupled from automation logic
- Power management is a separate concern triggered via CLI subcommands, not hardcoded into the bot flow

---

## Contributing

This is a personal project. Feel free to fork and adapt it for your own automation needs. The recovery system, human behavior layer, and power management integration are designed to be reusable across different web automation scenarios.

---

## License

Personal use. Not affiliated with Compensar or DeportesCompensar.
