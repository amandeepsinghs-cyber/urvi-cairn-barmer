"""R-6 (user, 2026-11-15): Urvi answers in English by default; Hindi / Hinglish only when the user switches."""
from __future__ import annotations

from app import settings
from app.agent import prompt
from app.live import session


def test_default_language_is_english():
    assert settings.DEFAULT_LANGUAGE == "english"


def test_text_prompt_defaults_to_english_and_explains_switching():
    text = prompt.render({})
    assert prompt.LANGUAGE_BLOCKS["english"] in text
    assert prompt.LANGUAGE_BLOCKS["hinglish"] not in text
    assert "LANGUAGE SWITCHING" in text and "English by default" in text


def test_live_prompt_defaults_to_english():
    assert session.norm_language(None) == "english"
    text = session._read_prompt()
    assert "speak English by default" in text
    # greeting example leads with English; Hinglish only as the alternative
    assert text.index("Hello! I am Urvi AI Agent") < text.index("Namaste! Main Urvi AI Agent hoon")
