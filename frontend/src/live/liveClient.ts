/**
 * liveClient.ts — WebSocket client for bidirectional voice and event streaming with Gemini Live.
 *
 * Implements the WellPulse Live client contract:
 * - Upstream: 16 kHz PCM16 mono little-endian audio, prompt, audio_end, interrupt, context
 * - Downstream: 24 kHz PCM16 mono audio, status, voice_state, input_transcript, caption_delta,
 *               tool_call, action, turn_complete, fallback_reply, interrupted, error
 */

import { audioPlayer } from './audioPlayer';
import { micCapture } from './micCapture';
import { getPersona, subscribePersona } from '../state/persona';
import type { AppLanguage } from '../agent/uiCommands';

export type LiveStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'resumed' | 'fallback';
export type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';
export type LiveLanguage = AppLanguage;

export interface LiveContext {
  field?: string;
  well_id?: string;
  persona?: string;
  language?: LiveLanguage;
  screen?: string;
}

export interface ToolCallEvent {
  name: string;
  status: 'running' | 'done';
  args?: Record<string, unknown>;
  result?: unknown;
  duration_ms?: number;
}

export interface LiveHandlers {
  onStatus?: (s: LiveStatus, info: { model?: string; memory?: boolean; message?: string }) => void;
  onVoiceState?: (s: VoiceState) => void;
  onInputTranscript?: (textDelta: string) => void;
  onCaptionDelta?: (textDelta: string) => void;
  onTurnComplete?: (fullText: string) => void;
  onToolCall?: (ev: ToolCallEvent) => void;
  onAction?: (kind: string, payload: unknown) => void;
  onInterrupted?: () => void;
  onFallbackReply?: (msg: {
    text: string;
    recommendation?: unknown;
    engine?: string;
    artifacts?: unknown[];
    actions?: unknown[];
  }) => void;
  onError?: (message: string) => void;
  onFirstAudio?: (latencyMs: number) => void; // ms from last audio_end/prompt sent to first downstream audio chunk of that turn
}

export class LiveClient {
  private ws: WebSocket | null = null;
  private status: LiveStatus = 'disconnected';
  private voiceState: VoiceState = 'idle';
  private handlers: LiveHandlers = {};
  private currentContext: LiveContext = {};
  private reconnectTimer: number | null = null;
  private reconnectAttempts = 0;
  private explicitDisconnect = false;
  private openMic = false;
  private turnStartTime: number | null = null;
  private waitingForFirstAudio = false;
  private fallbackRetryTimer: number | null = null;
  /** C-R10: true while the app wants Live on (set by connect, cleared by disconnect). */
  private active = false;
  /** C-R10: when the current socket reported connected (Cloud Run ends sockets at 60 min). */
  private connectedAt = 0;
  private refreshTimer: number | null = null;
  /** C-R10: per-tab voice session id so a reconnect resumes the same Gemini session and its memory. */
  private readonly sid: string = LiveClient.tabSessionId();

  private static tabSessionId(): string {
    try {
      const k = 'urvi.live.sid';
      let v = window.sessionStorage.getItem(k);
      if (!v) {
        v = (crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`).replace(/[^A-Za-z0-9-]/g, '');
        window.sessionStorage.setItem(k, v);
      }
      return v;
    } catch (_) {
      return `${Date.now()}-${Math.random().toString(36).slice(2)}`.replace(/[^A-Za-z0-9-]/g, '');
    }
  }

  /** Refresh the socket at ~55 min while Urvi is silent, so Cloud Run's 60-min cut never lands mid-reply. */
  private startRefreshWatch(): void {
    if (this.refreshTimer || typeof window === 'undefined') return;
    this.refreshTimer = window.setInterval(() => {
      if (!this.active || !this.ws || this.ws.readyState !== WebSocket.OPEN || !this.connectedAt) return;
      const ageMin = (Date.now() - this.connectedAt) / 60000;
      if (ageMin >= 55 && this.voiceState === 'idle') this.reopenSocket();
    }, 30000);
  }

  constructor(handlers?: LiveHandlers) {
    if (handlers) {
      this.handlers = handlers;
    }
    // Stage Y: persona switch reaches Live — sent as ui_state.persona (server re-gates every tool call).
    subscribePersona((p) => this.setContext({ persona: p }));
    // C-R10: voice must not stay dropped — reconnect as soon as the tab is visible again or the network returns.
    if (typeof window !== 'undefined') {
      const revive = () => this.reviveIfDropped();
      window.addEventListener('online', revive);
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') revive();
      });
    }
  }

  /** C-R10: back-off for socket reconnects: 1 s, 2 s, 4 s, 8 s, then every 15 s, for as long as Live is on. */
  private backoffMs(): number {
    return Math.min(15000, 1000 * 2 ** Math.max(0, this.reconnectAttempts - 1));
  }

  private scheduleReconnect(): void {
    if (this.explicitDisconnect || !this.active || this.reconnectTimer) return;
    this.reconnectAttempts += 1;
    const wait = this.backoffMs();
    this.setStatus('reconnecting', { message: `Reconnecting in ${Math.round(wait / 1000)}s...` });
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.explicitDisconnect) this.connect(this.currentContext);
    }, wait);
  }

  /** In text fallback (Gemini Live unavailable), keep trying to get voice back every 20 s; text keeps working. */
  private scheduleFallbackRetry(): void {
    if (this.explicitDisconnect || !this.active || this.fallbackRetryTimer) return;
    this.fallbackRetryTimer = window.setTimeout(() => {
      this.fallbackRetryTimer = null;
      if (this.explicitDisconnect || this.status !== 'fallback') return;
      this.reopenSocket();
    }, 20000);
  }

  /** Close the current socket (no auto-reconnect from its onclose) and dial a new one, keeping Live mode on. */
  private reopenSocket(): void {
    const old = this.ws;
    this.ws = null;
    if (old) {
      try {
        old.close();
      } catch (_) {}
    }
    this.connect(this.currentContext);
  }

  private reviveIfDropped(): void {
    if (this.explicitDisconnect || !this.active) return;
    if (this.status === 'disconnected' || this.status === 'reconnecting' || this.status === 'fallback') {
      if (this.reconnectTimer) {
        window.clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      this.reopenSocket();
    }
  }

  public setHandlers(h: LiveHandlers): void {
    this.handlers = h;
  }

  public getStatus(): LiveStatus {
    return this.status;
  }

  public isOpenMic(): boolean {
    return this.openMic;
  }

  private setStatus(s: LiveStatus, info: { model?: string; memory?: boolean; message?: string } = {}): void {
    this.status = s;
    this.handlers.onStatus?.(s, info);
  }

  private setVoiceState(s: VoiceState): void {
    this.voiceState = s;
    this.handlers.onVoiceState?.(s);
  }

  private buildWsUrl(ctx: LiveContext): string {
    if (typeof window === 'undefined') {
      return 'ws://localhost:8002/ws/live';
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // C-R10: always same-origin. In local dev the Vite server proxies /ws to the backend (vite.config.ts); dialling
    // <host>:8002 directly fails from a laptop (Cloudtop firewall / IPv6-only DNS) and left Live stuck in text mode.
    const host = window.location.host;

    const params = new URLSearchParams();
    if (ctx.language) params.set('language', ctx.language);
    if (ctx.well_id) params.set('well_id', ctx.well_id);
    if (ctx.field) params.set('field', ctx.field);
    if (ctx.persona) params.set('persona', ctx.persona);
    params.set('sid', this.sid);

    const qs = params.toString();
    return `${proto}//${host}/ws/live${qs ? `?${qs}` : ''}`;
  }

  public connect(ctx: LiveContext = {}): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (ctx) {
      this.currentContext = { ...this.currentContext, ...ctx };
    }
    if (!this.currentContext.persona) this.currentContext.persona = getPersona(); // Stage Y

    this.explicitDisconnect = false;
    this.active = true;
    this.connectedAt = 0;
    this.startRefreshWatch();
    this.setStatus('connecting');

    const url = this.buildWsUrl(this.currentContext);

    try {
      this.ws = new WebSocket(url);
      this.ws.binaryType = 'arraybuffer';

      const currentSock = this.ws;

      this.ws.onopen = () => {
        if (this.ws !== currentSock) return;
        // Back-off resets only when the server reports the Gemini session is up (status connected / resumed).
        // Status stays 'connecting' until the server reports the Gemini session is up
        // ({type:"status", status:"connected"}); only then is Live really usable.
        this.setContext({});
      };

      this.ws.onmessage = (event: MessageEvent) => {
        if (this.ws !== currentSock) return;

        // Downstream binary chunk (24 kHz PCM16 mono LE)
        if (event.data instanceof ArrayBuffer) {
          if (this.waitingForFirstAudio && this.turnStartTime !== null) {
            const latency = performance.now() - this.turnStartTime;
            this.waitingForFirstAudio = false;
            this.turnStartTime = null;
            this.handlers.onFirstAudio?.(latency);
          }
          audioPlayer.playPcmChunk(event.data);
          return;
        }

        try {
          const msg = JSON.parse(event.data);
          this.handleServerMessage(msg);
        } catch (_) {
          // ignore non-json
        }
      };

      this.ws.onclose = () => {
        if (this.ws !== currentSock) return;
        this.ws = null;
        this.waitingForFirstAudio = false;

        if (this.explicitDisconnect) {
          this.setStatus('disconnected');
          return;
        }
        if (this.status === 'fallback') {
          this.scheduleFallbackRetry(); // text keeps working; voice comes back by itself
          return;
        }
        // C-R10: unexpected socket close (network blip, laptop sleep, 1 h Cloud Run limit): keep retrying with back-off.
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        if (this.ws !== currentSock) return;
        // onclose follows and schedules the retry; no error bubble for a transient drop.
      };
    } catch (_) {
      this.ws = null;
      this.waitingForFirstAudio = false;
      this.scheduleReconnect();
    }
  }

  private handleServerMessage(msg: Record<string, any>): void {
    if (!msg || !msg.type) return;

    switch (msg.type) {
      case 'status': {
        const nextStatus = msg.status as LiveStatus;
        if (nextStatus === 'connected' || nextStatus === 'resumed') {
          this.reconnectAttempts = 0;
          this.connectedAt = Date.now();
        }
        this.setStatus(nextStatus, {
          model: msg.model,
          memory: msg.memory,
          message: msg.message,
        });
        if (nextStatus === 'fallback') this.scheduleFallbackRetry();
        break;
      }

      case 'voice_state': {
        const state = msg.state as VoiceState;
        this.setVoiceState(state);
        break;
      }

      case 'input_transcript': {
        this.handlers.onInputTranscript?.(msg.text ?? '');
        break;
      }

      case 'caption_delta': {
        this.handlers.onCaptionDelta?.(msg.text ?? '');
        break;
      }

      case 'turn_complete': {
        this.waitingForFirstAudio = false;
        this.handlers.onTurnComplete?.(msg.full_text ?? '');
        break;
      }

      case 'tool_call': {
        const ev: ToolCallEvent = {
          name: msg.name,
          status: msg.status,
          args: msg.args,
          result: msg.result,
          duration_ms: msg.duration_ms,
        };
        this.handlers.onToolCall?.(ev);
        break;
      }

      case 'action': {
        this.handlers.onAction?.(msg.kind, msg.payload);
        break;
      }

      case 'interrupted': {
        this.waitingForFirstAudio = false;
        audioPlayer.interrupt();
        this.handlers.onInterrupted?.();
        break;
      }

      case 'fallback_reply': {
        this.handlers.onFallbackReply?.({
          text: msg.text ?? '',
          recommendation: msg.recommendation,
          engine: msg.engine,
          artifacts: Array.isArray(msg.artifacts) ? msg.artifacts : [],
          actions: Array.isArray(msg.actions) ? msg.actions : [],
        });
        break;
      }

      case 'error': {
        this.handlers.onError?.(msg.message ?? 'Unknown server error');
        break;
      }
    }
  }

  public disconnect(): void {
    this.explicitDisconnect = true;
    this.active = false;
    if (this.refreshTimer) {
      window.clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.fallbackRetryTimer) {
      window.clearTimeout(this.fallbackRetryTimer);
      this.fallbackRetryTimer = null;
    }
    this.reconnectAttempts = 0;
    this.openMic = false;
    this.turnStartTime = null;
    this.waitingForFirstAudio = false;

    micCapture.stop();
    audioPlayer.interrupt();

    if (this.ws) {
      try {
        this.ws.close();
      } catch (_) {}
      this.ws = null;
    }
    this.setStatus('disconnected');
    this.setVoiceState('idle');
  }

  public retry(): void {
    this.disconnect();
    this.connect(this.currentContext);
  }

  public setContext(ctx: LiveContext): void {
    this.currentContext = { ...this.currentContext, ...ctx };
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: 'context',
          ui_state: {
            field: this.currentContext.field,
            well_id: this.currentContext.well_id,
            persona: this.currentContext.persona,
            language: this.currentContext.language,
            screen: this.currentContext.screen,
          },
        })
      );
    }
  }

  public sendText(text: string): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    audioPlayer.interrupt();
    this.turnStartTime = performance.now();
    this.waitingForFirstAudio = true;
    this.setVoiceState('thinking');
    this.ws.send(JSON.stringify({ type: 'prompt', text }));
    return true;
  }

  public async startTalking(): Promise<void> {
    if (this.voiceState === 'speaking' || audioPlayer.getIsPlaying()) {
      this.interrupt();
    }

    if (!micCapture.isCapturing()) {
      await micCapture.start((chunk: ArrayBuffer) => {
        this.sendAudio(chunk);
      });
    } else {
      micCapture.enable(true);
    }
    this.setVoiceState('listening');
  }

  private sendAudio(chunk: ArrayBuffer): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(chunk);
    }
  }

  public stopTalking(): void {
    if (this.openMic) {
      // In open-mic mode keep the mic enabled continuously and never send audio_end
      return;
    }

    micCapture.enable(false);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.turnStartTime = performance.now();
      this.waitingForFirstAudio = true;
      this.ws.send(JSON.stringify({ type: 'audio_end' }));
    }
    this.setVoiceState('thinking');
  }

  public async setOpenMic(on: boolean): Promise<void> {
    this.openMic = !!on;
    if (this.openMic) {
      if (this.voiceState === 'speaking' || audioPlayer.getIsPlaying()) {
        this.interrupt();
      }
      if (!micCapture.isCapturing()) {
        await micCapture.start((chunk: ArrayBuffer) => {
          this.sendAudio(chunk);
        });
      } else {
        micCapture.enable(true);
      }
      this.setVoiceState('listening');
    } else {
      micCapture.enable(false);
      this.setVoiceState('idle');
    }
  }

  public interrupt(): void {
    this.waitingForFirstAudio = false;
    audioPlayer.interrupt();
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'interrupt' }));
    }
    this.handlers.onInterrupted?.();
  }
}

export function isLiveSupported(): boolean {
  if (typeof window === 'undefined') return false;
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  return !!(
    AudioCtx &&
    'audioWorklet' in AudioCtx.prototype &&
    typeof navigator !== 'undefined' &&
    typeof navigator.mediaDevices?.getUserMedia === 'function' &&
    window.WebSocket
  );
}

