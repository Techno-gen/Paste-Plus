from __future__ import annotations

import time
from typing import Optional

from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from paste_plus import __version__
from paste_plus.config import Config

# All UI output goes to stderr so doesn't pollute clipboard out
console = Console(stderr=True, highlight=False)

_BANNER_ART = (
    "    ____             __           \n"
    "   / __ \\____ ______/ /____    __ \n"
    "  / /_/ / __ `/ ___/ __/ _ \\__/ /_\n"
    " / ____/ /_/ (__  ) /_/  __/_  __/\n"
    "/_/    \\__,_/____/\\__/\\___/ /_/   "
)


# Actual display components

def show_banner(cfg: Config, source_label: str, dry_run: bool = False) -> None:
    """Print the splash banner + config summary."""
    art = _BANNER_ART

    # Art panel
    art_text = Text(art, style="bold cyan", justify="center")
    subtitle = Text(
        f"Typing Emulator  ·  v{__version__}",
        style="dim",
        justify="center",
    )
    header_text = Text.assemble(art_text, "\n", subtitle)

    if dry_run:
        mode_badge = Text(" DRY RUN ", style="bold black on yellow")
        header_text = Text.assemble(header_text, "  ", mode_badge)

    console.print(Panel(header_text, border_style="cyan", padding=(1, 4)))

    # Summary of configs
    table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    table.add_column(style="dim")
    table.add_column(style="bold white")

    table.add_row("WPM", f"{cfg.wpm} ± {cfg.wpm_variance}")
    table.add_row("Typo rate", _pct(cfg.typo_rate))
    table.add_row("Retype rate", _pct(cfg.retype_rate))
    table.add_row(
        "Pause freq",
        f"{_pct(cfg.pause_frequency)}  ({cfg.pause_min_seconds}s – {cfg.pause_max_seconds}s)",
    )
    table.add_row(
        "Post-hoc fixes",
        f"{_pct(cfg.posthoc_correction_rate)}  (max {cfg.posthoc_max_corrections})",
    )
    table.add_row("Input source", source_label)
    if cfg.trigger_key:
        table.add_row("Trigger key", cfg.trigger_key.upper())
    else:
        table.add_row("Startup delay", f"{cfg.startup_delay}s")

    console.print(Panel(table, title="[bold]Settings[/bold]", border_style="bright_black", padding=(0, 2)))


def show_trigger_prompt(key: str) -> None:
    """Block-style prompt waiting for the trigger key."""
    console.print()
    console.print(
        Panel(
            Text.assemble(
                "Focus your target window, then press ",
                Text(key.upper(), style="bold yellow"),
                " to begin typing…",
            ),
            border_style="yellow",
            padding=(1, 4),
        )
    )


def show_countdown(seconds: float) -> None:
    """Animated countdown rendered in-place."""
    total = int(seconds)

    with Live(console=console, refresh_per_second=4, transient=True) as live:
        for remaining in range(total, 0, -1):
            live.update(
                Panel(
                    Text.assemble(
                        "Switch to your target window — starting in ",
                        Text(f"{remaining}s", style="bold yellow"),
                        "…",
                    ),
                    border_style="yellow",
                    padding=(1, 4),
                )
            )
            time.sleep(1)

        frac = seconds - total
        if frac > 0:
            time.sleep(frac)

    # Brief GO flash
    console.print(
        Panel(
            Text("Typing now!", style="bold green", justify="center"),
            border_style="green",
            padding=(0, 4),
        )
    )


def show_ready() -> None:
    """Called immediately after trigger key is pressed."""
    console.print(
        Panel(
            Text("Typing now!", style="bold green", justify="center"),
            border_style="green",
            padding=(0, 4),
        )
    )


def show_typing_status(char_count: int, wpm: int) -> None:
    console.print(
        f"[dim]Typing [bold]{char_count}[/bold] chars  ·  ~[bold]{wpm}[/bold] WPM  ·  Ctrl+C to abort[/dim]"
    )


def show_posthoc_banner(count: int) -> None:
    console.print(f"[dim]  ↩  Applying [bold]{count}[/bold] post-hoc correction(s)…[/dim]")


def show_done(char_count: int) -> None:
    console.print()
    console.print(
        Panel(
            Text.assemble(
                Text("✓ ", style="bold green"),
                f"Done — ",
                Text(str(char_count), style="bold white"),
                " characters typed",
            ),
            border_style="green",
            padding=(0, 4),
        )
    )


def show_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_warning(message: str) -> None:
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"
