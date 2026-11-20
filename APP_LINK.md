# Urvi · Cairn / Vedanta Oil and Gas (Barmer Basin) — Live Cloud Run Service

- **Cloud Run URL (Deterministic):** https://urvi-cairn-app-498143636903.us-central1.run.app
- **Cloud Run URL (Regional Hash):** https://urvi-cairn-app-6xyz3omk5q-uc.a.run.app
- **GCP Project:** `urvi-cairn-barmer-ai-agent` (`498143636903`)
- **Service / Region:** `urvi-cairn-app` (`us-central1`)
- **Active Ready Revision:** `urvi-cairn-app-00005-24s` (`v10-barmer-rc5`, deployed `2026-11-19`, `6/6` unauthenticated live smoke checks passed; Indian English `en-IN` voice locale + 15 Indian languages, cache warm-up at startup, two-sentence spoken answers, auto-reconnect / text-mode recovery). Rollback: `urvi-cairn-app-00004-cd9`.
- **Runtime Service Account:** `urvi-cairn-run@urvi-cairn-barmer-ai-agent.iam.gserviceaccount.com`
- **Direct 1-Click Browser Access:** Enabled via `--no-invoker-iam-check` (Argolis-compliant, `max-instances=1` cap). Open https://urvi-cairn-app-498143636903.us-central1.run.app directly in Chrome, click **Urvi AI Agent** (bottom right), and press **Live → Open mic** to talk.

*(The ONGC demo remains completely separate and untouched at `wellpulse-app` in `workover-operations-agentic-ai`.)*
