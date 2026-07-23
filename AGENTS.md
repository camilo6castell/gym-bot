# AGENTS.md

## Quick Reference

```bash
# Run the bot (must be from project root)
python -m src.main                    # default: reserve classes
python -m src.main run                # explicit reservation flow
python -m src.main suspend-now        # program RTC wake + suspend
python -m src.main power-cycle        # manage full power cycle

# Type checking (both configured in pyproject.toml / pyrightconfig.json)
mypy src/
pyright

# Linting
ruff check src/
ruff format --check src/
```

## Architecture

Single composition root: `src/main.py` wires every dependency. No global state.

```
src/main.py → builds Settings → constructs all classes → runs CLI subcommand
src/bot/scheduler.py → resolves which classes to book
src/components/ → Page Object classes (one per browser step)
src/utils/ → cross-cutting: recovery, human behavior, logging, exceptions
src/settings/provider.py → loads .env + YAML, validates with Pydantic
```

**Dependency injection everywhere.** Every class takes collaborators through its constructor. `logger.py` is the one exception (self-configures at import time before `Settings` exists).

## Key Conventions

- **Domain exceptions:** `src/utils/exceptions.py` defines `GymBotError` hierarchy. Never raise `RuntimeError` in business logic.
- **Recovery wraps all page interactions:** Use `recovery.with_recovery()` or `recovery.with_soft_recovery()` — no bare `try/except` in components.
- **Code comments and logs are in Spanish** (matching the target platform's locale).
- **Page Object pattern:** Each `src/components/*.py` class owns one step. `ReservationProcess` composes them.
- **Config validation is strict:** `_StrictModel` base class in `src/types/config.py` has `extra="forbid"` — typos in YAML keys fail fast at startup.

## Configuration

| File | Purpose |
|------|---------|
| `.env` | Secrets: credentials, Telegram token/chat ID, log settings |
| `src/settings/schedule.yaml` | Weekly class schedule, timezone, forced class for testing |
| `src/settings/app_config.yaml` | URLs, browser paths, power settings, execution flags |

All loaded and validated by `Settings` (`src/settings/provider.py`).

## Testing

Pytest configured in `pyproject.toml` with `testpaths = ["tests"]`, but no tests exist yet. If adding tests, place them in `tests/`.

## Gotchas

- `python -m src.main` **must** run from the project root (`.env` loading, import paths depend on it)
- `suspend-now` and `power-cycle` require `sudo` for `systemctl suspend` and RTC wakealarm writes
- `power-cycle` uses `filelock` (`/tmp/gym-bot-power-cycle.lock`) to prevent concurrent runs
- Browser profile paths are derived from `~/.config/chromium` (or Firefox profile if configured)
- `logger.py` imports `.env` directly for `LOG_DIR`/`LOG_FILENAME`/`LOG_MAX_LINES` — runs before `Settings` is constructed
