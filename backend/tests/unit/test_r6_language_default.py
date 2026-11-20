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
    # C-R7: no accent/prosody roleplay instruction that causes gemini-3.8-live to resample voice each turn
    assert "accent" not in text.lower() and "prosody" not in text.lower()
    # C-R7: supports Punjabi and any Indian regional / native language
    assert "Punjabi" in text and "regional or native language" in text


def test_live_config_unlocked_for_regional_languages_and_area_queries_do_not_pop_charts():
    from google.genai import types
    from app.live import voice_tools

    cfg = session.build_live_config(types, "sys", [], None, "Aoede", "english")
    # C-R8: English keeps the Indian English locale (Indian accent); the voice stays one fixed prebuilt voice
    assert cfg.speech_config.language_code == "en-IN"
    assert cfg.speech_config.voice_config.prebuilt_voice_config.voice_name == "Aoede"
    assert session.build_live_config(types, "sys", [], None, "Aoede", "hindi").speech_config.language_code == "hi-IN"
    assert session.build_live_config(types, "sys", [], None, "Aoede", "punjabi").speech_config.language_code == "pa-IN"
    # Languages without a verified Live locale stay unlocked so the model auto-detects them
    assert session.build_live_config(types, "sys", [], None, "Aoede", "assamese").speech_config.language_code is None
    assert session.norm_language("Punjabi") == "punjabi" and session.norm_language("klingon") == "english"

    # Area overview uses fleet_kpis without hijacking the map screen
    assert voice_tools.VOICE_TOOLS["fleet_kpis"].action_kind is None
    kpis = voice_tools.execute_voice_tool("fleet_kpis", {}, "ASSET_MANAGER")
    assert kpis["status"] == "OK"
    assert len(kpis.get("india_operating_areas") or []) >= 4
    assert len(kpis.get("barmer_fields") or []) == 4

    # field_production_history defaults to plot=False (tell numbers verbally without popping chart)
    res_no_plot = voice_tools.execute_voice_tool("field_production_history", {}, "ASSET_MANAGER")
    assert res_no_plot["plot"] is False
    res_plot = voice_tools.execute_voice_tool("field_production_history", {"plot": True}, "ASSET_MANAGER")
    assert res_plot["plot"] is True
