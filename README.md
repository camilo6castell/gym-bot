# gym-bot

> Autonomous gym class reservation bot with OS-level power management, human behavior simulation, and Telegram-based remote error recovery.

---

## Overview

**gym-bot** is a Python automation system designed to handle recurring gym class reservations on the [Compensar / DeportesCompensar](https://deportescompensar.com) platform — fully unattended.

Beyond simple task scheduling, the bot integrates deeply with the Linux operating system to manage the machine's power cycle autonomously: it suspends the host between reservation windows, wakes it up precisely before each booking, executes the reservation, and suspends again — all without human intervention.

When errors occur, the bot does not crash silently. It notifies you via Telegram, pauses execution, and waits for your remote command to resume or retry — giving you a 10-minute intervention window to diagnose and resolve any issue from anywhere.

---

## Key Features

### 🤖 Intelligent Automation
- Schedule-driven reservation engine that reads a YAML configuration and calculates the correct booking window (reservations open 2 days in advance)
- Force-run mode for manual, on-demand execution with a specific class, hour, and day
- Post-reservation verification: navigates to the user's upcoming sessions page and confirms the booking was recorded correctly

### 🧠 Human Behavior Simulation
Designed to avoid bot detection through realistic interaction patterns:
- Variable mouse trajectories with randomized steps and micro-deviations
- Randomized click offsets within element bounding boxes
- Typing simulation with per-character delays and occasional typo-and-correction sequences
- Random scroll amounts and directions between interactions
- Non-uniform delays between all actions

### 🛡️ Anti-Detection (Browser Stealth)
- Uses the user's real Chromium profile (cookies, history, extensions)
- Removes automation flags (`--enable-automation`, `AutomationControlled`)
- Injects JavaScript to mask `navigator.webdriver`, spoof plugins, and emulate real browser fingerprint
- Geolocation set to Bogotá, Colombia

### 🔁 Layered Error Recovery
Two recovery mechanisms handle failures at different severity levels:

**`with_soft_recovery`** — Silent auto-retry for transient failures (configurable retries with delay between attempts).

**`with_recovery`** — Full recovery pipeline for critical failures:
1. Automatically reloads the page and retries up to 2 times
2. If the error persists, sends a Telegram notification and pauses execution
3. Waits up to 10 minutes for a remote command:
   - `0` → Resume from current state
   - `1` → Refresh page and retry
4. If no response within the timeout, aborts gracefully

**CAPTCHA detection** is handled as a special case — any detected CAPTCHA immediately triggers a Telegram alert without attempting auto-retries, since human intervention is always required.

### 💤 OS-Level Power Management
The bot integrates with the Linux kernel to manage the host machine's power state autonomously:

- Reads the class schedule and computes the next reservation timestamp
- Programs the system's **RTC wakealarm** (`/sys/class/rtc/rtc0/wakealarm`) to wake the machine minutes before the booking window
- Suspends the system via `systemctl suspend`
- On resume, a **systemd-sleep hook** re-executes the scheduler to program the next cycle

This enables the host to remain suspended (consuming near-zero power) between reservation cycles, waking only when needed.

### 📲 Telegram Notifications
- Real-time error alerts with full context (action name, error message, retry count)
- Interactive remote control: resume, refresh, or abort — directly from your phone
- Confirmation messages for successful reservations

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Browser Automation | Playwright (sync API) |
| Scheduling | systemd user timers |
| Power Management | RTC wakealarm + systemd-sleep hooks |
| Notifications | Telegram Bot API |
| Configuration | `.env` + YAML |
| Logging | Loguru |
| Timezone handling | pytz |

---

## Project Structure

```
gym-bot/
├── main.py                         # Entry point — orchestrates the full reservation flow
│
├── bot/                            # Browser automation layer
│   ├── browser.py                  # Chromium launcher with stealth configuration
│   ├── login.py                    # Login flow with CAPTCHA detection
│   ├── logout.py                   # Session cleanup
│   ├── day_selector_handler.py     # Selects the correct booking date
│   ├── gym_class_selector_handler.py  # Finds and selects the target class
│   ├── gym_class_confirmation_handler.py  # Confirms the selected class
│   ├── gym_class_verification_handler.py  # Verifies the booking was recorded
│   └── reserve_gym_class.py        # Orchestrates the full reservation sub-flow
│
├── components/
│   ├── bot_run.py                  # Decides force-run vs schedule-run, returns class list
│   ├── membership.py               # Opens the membership plan before booking
│   └── add_a_minute_for_x.py      # Optional timing offset for execution window
│
├── core/
│   ├── env.py                      # Centralized environment variable loading
│   ├── env_utils.py                # Helpers for type-safe env parsing
│   └── classes.yaml                # Weekly class schedule configuration
│
├── utils/
│   ├── recovery.py                 # with_recovery / with_soft_recovery / Telegram control loop
│   ├── human_behavior.py           # Mouse, click, typing, scroll simulation
│   ├── page_utils.py               # Page waits, CAPTCHA detection, URL management
│   ├── error_broadcast.py          # Screenshot + Telegram error notification
│   ├── exceptions.py               # Custom exceptions (CaptchaDetectedError)
│   ├── element_utils.py            # Text normalization for robust element matching
│   ├── time_utils.py               # Time format conversion utilities
│   ├── logger.py                   # Loguru configuration
│   └── days_handler.py             # Day name mapping (EN ↔ ES, weekday index)
│
├── notifications/
│   └── telegram.py                 # notify() and getUpdates() wrappers
│
├── os_integration/
│   ├── os_integration_utils.py     # find_next_reservation(), set_wake_alarm(), suspend()
│   ├── power_autonomous.py         # Full autonomous power cycle manager
│   └── start_power_autonomous.py   # Lightweight entry point for alias / systemd
│
└── doc/
    └── LINUX_integration-and-initialization-os-integration_power-optimization.md
```

---

## Configuration

### `.env`

```env
# Authentication
LOGIN_URL=https://seguridad.compensar.com/sign-in?...
POST_LOGIN_URL=https://sistemaplanbienestar.deportescompensar.com/...
GYM_CLASS_VERIFICATION_URL=https://sistemared.deportescompensar.com/...

COMPENSAR_DOC_TYPE=CC
COMPENSAR_DOC_NUM=your_id
COMPENSAR_PASSWORD=your_password

# Bot behavior
BOT_HEADLESS=true
ADDITIONAL_MINUTE_FOR_EXECUTION=false

# Force run (optional override)
BOT_FORCE_RUN=false
BOT_FORCE_RUN_CLASS=Pilates
BOT_FORCE_RUN_HOUR=06:00 - 07:00
BOT_FORCE_RUN_DAY=monday

# Telegram
TOKEN=your_bot_token
CHAT_ID=your_chat_id

# Power management
WAKEALARM_PATH=/sys/class/rtc/rtc0/wakealarm
WAKE_MINUTES_BEFORE=2
SLEEP_MINUTES_AFTER=10
```

### `core/classes.yaml`

```yaml
timezone: America/Bogota
days:
  monday:
    - name: Pilates
      hour: "06:00 - 07:00"
  wednesday:
    - name: Estiramiento
      hour: "06:00 - 07:00"
    - name: Pilates
      hour: "07:00 - 08:00"
```

> Classes are booked 2 days in advance. A Monday entry triggers on Saturday.

---

## How It Works

```
RTC wakealarm fires
       ↓
systemd-sleep hook triggers power_autonomous.py
       ↓
gym-bot.timer fires main.py every minute
       ↓
main.py evaluates schedule → finds matching class
       ↓
Launches Chromium with real user profile
       ↓
Login → Navigate → Select date → Select class → Confirm → Verify
       ↓
Telegram: "✅ Reservation complete"
       ↓
power_autonomous.py programs next RTC wake → suspends
```

If anything fails along the way:

```
Exception raised
       ↓
Auto-refresh x2 (silent)
       ↓
Telegram alert → wait up to 10 min
       ↓
User sends 0 (resume) or 1 (refresh)
       ↓
Bot continues
```

---

## OS Integration Setup

See [`doc/LINUX_integration-and-initialization-os-integration_power-optimization.md`](doc/LINUX_integration-and-initialization-os-integration_power-optimization.md) for the full setup guide, including:

- sudoers configuration for passwordless suspend
- systemd service and timer definitions
- systemd-sleep hook for post-resume scheduler execution
- USB wakeup source disabling (prevents premature wakeups from connected devices)
- Shell alias for manual trigger

---

## Broader Application

While built for a specific fitness platform, the architecture is designed with reusability in mind. The same patterns apply to any web-based reservation or form automation scenario:

- **Human behavior layer** is fully decoupled from the bot logic
- **Recovery system** is generic — any `Callable` can be wrapped
- **Power management** works with any Linux machine and any scheduled task
- **Telegram control loop** provides a universal remote intervention interface

This makes gym-bot a practical reference implementation for building robust, autonomous, OS-integrated Python automation systems.

---

## Requirements

```
playwright==1.57.0
loguru==0.7.3
python-dotenv==1.2.1
pytz==2025.2
PyYAML==6.0.3
requests
```

Install dependencies and Playwright browsers:

```bash
pip install -r requeriments.txt
playwright install chromium
```

---

## License

Personal use. Not affiliated with Compensar or DeportesCompensar.
