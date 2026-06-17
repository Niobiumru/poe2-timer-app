# Project Standards: Quality & Stability Mandates

This document contains absolute mandates for all modifications to the PoE 2 Timer App. Adherence to these rules is required to prevent regressions and launch failures.

## 1. Integrity Verification (CRITICAL)
Before completing any task:
- **Syntax Check**: Run `python -m py_compile app/ui_main.py main.py`.
- **Runtime Dry-Run (Mandatory)**: Create a temporary test script (e.g., `test_launch.py`) that imports `MainWindow` and attempts to instantiate it within a `QApplication` block. This is the ONLY way to catch `AttributeError` and `NameError` before delivery.
- **Variable Scope**: All UI elements MUST be defined as `self.variable = ...` before `_load_settings()` or any signal connections are called.

## 2. UI Consistency Rules
- **Defensive UI Loading**: Never call methods that update UI text (like `_on_map_completed`) inside `_load_settings` unless you verify the widgets exist.
- **Seamless Backgrounds**: Maintain the deep dark background (#0b0f12 for window, #12181d for cards) without inconsistent borders or headers.
- **Safe Scaling**: When implementing font or window scaling, verify that text does not clip and layouts do not overlap. Use `setVisible()` instead of resizing elements to 0 where appropriate.
- **Mini Mode Integration**: Quick controls (S, M, L, FULL UI) must be integrated into the `info_bar` using the `miniBtn` object name for consistent styling.

## 3. Reliability
- **Launch Safety**: The application MUST be launchable via `python main.py` or `pythonw main.pyw` after every single file modification.
- **Graceful Failures**: If the log file is missing or sound cannot be played, the app must log the error to the UI (if in debug) or show a message box, but NEVER crash.
