```
    ____             __           
   / __ \____ ______/ /____    __ 
  / /_/ / __ `/ ___/ __/ _ \__/ /_
 / ____/ /_/ (__  ) /_/  __/_  __/
/_/    \__,_/____/\__/\___/ /_/   
```
### A command line utility designed to bypass annoying copy/paste history protections.
Paste Plus emulates keystrokes, pauses, grammatical errors, and fixes to simulate a real person typing.

## Features
- Transposition typos (teh instead of the)
- Double-strike errors (helllo)
- Shift key mistakes
- Per-word WPM scaling
- "Burst" mode (occasional fast runs followed by normal to slow typing speed)
- Watch clipboard for changes and auto-type when new content is copied
- Allows for multi-file input (typing several files in sequence)
- Preview mode(show humanized text diff before typing)
- Many choices for configuration

---

## Installation

### Build from source
```bash
git clone https://github.com/Techno-gen/Paste-Plus
cd Paste-Plus
pip install -r requirements.txt
pip install -e .
```

### Prebuilt install
Simply download the executable from the releases page and run it normally. Keep in mind that the app will close when the text is written.

> **Windows only.** Keystroke emulation via `pyautogui` requires a display and may not reach UAC-elevated windows without running as Administrator.

## Usage

```bash
# Type from clipboard (default) — press F9 to start
# Think of this like an alternative paste button, you just have to have paste-plus running in the background.
paste-plus

# Type from a file
paste-plus myfile.txt

# Type from stdin
echo "Hello world" | paste-plus

# Adjust speed and typo rate
paste-plus --wpm 120 --typo-rate 0.08 myfile.txt

# Preview without typing
paste-plus --dry-run myfile.txt

# Use a countdown instead of trigger key
paste-plus --trigger-key "" --delay 5
```

Run `paste-plus -h` for the full list of options.

## Screenshots
<img src="https://github.com/Techno-gen/Paste-Plus/blob/main/Screenshots/Homepage.png" width="75%">
<img src="https://github.com/Techno-gen/Paste-Plus/blob/main/Screenshots/Starthisgif.gif" width="50%"><br/>
