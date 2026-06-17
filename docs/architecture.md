# PoE 2 Timer App - Architecture & Context

## 🤖 AI Agent Quick Context
**Application:** Path of Exile 2 Map Timer Monitor.
**Tech Stack:** Python 3, PySide6 (Qt for Python).
**Layout:** Standard Python `app-layout` (`main.py` at root, logic in `app/`).
**Core Mechanism:** The app monitors the game's `Client.txt` log file in real-time. It uses a background thread (`QRunnable` via `QThreadPool`) to parse incoming lines without blocking the UI. Communication between the background thread and the UI is strictly handled via **Qt Signals and Slots**.
**UI/UX:** The GUI uses frameless windows and native Qt styling via CSS. It includes a "Mini Mode" which dynamically hides UI elements and shrinks the window, using negative margins to tightly wrap around typography.
**Rules for AI:** 
- NEVER block the main UI thread. 
- All cross-thread communication MUST use `Signal.emit()`.
- Do not add external heavy dependencies (like `pandas` or `requests`) unless specifically requested; keep the app lightweight.
- Ensure strict error handling in the parser; game log formats can change.

---

## 📂 Directory Structure
```
poe2_timer_app/
├── docs/                # Project documentation and AI context
├── app/                 # Main application package
│   ├── __init__.py      
│   ├── config_manager.py # JSON read/write logic
│   ├── log_watcher.py    # Background file tailing (QRunnable)
│   ├── parser_logic.py   # Regex/String parsing for game events
│   ├── sound_manager.py  # Audio playback using QtMultimedia
│   ├── timer_logic.py    # QTimer management and state tracking
│   └── ui_main.py        # PySide6 MainWindow and UI layouts
├── tests/               # Validation and testing scripts
│   ├── test_launch.py    # Dry-run script to verify UI instantiates
│   └── validate_logic.py # Unit tests for parser and timer rules
├── main.py              # Application entry point (Console)
├── main.pyw             # Application entry point (Windowed/No-Console)
├── config.json          # User settings (generated at runtime)
├── GEMINI.md            # Hard constraints and specific project rules
└── requirements.txt     # Python dependencies
```

## 🧩 Core Modules Explained

### 1. `app/ui_main.py`
The primary View layer. Constructs the `MainWindow` class inheriting from `QMainWindow`. Responsible for:
- Building all visual layouts, buttons, cards, and input fields.
- Switching between Full Mode and Mini Mode.
- Displaying timer updates, log tables, and color gradients.
- Routing user interactions (clicks, settings changes) to appropriate logical components.

### 2. `app/timer_logic.py`
The central Controller for time-based logic. Inherits from `QObject` to utilize Signals.
- Manages instances of `QTimer` (re-entry countdown and area elapsed time).
- Holds state regarding `last_instance_id` and `pending_instance_id` to determine when to reset or pause timers.
- Emits ticks (`reentry_tick`, `area_tick`) consumed by `ui_main.py` for rendering.

### 3. `app/log_watcher.py`
The Data ingress layer. Inherits from `QRunnable`.
- Runs in a separate thread.
- Tails the Path of Exile `Client.txt` file continuously.
- Feeds new lines into `parser_logic.py`.
- Emits structured event dictionaries to the main thread via a `LogSignals` object.

### 4. `app/parser_logic.py`
The parsing engine.
- Contains string matching and regex logic.
- Converts raw strings like `[DEBUG Client 55380] Generating level 79 area "MapIceCave"` into actionable dictionaries: `{"type": "area", "value": "MapIceCave"}`.

### 5. `app/config_manager.py` & `app/sound_manager.py`
Utility classes.
- **ConfigManager:** Abstracted layer to read/write settings safely to `config.json`.
- **SoundManager:** Abstracted wrapper around `QSoundEffect` to play `.wav` or `.mp3` alerts when the re-entry timer finishes.
