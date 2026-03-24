```
    ____             __           
   / __ \____ ______/ /____    __ 
  / /_/ / __ `/ ___/ __/ _ \__/ /_
 / ____/ /_/ (__  ) /_/  __/_  __/
/_/    \__,_/____/\__/\___/ /_/   
```
### A command line utility designed to bypass annoying copy/paste history protections.
Paste Plus emulates keystrokes, pauses, grammatical errors, and fixes, to simulate a real person typing.

## Features
- **Transposition typos**(teh instead of the)
- **Double-strike errors**(helllo)
- **Shift key mistakes**
- **Per-word WPM scaling**
- **"Burst" mode**(occasional fast runs followed by normal to slow typing speed)
- **Watch clipboard for changes and auto-type when new content is copied**
- **Allows for multi-file input**(typing several files in sequence)
- **Preview mode**(show humanized text diff before typing)
- **Many choices for configuration**

---

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

> **Windows only.** Keystroke emulation via `pyautogui` requires a display and may not reach UAC-elevated windows without running as Administrator.

---
