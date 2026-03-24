import json
import random

import pytest

from paste_plus.config import Config, apply_overrides, load_config
from paste_plus.engine import (
    DryRunKeyboard, Humanizer, PosthocPlan, TypingSession, _adjacent,
)


# ── Config ────────────────────────────────────────────────────────────────────

def test_config_defaults():
    cfg = Config()
    assert cfg.wpm == 80
    assert cfg.typo_rate == 0.04
    assert cfg.fail_safe is True

def test_config_validate_bad_rate():
    with pytest.raises(ValueError, match="typo_rate"):
        Config(typo_rate=1.5).validate()

def test_config_validate_pause_range():
    with pytest.raises(ValueError, match="pause_min"):
        Config(pause_min_seconds=3.0, pause_max_seconds=1.0).validate()

def test_apply_overrides_skips_none():
    cfg = Config()
    apply_overrides(cfg, {"wpm": None, "typo_rate": 0.1})
    assert cfg.wpm == 80
    assert cfg.typo_rate == 0.1

def test_load_config_from_file(tmp_path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"wpm": 120}))
    assert load_config(str(f)).wpm == 120


# ── Adjacency ─────────────────────────────────────────────────────────────────

def test_all_letters_have_adjacents():
    for ch in "abcdefghijklmnopqrstuvwxyz":
        assert _adjacent(ch), f"No adjacents for {ch!r}"

def test_adjacent_returns_list():
    assert isinstance(_adjacent("a"), list) and len(_adjacent("a")) > 0

def test_adjacent_uppercase_normalises():
    assert _adjacent("a") == _adjacent("A")

def test_adjacent_unknown_char():
    assert _adjacent("€") == []


# ── Humanizer ─────────────────────────────────────────────────────────────────

def _h(seed=42, **kw):
    return Humanizer(Config(**kw), random.Random(seed))

def test_inter_key_delay_at_fixed_wpm():
    delay = _h(wpm=80, wpm_variance=0).inter_key_delay()
    assert abs(delay - 60.0 / (80 * 5)) < 0.001

def test_inter_key_delay_floor():
    assert _h(wpm=80, wpm_variance=0, inter_key_floor_ms=500).inter_key_delay() >= 0.5

def test_typo_never_at_zero():
    assert all(_h(typo_rate=0.0).maybe_typo("a") is None for _ in range(100))

def test_typo_always_at_one():
    t = _h(typo_rate=1.0).maybe_typo("a")
    assert t and t.correct_char == "a" and t.wrong_char != "a"

def test_typo_non_alpha_is_none():
    h = _h(typo_rate=1.0)
    assert h.maybe_typo(" ") is None and h.maybe_typo("1") is None

def test_pause_never_at_zero():
    assert all(_h(pause_frequency=0.0).maybe_pause() is None for _ in range(100))

def test_pause_duration_in_range():
    h = _h(pause_frequency=1.0, pause_min_seconds=0.5, pause_max_seconds=1.0)
    for _ in range(20):
        p = h.maybe_pause()
        assert p and 0.5 <= p.duration <= 1.0

def test_retype_never_at_zero():
    assert all(_h(retype_rate=0.0).maybe_retype() is None for _ in range(100))

def test_retype_length_in_range():
    h = _h(retype_rate=1.0, retype_min_chars=3, retype_max_chars=6)
    for _ in range(20):
        r = h.maybe_retype()
        assert r and 3 <= r.length <= 6


# ── Post-hoc corrections ──────────────────────────────────────────────────────

def _plan(text, rate=1.0, max_c=5, seed=1):
    return PosthocPlan(text, Config(posthoc_correction_rate=rate, posthoc_max_corrections=max_c),
                       random.Random(seed))

def test_no_corrections_at_zero_rate():
    p = _plan("hello world", rate=0.0)
    assert not p.corrections

def test_corrections_capped():
    assert len(_plan("the quick brown fox jumps", rate=1.0, max_c=2).corrections) <= 2

def test_corrections_not_in_last_10():
    text = "abcdefghijklmnop"
    for c in _plan(text, rate=1.0, max_c=10).corrections:
        assert c.char_index < len(text) - 10

def test_execute_uses_left_and_delete():
    p = _plan("hello world", rate=1.0, max_c=1)
    if not p.corrections: return
    kb = DryRunKeyboard()
    p.execute(kb, len("hello world"))
    assert any("PRESS left" in e for e in kb.log)
    assert any("PRESS delete" in e for e in kb.log)

def test_no_corrections_short_text():
    assert not _plan("hi", rate=1.0).corrections


# ── Typing session ────────────────────────────────────────────────────────────

def _run(text, **kw):
    cfg = Config(startup_delay=0, **kw)
    kb = DryRunKeyboard()
    TypingSession(text, cfg, kb).run()
    return kb

def test_plain_text_all_chars_typed():
    kb = _run("hello", typo_rate=0, retype_rate=0, pause_frequency=0, posthoc_correction_rate=0)
    typed = "".join(e.split("TYPE ")[1].strip("'") for e in kb.log if e.startswith("TYPE"))
    assert typed == "hello"

def test_typo_produces_backspace():
    assert any("PRESS backspace" in e for e in _run("aaaa", typo_rate=1.0, retype_rate=0,
                                                     pause_frequency=0, posthoc_correction_rate=0).log)

def test_pause_produces_long_sleep():
    kb = _run("hello world", typo_rate=0, retype_rate=0, pause_frequency=1.0,
              pause_min_seconds=0.5, pause_max_seconds=0.5, posthoc_correction_rate=0)
    assert any(float(e.split()[1].rstrip("s")) >= 0.4 for e in kb.log if e.startswith("SLEEP"))

def test_newline_becomes_enter():
    assert "PRESS enter" in _run("a\nb", typo_rate=0, retype_rate=0,
                                  pause_frequency=0, posthoc_correction_rate=0).log

def test_empty_text_no_crash():
    TypingSession("", Config(startup_delay=0), DryRunKeyboard()).run()
