# Urvi · Cairn / Vedanta Oil and Gas (Barmer Basin) — Live Cloud Run Service

- **Cloud Run URL (Deterministic):** https://urvi-cairn-app-498143636903.us-central1.run.app
- **Cloud Run URL (Regional Hash):** https://urvi-cairn-app-6xyz3omk5q-uc.a.run.app
- **GCP Project:** `urvi-cairn-barmer-ai-agent` (`498143636903`)
- **Service / Region:** `urvi-cairn-app` (`us-central1`)
- **Active Ready Revision:** `urvi-cairn-app-00003-cqg` (`v10-barmer-rc3`, deployed `2026-11-15`, `6/6` live smoke checks passed incl. `/ws/live` Gemini Live WebSocket with `en-IN` Indian English accent + visual interventions parity)
- **Runtime Service Account:** `urvi-cairn-run@urvi-cairn-barmer-ai-agent.iam.gserviceaccount.com`
- **Authenticated Browser Access (Org Policy Note):** Org policy restricts `allUsers` on `amandeepsinghs.altostrat.com`; to open the Cloud Run service in any laptop browser with automatic IAM auth, run:
  ```bash
  gcloud run services proxy urvi-cairn-app --project=urvi-cairn-barmer-ai-agent --region=us-central1 --port=8080
  ```
  and open `http://localhost:8080`.

*(The ONGC demo remains completely separate and untouched at `wellpulse-app` in `workover-operations-agentic-ai`.)*
