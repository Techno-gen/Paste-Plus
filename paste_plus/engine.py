from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional, Protocol

# QWERTY adjacency map to see where you can screw up

_ADJACENCY: dict[str, list[str]] = {
    "1": ["2", "q"],              "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],    "0": ["9", "-", "o", "p"],
    "-": ["0", "=", "p", "["],    "=": ["-", "[", "]"],

    "q": ["1", "2", "w", "a"],    "w": ["2", "3", "q", "e", "a", "s"],
    "e": ["3", "4", "w", "r", "s", "d"],  "r": ["4", "5", "e", "t", "d", "f"],
    "t": ["5", "6", "r", "y", "f", "g"],  "y": ["6", "7", "t", "u", "g", "h"],
    "u": ["7", "8", "y", "i", "h", "j"],  "i": ["8", "9", "u", "o", "j", "k"],
    "o": ["9", "0", "i", "p", "k", "l"],  "p": ["0", "-", "o", "[", "l", ";"],
    "[": ["-", "=", "p", "]", ";", "'"],  "]": ["=", "[", "'"],

    "a": ["q", "w", "s", "z"],    "s": ["a", "w", "e", "d", "z", "x"],
    "d": ["s", "e", "r", "f", "x", "c"], "f": ["d", "r", "t", "g", "c", "v"],
    "g": ["f", "t", "y", "h", "v", "b"], "h": ["g", "y", "u", "j", "b", "n"],
    "j": ["h", "u", "i", "k", "n", "m"], "k": ["j", "i", "o", "l", "m", ","],
    "l": ["k", "o", "p", ";", ",", "."], ";": ["l", "p", "[", "'", "."],
    "'": [";", "[", "]"],

    "z": ["a", "s", "x"],         "x": ["z", "s", "d", "c"],
    "c": ["x", "d", "f", "v"],    "v": ["c", "f", "g", "b"],
    "b": ["v", "g", "h", "n"],    "n": ["b", "h", "j", "m"],
    "m": ["n", "j", "k", ","],    ",": ["m", "k", "l", "."],
    ".": [",", "l", ";"],         "/": [".", ";", "'"],
}

_SAFE_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 `~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
)

def _adjacent(ch: str) -> list[str]:
    return [n for n in _ADJACENCY.get(ch.lower(), []) if n in _SAFE_CHARS]


# Main humanizer class

@dataclass
class TypoEvent:
    wrong_char: str
    correct_char: str

@dataclass
class RetypeEvent:
    length: int

@dataclass
class PauseEvent:
    duration: float


class Humanizer:
    def __init__(self, cfg, rng: Optional[random.Random] = None) -> None:
        self._cfg = cfg
        self._rng = rng or random.Random()

    def inter_key_delay(self) -> float:
        wpm = max(10, min(300, self._rng.gauss(self._cfg.wpm, self._cfg.wpm_variance)))
        return max(60.0 / (wpm * 5), self._cfg.inter_key_floor_ms / 1000.0)

    def maybe_typo(self, ch: str) -> Optional[TypoEvent]:
        if not ch.isalpha() or self._rng.random() >= self._cfg.typo_rate:
            return None
        neighbours = _adjacent(ch)
        return TypoEvent(wrong_char=self._rng.choice(neighbours), correct_char=ch) if neighbours else None

    def maybe_pause(self) -> Optional[PauseEvent]:
        if self._rng.random() >= self._cfg.pause_frequency:
            return None
        return PauseEvent(self._rng.uniform(self._cfg.pause_min_seconds, self._cfg.pause_max_seconds))

    def maybe_retype(self) -> Optional[RetypeEvent]:
        if self._rng.random() >= self._cfg.retype_rate:
            return None
        return RetypeEvent(self._rng.randint(self._cfg.retype_min_chars, self._cfg.retype_max_chars))

    def oops_pause(self) -> float:   return self._rng.uniform(0.05, 0.20)
    def fix_pause(self) -> float:    return self._rng.uniform(0.03, 0.10)
    def retype_oops(self) -> float:  return self._rng.uniform(0.08, 0.25)
    def retype_resume(self) -> float: return self._rng.uniform(0.05, 0.15)


# Keyboard backend interface + implementations

class KeyboardBackend(Protocol):
    def type_char(self, ch: str) -> None: ...
    def press_key(self, key: str) -> None: ...
    def hotkey(self, *keys: str) -> None: ...
    def sleep(self, seconds: float) -> None: ...


class PyautoguiKeyboard:
    def __init__(self, unicode_paste_fallback: bool = True) -> None:
        import pyautogui
        pyautogui.PAUSE = 0
        self._pag = pyautogui
        self._unicode_fallback = unicode_paste_fallback

    def type_char(self, ch: str) -> None:
        if ch == "\n":   self._pag.press("enter")
        elif ch == "\t": self._pag.press("tab")
        elif ch == "\b": self._pag.press("backspace")
        elif ord(ch) < 128:
            try:    self._pag.typewrite(ch, interval=0)
            except Exception: self._paste(ch)
        elif self._unicode_fallback:
            self._paste(ch)

    def press_key(self, key: str) -> None:  self._pag.press(key)
    def hotkey(self, *keys: str) -> None:   self._pag.hotkey(*keys)
    def sleep(self, seconds: float) -> None:
        if seconds > 0: time.sleep(seconds)

    def _paste(self, ch: str) -> None:
        import pyperclip
        old = pyperclip.paste()
        pyperclip.copy(ch)
        self._pag.hotkey("ctrl", "v")
        time.sleep(0.05)
        pyperclip.copy(old)


class DryRunKeyboard:
    def __init__(self) -> None:
        self.log: list[str] = []

    def type_char(self, ch: str) -> None:
        if ch == "\n":   self.press_key("enter")
        elif ch == "\t": self.press_key("tab")
        elif ch == "\b": self.press_key("backspace")
        else:
            e = f"TYPE {ch!r}"; self.log.append(e); print(e)

    def press_key(self, key: str) -> None:
        e = f"PRESS {key}"; self.log.append(e); print(e)

    def hotkey(self, *keys: str) -> None:
        e = f"HOTKEY {'+'.join(keys)}"; self.log.append(e); print(e)

    def sleep(self, seconds: float) -> None:
        e = f"SLEEP {seconds:.3f}s"; self.log.append(e); print(e)


# Post-hoc correction planning and execution

@dataclass
class _Correction:
    char_index: int
    wrong_char: str
    correct_char: str


class PosthocPlan:
    def __init__(self, text: str, cfg, rng: Optional[random.Random] = None) -> None:
        self._text = text
        self._cfg = cfg
        self._rng = rng or random.Random()
        self.corrections: list[_Correction] = []
        self.indices: set[int] = set()
        self._plan(text)

    def _plan(self, text: str) -> None:
        if not (self._cfg.posthoc_correction_rate > 0 and self._cfg.posthoc_max_corrections > 0):
            return
        candidates = [
            (i, ch) for i, ch in enumerate(text[: max(0, len(text) - 10)])
            if ch.isalpha() and _adjacent(ch)
        ]
        if not candidates:
            return
        n = min(int(len(candidates) * self._cfg.posthoc_correction_rate),
                self._cfg.posthoc_max_corrections)
        for idx, ch in self._rng.sample(candidates, min(n, len(candidates))):
            wrong = self._rng.choice(_adjacent(ch))
            self.corrections.append(_Correction(idx, wrong, ch))
            self.indices.add(idx)

    def execute(self, kb: KeyboardBackend, text_len: int, verbose: bool = False) -> None:
        if not self.corrections:
            return
        cursor = 0
        for c in sorted(self.corrections, key=lambda x: x.char_index, reverse=True):
            if verbose:
                from paste_plus import ui
                ui.console.print(
                    f"[dim]  post-hoc fix [red]{c.wrong_char!r}[/red] → "
                    f"[green]{c.correct_char!r}[/green] at {c.char_index}[/dim]"
                )
            kb.sleep(random.uniform(0.5, 2.0))
            # Navigate so cursor is right AFTER the wrong char, then backspace it
            target = text_len - c.char_index - 1
            for _ in range(target - cursor):
                kb.press_key("left"); kb.sleep(0.05)
            cursor = target
            kb.sleep(random.uniform(0.1, 0.3))
            kb.press_key("backspace"); kb.sleep(random.uniform(0.05, 0.15))
            kb.type_char(c.correct_char)
            # cursor distance from end stays the same (deleted one, typed one)
            kb.sleep(random.uniform(0.2, 0.6))
        if cursor > 0:
            kb.hotkey("ctrl", "end")


# Typing class that orchestrates the whole process

class TypingSession:
    def __init__(self, text: str, cfg, kb: KeyboardBackend, verbose: bool = False) -> None:
        self._text = text
        self._cfg = cfg
        self._kb = kb
        self._verbose = verbose
        self._h = Humanizer(cfg)
        self._plan = PosthocPlan(text, cfg)

    def run(self) -> None:
        self._start()
        from paste_plus import ui
        if self._verbose:
            ui.show_typing_status(len(self._text), self._cfg.wpm)

        i = 0
        while i < len(self._text):
            ch = self._text[i]
            if ch in (" ", "\n", "\t"):
                p = self._h.maybe_pause()
                if p:
                    if self._verbose: ui.console.print(f"[dim]  pause {p.duration:.2f}s[/dim]")
                    self._kb.sleep(p.duration)
                r = self._h.maybe_retype()
                if r and i + 1 + r.length < len(self._text):
                    # Type the space first, then retype the next chunk
                    self._kb.sleep(self._h.inter_key_delay())
                    self._kb.type_char(ch)
                    self._retype(i + 1, r.length)
                    i += 1 + r.length  # skip past space + retyped chars
                    continue

            self._kb.sleep(self._h.inter_key_delay())

            if i in self._plan.indices:
                c = next(x for x in self._plan.corrections if x.char_index == i)
                if self._verbose:
                    ui.console.print(f"[dim]  posthoc-plant [yellow]{c.wrong_char!r}[/yellow] at {i}[/dim]")
                self._kb.type_char(c.wrong_char)
            elif ch.isalpha():
                t = self._h.maybe_typo(ch)
                if t:
                    if self._verbose:
                        ui.console.print(f"[dim]  typo [red]{t.wrong_char!r}[/red] → backspace → [green]{t.correct_char!r}[/green][/dim]")
                    self._kb.type_char(t.wrong_char)
                    self._kb.sleep(self._h.oops_pause())
                    self._kb.press_key("backspace")
                    self._kb.sleep(self._h.fix_pause())
                    self._kb.type_char(t.correct_char)
                else:
                    self._kb.type_char(ch)
            else:
                self._kb.type_char(ch)
            i += 1

        if self._plan.corrections:
            if self._verbose: ui.show_posthoc_banner(len(self._plan.corrections))
            self._plan.execute(self._kb, len(self._text), verbose=self._verbose)

        ui.show_done(len(self._text))

    def _retype(self, start: int, length: int) -> None:
        seg = self._text[start : start + length]
        if self._verbose:
            from paste_plus import ui
            ui.console.print(f"[dim]  retype {seg!r}[/dim]")
        for ch in seg:
            self._kb.sleep(self._h.inter_key_delay()); self._kb.type_char(ch)
        self._kb.sleep(self._h.retype_oops())
        for _ in seg:
            self._kb.press_key("backspace"); self._kb.sleep(0.04)
        self._kb.sleep(self._h.retype_resume())
        for ch in seg:
            self._kb.sleep(self._h.inter_key_delay()); self._kb.type_char(ch)

    def _start(self) -> None:
        from paste_plus import ui
        if self._cfg.trigger_key:
            ui.show_trigger_prompt(self._cfg.trigger_key)
            try:
                import keyboard as kb_lib
                kb_lib.wait(self._cfg.trigger_key)
                kb_lib.unhook_all()
                ui.show_ready()
            except ImportError:
                ui.show_warning("'keyboard' not installed — falling back to 3s delay. pip install keyboard")
                self._cfg.trigger_key = None
                self._cfg.startup_delay = 3.0
                ui.show_countdown(self._cfg.startup_delay)
            except Exception as e:
                ui.show_warning(f"Could not listen for trigger key: {e}")
        elif self._cfg.startup_delay > 0:
            ui.show_countdown(self._cfg.startup_delay)
