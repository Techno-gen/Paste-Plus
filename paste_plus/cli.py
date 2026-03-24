from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from paste_plus import __version__, ui
from paste_plus.config import Config, apply_overrides, load_config
from paste_plus.engine import DryRunKeyboard, PyautoguiKeyboard, TypingSession


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "--version")
@click.argument("file", required=False, default=None)
@click.option("-f", "--file", "file_opt", default=None, help="Text file to type.")
@click.option("-c", "--clipboard", "use_clipboard", is_flag=True, help="Read from clipboard.")
@click.option("-s", "--stdin", "use_stdin", is_flag=True, help="Read from stdin.")
@click.option("--wpm", default=None, type=int, help="Words per minute.")
@click.option("--wpm-variance", default=None, type=int, help="WPM standard deviation.")
@click.option("--typo-rate", default=None, type=float, help="Per-char typo probability (0–1).")
@click.option("--retype-rate", default=None, type=float, help="Per-word retype probability (0–1).")
@click.option("--pause-freq", default=None, type=float, help="Per-word pause probability (0–1).")
@click.option("--pause-min", default=None, type=float, help="Min pause seconds.")
@click.option("--pause-max", default=None, type=float, help="Max pause seconds.")
@click.option("--posthoc-rate", default=None, type=float, help="Fraction of typos corrected post-hoc.")
@click.option("--delay", default=None, type=float, help="Startup delay in seconds.")
@click.option("--trigger-key", default=None, type=str, help="Key to press to start typing (e.g. f9).")
@click.option("--config", "config_path", default=None, help="Path to config.json.")
@click.option("--dry-run", is_flag=True, help="Print actions instead of typing.")
@click.option("--no-fail-safe", is_flag=True, help="Disable pyautogui corner abort.")
@click.option("-v", "--verbose", is_flag=True, help="Show timing events on stderr.")
def main(
    file: Optional[str], file_opt: Optional[str],
    use_clipboard: bool, use_stdin: bool,
    wpm: Optional[int], wpm_variance: Optional[int],
    typo_rate: Optional[float], retype_rate: Optional[float],
    pause_freq: Optional[float], pause_min: Optional[float], pause_max: Optional[float],
    posthoc_rate: Optional[float], delay: Optional[float], trigger_key: Optional[str],
    config_path: Optional[str], dry_run: bool, no_fail_safe: bool, verbose: bool,
) -> None:
    """Paste-Plus: emulate human typing from clipboard, stdin, or a file."""
    resolved_file = file or file_opt

    try:
        cfg = load_config(config_path)
    except (ValueError, FileNotFoundError) as e:
        ui.show_error(f"Loading config: {e}"); sys.exit(1)

    apply_overrides(cfg, {
        "wpm": wpm, "wpm_variance": wpm_variance, "typo_rate": typo_rate,
        "retype_rate": retype_rate, "pause_frequency": pause_freq,
        "pause_min_seconds": pause_min, "pause_max_seconds": pause_max,
        "posthoc_correction_rate": posthoc_rate, "startup_delay": delay,
        "trigger_key": trigger_key,
        "fail_safe": (not no_fail_safe) if no_fail_safe else None,
    })

    try:
        cfg.validate()
    except ValueError as e:
        ui.show_error(f"Invalid config: {e}"); sys.exit(1)

    try:
        text, source_label = _read_input(resolved_file, use_clipboard, use_stdin)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        ui.show_error(f"Input: {e}"); sys.exit(1)

    if not text:
        ui.show_error("No text to type."); sys.exit(1)

    ui.show_banner(cfg, source_label=source_label, dry_run=dry_run)

    if dry_run:
        kb = DryRunKeyboard()
    else:
        _check_windows()
        try:
            import pyautogui
        except ImportError:
            ui.show_error("pyautogui not installed. Run: pip install pyautogui"); sys.exit(1)
        if not cfg.fail_safe:
            pyautogui.FAILSAFE = False
        kb = PyautoguiKeyboard()

    try:
        TypingSession(text, cfg, kb, verbose=verbose).run()
    except KeyboardInterrupt:
        ui.console.print("\n[bold red]Interrupted.[/bold red]")
        sys.exit(130)


def _read_input(
    file: Optional[str], use_clipboard: bool, use_stdin: bool
) -> tuple[str, str]:
    if file:
        p = Path(file)
        if not p.exists(): raise FileNotFoundError(f"File not found: {file}")
        return p.read_text(encoding="utf-8"), f"file: {file}"
    if use_clipboard:
        return _from_clipboard(), "clipboard"
    if use_stdin:
        return _from_stdin(), "stdin"
    if not sys.stdin.isatty():
        return _from_stdin(), "stdin (piped)"
    return _from_clipboard(), "clipboard (auto)"


def _from_clipboard() -> str:
    try:
        import pyperclip
        text = pyperclip.paste()
    except Exception as e:
        raise RuntimeError(f"Could not read clipboard: {e}") from e
    if not text: raise ValueError("Clipboard is empty. Copy some text first.")
    return text


def _from_stdin() -> str:
    text = sys.stdin.read()
    if not text: raise ValueError("stdin was empty.")
    return text


def _check_windows() -> None:
    import platform
    if platform.system() != "Windows":
        ui.show_warning("paste-plus is designed for Windows. Keystroke emulation may not work on this OS.")
    try:
        import ctypes, platform as _p
        if _p.system() == "Windows" and not ctypes.windll.shell32.IsUserAnAdmin():
            ui.show_warning("Running without admin rights — keystrokes can't reach UAC-elevated windows.")
    except Exception:
        pass
