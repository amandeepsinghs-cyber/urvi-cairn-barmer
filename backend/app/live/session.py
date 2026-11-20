"""app/live/session.py — Gemini Live proxy behind ``WS /ws/live`` (SDD §11.3-11.4, BDD F-07).

Port of the ADK repo's ``agent/live/live_session.py`` (itself a port of Drilling Intelligence 2.0
``backend/app/agent/live_session.py``, ADR-003)::

    browser WS --(one reader task)--> inbound queue --> current Gemini Live session
                                                   \\--> text fallback (after 6 failures)

* The Gemini session can be replaced (GoAway / drop) without dropping the browser socket.
* Reconnects reuse the latest ``SessionResumptionConfig`` handle, keep sliding-window context
  compression on, and send a **recap** of past turns so memory survives (BDD-F07-S03).
* After 2 consecutive failures the handle is dropped (a stale handle can be the cause); after 6 (exponential
  back-off, C-R10) the client gets ``status: fallback`` and prompts are answered by ``app.live.fallback``
  (BDD-F07-S04); the browser then retries voice every 20 s.
* Tool calls run the registered ``voice_tools`` in a worker thread with a 10 s timeout.
* The language toggle (english / hinglish / hindi) is a LANGUAGE block in the system instruction at
  connect time and a context line on change (SDD §11.6). Voice never speaks ₹ / USD (D-1).

All per-connection state lives in a local ``state`` dict (no module-level mutable state, SDD §12.4).

Configuration (env; ``WELLPULSE_*`` wins, ``WORKOVER_*`` accepted as alias):
  WELLPULSE_LIVE_MODEL     verified via ``python -m app.live.verify_model`` (Stage U: gemini-3.8-live)
  WELLPULSE_LIVE_LOCATION  default us-central1 (gemini-3.8-live is not served from ``global``)
  WELLPULSE_LIVE_PROJECT   default GOOGLE_CLOUD_PROJECT, then urvi-cairn-barmer-ai-agent
  WELLPULSE_LIVE_VOICE     default Aoede (DI 2.0; D-42 kept the female voice)
  WELLPULSE_LIVE_OFFLINE   1 => skip Gemini, go straight to text fallback
  WELLPULSE_DEBUG_RECONNECT 1 => accept {"type":"debug_reconnect"} to force a resume (tests / demo)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.live import voice_tools

logger = logging.getLogger("wellpulse.live.session")

DEFAULT_LIVE_MODEL = "gemini-3.8-live"  # verified 2026-10-07 by models.list + live.connect (us-central1)
DEFAULT_LIVE_LOCATION = "us-central1"
DEFAULT_PROJECT = "urvi-cairn-barmer-ai-agent"
MAX_CONSECUTIVE_FAILURES = 6  # C-R10: ride out transient Vertex 1006 drops (~15 s of back-off) before text fallback
DROP_HANDLE_AFTER = 2
MAX_BACKOFF_S = 8.0
RECAP_KEEP_FIRST = 4
RECAP_KEEP_LAST = 16
RECAP_MAX_CHARS = 320
MAX_REASK = 2  # C9.10: re-ask an unanswered question at most twice after a mid-answer drop
REASK_NOTE = "[The connection dropped before you finished answering. Answer this again, briefly and in full.]"
BLIP_CAPTION = " … (connection blip — answering again)"
GIVE_UP_CAPTION = " … (connection lost — please ask again)"
LANGUAGES = (
    "english", "hinglish", "hindi", "punjabi", "rajasthani", "gujarati", "marathi", "bengali", "assamese", "odia",
    "tamil", "telugu", "kannada", "malayalam", "urdu",
)
# C-R8: Gemini Live speech locale per language. English / Hinglish use Indian English (en-IN) so the voice keeps an
# Indian accent. Every locale below connected and answered in its language on gemini-3.8-live (probe 2026-11-19,
# scratch/probe_locales.py). Rajasthani, Assamese, Odia and Urdu stay unlocked (None) and are auto-detected.
SPEECH_LOCALES: dict[str, str | None] = {
    "english": "en-IN", "hinglish": "en-IN", "hindi": "hi-IN", "punjabi": "pa-IN", "gujarati": "gu-IN",
    "marathi": "mr-IN", "bengali": "bn-IN", "tamil": "ta-IN", "telugu": "te-IN", "kannada": "kn-IN",
    "malayalam": "ml-IN",
}
PROMPT_PATH = Path(__file__).with_name("live_prompt.md")
LANGUAGE_MARKER = "## LANGUAGE BLOCKS"

_CLOSED = object()  # sentinel pushed on the inbound queue when the browser disconnects

# connect_factory(model, config) -> async context manager yielding a Live session
ConnectFactory = Callable[[str, Any], Any]


# ---------------------------------------------------------------------------
# Settings + prompt
# ---------------------------------------------------------------------------
def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(f"WELLPULSE_{name}") or os.getenv(f"WORKOVER_{name}") or default


def live_settings() -> dict[str, Any]:
    return {
        "model": _env("LIVE_MODEL", DEFAULT_LIVE_MODEL),
        "location": _env("LIVE_LOCATION", DEFAULT_LIVE_LOCATION),
        "project": _env("LIVE_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or DEFAULT_PROJECT,
        "voice": _env("LIVE_VOICE", "Aoede"),
        "offline": _env("LIVE_OFFLINE", "0") == "1",
        "debug_reconnect": _env("DEBUG_RECONNECT", "0") == "1",
        "backoff_s": float(_env("LIVE_BACKOFF_S", "0.5") or 0.5),
        "tool_timeout_s": float(_env("LIVE_TOOL_TIMEOUT_S", str(voice_tools.TOOL_TIMEOUT_S)) or 10),
    }


def norm_language(lang: str | None) -> str:
    lang = (lang or "english").strip().lower()
    return lang if lang in LANGUAGES else "english"


def _read_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        return (
            "You are Urvi AI Agent (voice) for Cairn Oil & Gas, Barmer. Every number you speak must come "
            "from a tool result in the same turn. Never speak rupee or dollar figures. 1-3 short sentences."
        )


def language_block(lang: str) -> str:
    """The ``### <lang>`` subsection under ``## LANGUAGE BLOCKS`` in live_prompt.md."""
    text = _read_prompt()
    _, _, blocks = text.partition(LANGUAGE_MARKER)
    lang = norm_language(lang)
    for chunk in blocks.split("### ")[1:]:
        head, _, body = chunk.partition("\n")
        if head.strip().lower() == lang:
            return body.strip()
    return (f"Speak natural, fluent {lang.title()} with captions in its native script; oilfield technical terms may "
            f"stay in English. Use feminine first-person forms where the language is gendered. Every number spoken "
            f"must come directly from tool outputs.")


def build_system_prompt(ui: dict[str, Any] | None) -> str:
    ui = ui or {}
    base = _read_prompt().partition(LANGUAGE_MARKER)[0].strip()
    lang = norm_language(ui.get("language"))
    parts = [base, f"## LANGUAGE ({lang})\n{language_block(lang)}"]
    ctx = _context_line(ui)
    if ctx:
        parts.append(f"## SESSION CONTEXT\n{ctx}")
    return "\n\n".join(parts)


def speech_language_code(lang: str | None) -> str | None:
    """BCP-47 Gemini Live locale for a language (en-IN for English / Hinglish); None = unlocked auto-detect."""
    return SPEECH_LOCALES.get(norm_language(lang))


def build_live_config(
    types: Any, system_prompt: str, tools: list[Any], handle: str | None, voice: str, language: str | None = "english"
) -> Any:
    """LiveConnectConfig: one fixed prebuilt voice, per-language speech locale (Indian English by default)."""
    code = speech_language_code(language)
    speech = types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)),
        **({"language_code": code} if code else {}),
    )
    return types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        temperature=0.2,
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=types.Content(parts=[types.Part.from_text(text=system_prompt)]),
        tools=tools,
        speech_config=speech,
        session_resumption=types.SessionResumptionConfig(handle=handle),
        context_window_compression=types.ContextWindowCompressionConfig(sliding_window=types.SlidingWindow()),
    )


def _default_connect_factory(settings: dict[str, Any]) -> ConnectFactory:
    from google import genai

    client = genai.Client(vertexai=True, project=settings["project"], location=settings["location"])

    def factory(model: str, config: Any) -> Any:
        return client.aio.live.connect(model=model, config=config)

    return factory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _send(ws: WebSocket, payload: dict[str, Any]) -> bool:
    try:
        await ws.send_json(payload)
        return True
    except Exception:
        return False


def _log_turn(state: dict[str, Any], role: str, text: str) -> None:
    text = " ".join((text or "").split())
    if text:
        state.setdefault("log", []).append((role, text[:RECAP_MAX_CHARS]))


def recap_turns(state: dict[str, Any], types: Any) -> list[Any] | None:
    """Past turns re-sent after reconnect as alternating user/model history (not one blob)."""
    log = state.get("log") or []
    if not log:
        return None
    if len(log) > RECAP_KEEP_FIRST + RECAP_KEEP_LAST:
        lines = log[:RECAP_KEEP_FIRST] + log[-RECAP_KEEP_LAST:]
    else:
        lines = list(log)
    turns: list[Any] = []
    for role, text in lines:
        r = "model" if role == "Agent" else "user"
        if turns and turns[-1].role == r:
            turns[-1].parts.append(types.Part.from_text(text=text))
        else:
            turns.append(types.Content(role=r, parts=[types.Part.from_text(text=text)]))
    if turns and turns[0].role == "user":
        turns[0].parts.insert(0, types.Part.from_text(text="[Earlier in this conversation — history only]"))
    return turns


def _context_line(ui: dict[str, Any] | None) -> str:
    if not ui:
        return ""
    bits = []
    for key in ("field", "well_id", "persona", "screen"):
        if ui.get(key):
            bits.append(f"{key}={ui[key]}")
    if ui.get("language"):
        bits.append(f"language={norm_language(ui['language'])}")
    return f"[UI context] {', '.join(bits)}" if bits else ""


def _summarize(result: dict[str, Any]) -> str:
    s = json.dumps(result, default=str, ensure_ascii=False)
    return s if len(s) <= 400 else s[:397] + "..."


def _merge_ui(state: dict[str, Any], ui_state: Any) -> bool:
    """Merge a ui_state dict; returns True if the language changed."""
    if not isinstance(ui_state, dict):
        return False
    before = norm_language(state["ui"].get("language"))
    state["ui"] = {**state["ui"], **{k: v for k, v in ui_state.items() if v is not None}}
    return norm_language(state["ui"].get("language")) != before


async def _run_tool(ws: WebSocket, name: str, args: dict[str, Any], state: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    """Execute a voice tool off the event loop (10 s timeout) and emit tool_call/action events."""
    persona = state["ui"].get("persona")
    await _send(ws, {"type": "tool_call", "name": name, "status": "running", "args": args})
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(voice_tools.execute_voice_tool, name, args, persona), timeout=timeout_s
        )
    except TimeoutError:
        result = {"status": "UNAVAILABLE", "message": "timeout", "duration_ms": round(timeout_s * 1000)}
    await _send(
        ws,
        {
            "type": "tool_call",
            "name": name,
            "status": "done",
            "args": args,
            "duration_ms": result.get("duration_ms"),
            "result_summary": _summarize(result),
            "result": result,
        },
    )
    tool = voice_tools.VOICE_TOOLS.get(name)
    emit_action = bool(tool and tool.action_kind and result.get("status") == "OK")
    if name == "field_production_history" and not (args or {}).get("plot"):
        emit_action = False  # BDD-F11-S01: tell numbers first; open chart only when user asks for plot/chart
    if name == "ui_control" and result.get("status") == "OK":
        cmd = (result.get("data") or {}).get("command") if isinstance(result.get("data"), dict) else None
        if isinstance(cmd, dict) and cmd.get("action") == "language" and cmd.get("value"):
            before = speech_language_code(state["ui"].get("language"))
            state["ui"]["language"] = norm_language(cmd["value"])
            if speech_language_code(state["ui"]["language"]) != before:
                state["relocale"] = True  # C-R8: reconnect on the new speech locale after this reply finishes
    if emit_action and tool:
        await _send(ws, {"type": "action", "kind": tool.action_kind, "payload": result})
    return result


def initial_ui_from_query(websocket: WebSocket) -> dict[str, Any]:
    q = websocket.query_params
    ui = {k: q.get(k) for k in ("field", "well_id", "persona", "screen", "language") if q.get(k)}
    ui["language"] = norm_language(ui.get("language"))
    return ui


# ---------------------------------------------------------------------------
# C-R10: voice session continuity across browser sockets. Cloud Run ends every WebSocket after 60 min and networks
# blip; the browser reconnects with the same ?sid= and we resume the Gemini session (handle + recap) instead of
# starting from zero. Bounded, short-lived store (one instance, D-16): at most 200 sessions, 30 min after last use.
# ---------------------------------------------------------------------------
_PARKED: dict[str, dict[str, Any]] = {}
PARK_TTL_S = 1800.0
PARK_MAX = 200


def _sid(websocket: WebSocket) -> str:
    sid = (websocket.query_params.get("sid") or "").strip()
    return sid if 8 <= len(sid) <= 64 and sid.replace("-", "").isalnum() else ""


def park_session(sid: str, state: dict[str, Any]) -> None:
    if not sid:
        return
    _PARKED[sid] = {"handle": state.get("handle"), "resumable": state.get("resumable", False),
                    "log": list(state.get("log") or [])[-(RECAP_KEEP_FIRST + RECAP_KEEP_LAST):],
                    "pending": state.get("pending"), "t": time.monotonic()}
    if len(_PARKED) > PARK_MAX:
        for k in sorted(_PARKED, key=lambda k: _PARKED[k]["t"])[: len(_PARKED) - PARK_MAX]:
            _PARKED.pop(k, None)


def unpark_session(sid: str) -> dict[str, Any] | None:
    if not sid:
        return None
    p = _PARKED.pop(sid, None)
    if not p or time.monotonic() - p["t"] > PARK_TTL_S:
        return None
    return p


# ---------------------------------------------------------------------------
# C9.10: a Gemini Live drop (Vertex 1006 / GoAway) in the middle of an answer used to lose that answer — the user saw
# a partial caption and heard nothing until they asked again. The question being answered is kept in
# state["pending"] until its real turn_complete; after the reconnect it is asked again (at most MAX_REASK times).
# ---------------------------------------------------------------------------
def _set_pending(state: dict[str, Any], text: str, voice: bool) -> None:
    text = " ".join((text or "").split())
    if text:
        state["pending"] = {"text": text, "voice": voice}


def _clear_pending(state: dict[str, Any]) -> None:
    state.pop("pending", None)
    state.pop("reask_tries", None)
    state.pop("caption_open", None)


async def reask_pending(websocket: WebSocket, session: Any, state: dict[str, Any], types: Any) -> bool:
    """After a reconnect, ask the unanswered question again. Returns True if it was re-sent."""
    pending = state.get("pending")
    if not pending:
        return False
    tries = state["reask_tries"] = state.get("reask_tries", 0) + 1
    text = pending["text"]
    give_up = tries > MAX_REASK or (pending.get("voice") and len(text.split()) < 2)
    if state.pop("caption_open", False):  # close the half-shown reply bubble so the next answer gets its own
        await _send(websocket, {"type": "caption_delta", "text": GIVE_UP_CAPTION if give_up else BLIP_CAPTION, "role": "agent"})
        await _send(websocket, {"type": "turn_complete", "full_text": ""})
    if give_up:
        logger.warning("Gemini Live dropped turn NOT re-asked (try %d, voice=%s): %r", tries, pending.get("voice"), text[:80])
        _clear_pending(state)
        return False
    logger.info("Gemini Live dropped mid-answer — re-asking (try %d, voice=%s): %r", tries, pending.get("voice"), text[:80])
    line = _context_line(state["ui"])
    body = f"{REASK_NOTE}\n{text}"
    await session.send_client_content(
        turns=[types.Content(role="user", parts=[types.Part.from_text(text=f"{line}\n{body}" if line else body)])],
        turn_complete=True,
    )
    await _send(websocket, {"type": "voice_state", "state": "thinking"})
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def handle_live_websocket(websocket: WebSocket, connect_factory: ConnectFactory | None = None) -> None:
    """Entry point for /ws/live. ``connect_factory`` is injectable for tests (fake sessions)."""
    await websocket.accept()
    settings = live_settings()
    inbound: asyncio.Queue = asyncio.Queue()
    state: dict[str, Any] = {"handle": None, "resumable": False, "ui": initial_ui_from_query(websocket), "log": []}
    sid = _sid(websocket)
    parked = unpark_session(sid)
    if parked:  # C-R10: same browser session reconnecting -> resume the Gemini session and its memory
        state.update(handle=parked["handle"], resumable=parked["resumable"], log=parked["log"], restored=True)
        if parked.get("pending"):
            state["pending"] = parked["pending"]  # C9.10: the browser socket died mid-answer -> answer it on resume
    t_open = time.monotonic()
    logger.info("live socket open sid=%s restored=%s lang=%s", sid or "-", bool(parked), state["ui"].get("language"))

    async def browser_reader() -> None:
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                await inbound.put(msg)
        except (WebSocketDisconnect, RuntimeError):
            pass
        except Exception as e:  # pragma: no cover - defensive
            logger.error("browser_reader error: %s", e)
        finally:
            await inbound.put(_CLOSED)

    reader_task = asyncio.create_task(browser_reader())
    try:
        if settings["offline"] and connect_factory is None:
            await _send(websocket, {"type": "status", "status": "fallback", "model": "text", "memory": False,
                                    "message": "WELLPULSE_LIVE_OFFLINE=1 — text mode."})
            await run_fallback_session(websocket, inbound, state)
            return
        await run_resilient_live(websocket, inbound, settings, state, connect_factory)
    finally:
        park_session(sid, state)
        logger.info("live socket closed sid=%s after %.0f s (turns logged=%d)", sid or "-",
                    time.monotonic() - t_open, len(state.get("log") or []))
        reader_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await reader_task


async def run_resilient_live(
    websocket: WebSocket,
    inbound: asyncio.Queue,
    settings: dict[str, Any],
    state: dict[str, Any],
    connect_factory: ConnectFactory | None = None,
) -> None:
    try:
        from google.genai import types

        tools = voice_tools.build_genai_tools(state["ui"].get("persona"))
        if connect_factory is None:
            connect_factory = _default_connect_factory(settings)
    except Exception as e:  # broken setup must degrade, not kill the socket
        logger.error("Live setup failed: %s: %s", type(e).__name__, e)
        await _send(websocket, {"type": "status", "status": "fallback", "model": "text", "memory": False,
                                "message": f"Gemini Live setup error ({type(e).__name__}) — switched to text."})
        await run_fallback_session(websocket, inbound, state)
        return

    model = settings["model"]
    failures = 0
    ever_connected = bool(state.get("restored"))  # C-R10: a restored browser session resumes (handle + recap)
    while True:
        handle = state["handle"] if state["resumable"] else None
        resuming = ever_connected
        await _send(websocket, {"type": "status", "status": "reconnecting" if resuming else "connecting", "model": model})
        try:
            # Rebuilt each connect so a language/persona change is honoured on resume.
            config = build_live_config(
                types, build_system_prompt(state["ui"]), tools, handle, settings["voice"], state["ui"].get("language")
            )
            logger.info("Gemini Live connect model=%s resume=%s", model, bool(handle))
            async with connect_factory(model, config) as session:
                failures = 0
                recap = recap_turns(state, types) if resuming else None
                await _send(websocket, {"type": "status", "status": "resumed" if resuming else "connected",
                                        "model": model, "memory": bool(handle) or bool(recap)})
                ever_connected = True
                if recap:
                    try:
                        await session.send_client_content(turns=recap, turn_complete=False)
                    except Exception as e:  # recap is best-effort
                        logger.warning("Recap send failed: %s", e)
                if resuming:
                    await reask_pending(websocket, session, state, types)
                reason = await _run_bidi_stream(websocket, session, inbound, state, settings)
            logger.info("Gemini Live session ended: %s", reason)
            if reason == "browser_closed":
                return
            continue  # go_away / server_closed -> resume with latest handle
        except Exception as e:
            failures += 1
            logger.warning("Gemini Live failure %d/%d: %s: %s", failures, MAX_CONSECUTIVE_FAILURES, type(e).__name__, e)
            if failures >= MAX_CONSECUTIVE_FAILURES:
                logger.warning("Gemini Live FALLBACK to text after %d failures: %s", failures, type(e).__name__)
                await _send(websocket, {"type": "status", "status": "fallback", "model": "text", "memory": bool(state["log"]),
                                        "message": f"Gemini Live unavailable ({type(e).__name__}) — switched to text."})
                await run_fallback_session(websocket, inbound, state)
                return
            if failures >= DROP_HANDLE_AFTER:
                state["resumable"] = False
            await asyncio.sleep(min(MAX_BACKOFF_S, settings["backoff_s"] * (2 ** (failures - 1))))


async def _run_bidi_stream(
    websocket: WebSocket, session: Any, inbound: asyncio.Queue, state: dict[str, Any], settings: dict[str, Any]
) -> str:
    """Pump one Gemini session. Returns 'browser_closed' | 'go_away' | 'server_closed'.

    Raises on unexpected upstream errors so the caller can count failures.
    """
    from google.genai import types

    state.pop("go_away_pending", None)

    async def send_context(prefix: str = "") -> None:
        line = _context_line(state["ui"])
        if not line:
            return
        lang = norm_language(state["ui"].get("language"))
        text = f"{line}\n{prefix}" if prefix else line
        if prefix:
            text += f"\nLANGUAGE ({lang}): {language_block(lang)}"
        await session.send_client_content(
            turns=[types.Content(role="user", parts=[types.Part.from_text(text=text)])], turn_complete=False
        )

    async def client_to_gemini() -> str:
        while True:
            message = await inbound.get()
            if message is _CLOSED:
                return "browser_closed"
            if message.get("bytes"):
                await session.send_realtime_input(audio=types.Blob(data=message["bytes"], mime_type="audio/pcm;rate=16000"))
                continue
            if not message.get("text"):
                continue
            try:
                data = json.loads(message["text"])
            except json.JSONDecodeError:
                continue
            mtype = data.get("type")
            locale_before = speech_language_code(state["ui"].get("language"))
            lang_changed = _merge_ui(state, data.get("ui_state"))
            if lang_changed and speech_language_code(state["ui"].get("language")) != locale_before:
                if mtype == "context":
                    return "language_changed"  # C-R8: reconnect (resume handle + recap) on the new speech locale
                state["relocale"] = True  # a prompt carried the switch: answer it, then reconnect after the reply
            if mtype == "context":
                await send_context("[Language switched — use the new language from now on.]" if lang_changed else "")
            elif mtype in ("prompt", "text"):
                text = str(data.get("text", ""))
                _log_turn(state, "User", text)
                _clear_pending(state)
                _set_pending(state, text, voice=False)
                await _send(websocket, {"type": "voice_state", "state": "thinking"})
                line = _context_line(state["ui"])
                full = f"{line}\n{text}" if line else text
                await session.send_client_content(
                    turns=[types.Content(role="user", parts=[types.Part.from_text(text=full)])], turn_complete=True
                )
            elif mtype == "audio_end":
                await session.send_realtime_input(audio_stream_end=True)
            elif mtype == "interrupt":
                # Client already stopped playback (barge-in); Gemini VAD interrupts on new speech.
                await _send(websocket, {"type": "interrupted"})
                await _send(websocket, {"type": "voice_state", "state": "listening"})
            elif mtype == "debug_reconnect" and settings.get("debug_reconnect"):
                return "go_away"

    async def gemini_to_client() -> str:
        caption: list[str] = []
        turn_output = False
        tool_since_output = False
        while True:
            got_any = False
            async for response in session.receive():
                got_any = True
                sru = getattr(response, "session_resumption_update", None)
                if sru is not None and getattr(sru, "resumable", False) and getattr(sru, "new_handle", None):
                    state["handle"] = sru.new_handle
                    state["resumable"] = True
                if getattr(response, "go_away", None) is not None:
                    logger.info("Gemini Live GoAway (time_left=%s) answer_in_progress=%s",
                                getattr(response.go_away, "time_left", None), bool(state.get("pending")))
                    if not state.get("pending"):
                        return "go_away"
                    state["go_away_pending"] = True  # C9.10: let the current answer finish, then reconnect
                    continue

                tc = getattr(response, "tool_call", None)
                if tc is not None:
                    tool_since_output = True
                    await _send(websocket, {"type": "voice_state", "state": "thinking"})
                    responses = []
                    for fc in tc.function_calls or []:
                        args = dict(fc.args or {})
                        result = await _run_tool(websocket, fc.name, args, state, settings["tool_timeout_s"])
                        _log_turn(state, "Tool", f"{fc.name} -> {_summarize(result)}")
                        responses.append(types.FunctionResponse(name=fc.name, response={"result": result}, id=fc.id))
                    await session.send_tool_response(function_responses=responses)

                sc = getattr(response, "server_content", None)
                if sc is None:
                    continue
                if getattr(sc, "interrupted", False):
                    # C-R10 telemetry: was Urvi cut off mid-reply (barge-in or her own voice echoed into the mic)?
                    logger.info("Gemini Live interrupted while_speaking=%s heard=%r", bool(state.get("speaking")),
                                "".join(state.get("heard") or [])[:80])
                    state["speaking"] = False
                    _clear_pending(state)  # barge-in: the user moved on; their new words become the pending question
                    await _send(websocket, {"type": "interrupted"})
                it = getattr(sc, "input_transcription", None)
                if it is not None and getattr(it, "text", None):
                    state.setdefault("heard", []).append(it.text)
                    if not (state.get("pending") and not state["pending"].get("voice")):
                        _set_pending(state, "".join(state["heard"]), voice=True)
                    await _send(websocket, {"type": "input_transcript", "text": it.text})
                ot = getattr(sc, "output_transcription", None)
                if ot is not None and getattr(ot, "text", None):
                    turn_output = True
                    state["caption_open"] = True
                    caption.append(ot.text)
                    await _send(websocket, {"type": "caption_delta", "text": ot.text, "role": "agent"})
                mt = getattr(sc, "model_turn", None)
                if mt is not None:
                    for part in mt.parts or []:
                        inline = getattr(part, "inline_data", None)
                        if inline is not None and inline.data:
                            if not state.get("speaking"):
                                state["speaking"] = True
                                await _send(websocket, {"type": "voice_state", "state": "speaking"})
                            turn_output = True
                            await websocket.send_bytes(inline.data)
                if getattr(sc, "turn_complete", False):
                    if not turn_output and tool_since_output:
                        continue  # swallow the empty turn_complete Gemini emits right after a tool call
                    turn_output = False
                    tool_since_output = False
                    state["speaking"] = False
                    full_text = "".join(caption).strip()
                    caption = []
                    heard = "".join(state.pop("heard", [])).strip()
                    if heard:
                        _log_turn(state, "User", heard)
                    _log_turn(state, "Agent", full_text)
                    await _send(websocket, {"type": "turn_complete", "full_text": full_text})
                    await _send(websocket, {"type": "voice_state", "state": "idle"})
                    if state.get("reask_tries"):
                        logger.info("Gemini Live re-asked turn answered (words=%d)", len(full_text.split()))
                    _clear_pending(state)
                    if state.pop("relocale", False):
                        return "language_changed"
                    if state.pop("go_away_pending", False):
                        return "go_away"
            if not got_any:
                return "server_closed"

    async def guarded() -> str:
        try:
            return await gemini_to_client()
        except Exception as e:
            with contextlib.suppress(Exception):
                from websockets.exceptions import ConnectionClosedOK

                if isinstance(e, ConnectionClosedOK):
                    return "server_closed"
            if " 1000 " in f" {e} " or " 1001 " in f" {e} ":
                return "server_closed"
            raise

    t1 = asyncio.create_task(client_to_gemini())
    t2 = asyncio.create_task(guarded())
    done, pending = await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
    for p in pending:
        p.cancel()
    for p in pending:
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await p
    return done.pop().result()


# ---------------------------------------------------------------------------
# Fallback: text turns via app.live.fallback (Stage V swaps in the ADK Runner)
# ---------------------------------------------------------------------------
async def run_fallback_session(websocket: WebSocket, inbound: asyncio.Queue, state: dict[str, Any]) -> None:
    from app.live import fallback

    await _send(websocket, {"type": "voice_state", "state": "idle"})
    warned_audio = False
    while True:
        msg = await inbound.get()
        if msg is _CLOSED:
            return
        if msg.get("bytes"):
            if not warned_audio:
                warned_audio = True
                await _send(websocket, {"type": "error", "message": "Gemini Live unavailable — text mode: type your question."})
            continue
        if not msg.get("text"):
            continue
        try:
            data = json.loads(msg["text"])
        except json.JSONDecodeError:
            continue
        _merge_ui(state, data.get("ui_state"))
        if data.get("type") not in ("prompt", "text"):
            continue
        text = str(data.get("text", ""))
        _log_turn(state, "User", text)
        await _send(websocket, {"type": "voice_state", "state": "thinking"})
        reply = await fallback.answer_text_async(text, dict(state["ui"]), list(state["log"]))
        reply_text = voice_tools.strip_money(str(reply.get("text", "")))
        _log_turn(state, "Agent", reply_text)
        await _send(websocket, {"type": "fallback_reply", "text": reply_text,
                                "recommendation": voice_tools.strip_money(reply.get("recommendation")),
                                "artifacts": voice_tools.to_json_safe(voice_tools.strip_money(reply.get("artifacts") or [])),
                                "actions": voice_tools.to_json_safe(reply.get("actions") or []),
                                "engine": reply.get("engine", "text-fallback")})
        await _send(websocket, {"type": "caption_delta", "text": reply_text, "role": "agent"})
        await _send(websocket, {"type": "turn_complete", "full_text": reply_text})
        await _send(websocket, {"type": "voice_state", "state": "idle"})
