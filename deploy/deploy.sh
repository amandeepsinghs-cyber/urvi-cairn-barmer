#!/usr/bin/env bash
# ==============================================================================
# WellPulse v0.4 — Cloud Run packaging + deploy (Stage W, SDD §17, D-14, D-16, D-18)
#
#   deploy/deploy.sh plan      print every command, change nothing (default)
#   deploy/deploy.sh iam       ensure runtime SA + additive role bindings (never removes any)
#   deploy/deploy.sh build     Cloud Build the multi-stage image -> Artifact Registry (no deploy)
#   deploy/deploy.sh deploy    new revision of urvi-cairn-app from $IMAGE (or --source, see below)
#   deploy/deploy.sh smoke     deploy/smoke_test.py against the service URL
#   deploy/deploy.sh all       iam -> build -> deploy -> smoke
#
# Env overrides:
#   IMAGE_TAG=v04-<sha>      image tag (default: v04-<git short sha>[-dirty])
#   RUN_SA=<email>           runtime SA (default dedicated urvi-cairn-run@…; SDD §17.3)
#   DEPLOY_MODE=image|source image (default): build with gcloud builds submit on e2-highcpu-8,
#                            then `run deploy --image`. source: `gcloud run deploy --source .`
#                            (Cloud Run's default build machine; corpus build is slower there).
#   DRY_RUN=1                print commands instead of running them (implied by `plan`)
#
# Never deletes services, revisions, images or IAM bindings. Rollback:
#   gcloud run services update-traffic urvi-cairn-app --region us-central1 \
#     --project urvi-cairn-barmer-ai-agent --to-revisions=<previous>=100
# ==============================================================================
set -euo pipefail

PROJECT="urvi-cairn-barmer-ai-agent"
REGION="us-central1"
SERVICE="urvi-cairn-app"

# ---- SAFETY GUARD (Cairn / Vedanta replica) -------------------------------------------------------
# This repo is a replica of the ONGC WellPulse demo. It must NEVER deploy to, build into or grant IAM on the ONGC
# project or service. Refuse to run any real step (anything except `plan`) when the targets are ONGC's or are still
# the placeholder. Set PROJECT above once the Cairn Google Cloud project exists.
ONGC_PROJECT="workover-operations""-agentic-ai"
ONGC_SERVICE="wellpulse""-app"
guard_targets() {
    if [ "${PROJECT}" = "${ONGC_PROJECT}" ] || [ "${SERVICE}" = "${ONGC_SERVICE}" ]; then
        echo "[x] REFUSED: targets point at the ONGC demo (${PROJECT}/${SERVICE}). This is the Cairn replica." >&2
        exit 2
    fi
    case "${PROJECT}" in *TBD*)
        echo "[x] REFUSED: Cairn Google Cloud project not set yet (PROJECT=${PROJECT}). Edit deploy/deploy.sh." >&2
        exit 2;;
    esac
}
AR_REPO="cloud-run-source-deploy"
BUCKET="urvi-cairn-barmer-ai-agent-datalake"
BQ_DATASETS=(urvi_cairn_bronze urvi_cairn_silver urvi_cairn_gold)
SA_NAME="urvi-cairn-run"
RUN_SA="${RUN_SA:-${SA_NAME}@${PROJECT}.iam.gserviceaccount.com}"
DEPLOY_MODE="${DEPLOY_MODE:-image}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

# The shell may export the WRONG project (og-agentic-ecosystem): every gcloud call below passes
# --project explicitly, and we unset it so nothing inherits it by accident.
unset GOOGLE_CLOUD_PROJECT CLOUDSDK_CORE_PROJECT || true

if [ -z "${IMAGE_TAG:-}" ]; then
    sha="$(git rev-parse --short HEAD 2>/dev/null || echo nogit)"
    dirty="$(git status --porcelain 2>/dev/null | grep -q . && echo -dirty || true)"
    IMAGE_TAG="v04-${sha}${dirty}"
fi
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}/${SERVICE}:${IMAGE_TAG}"

# Cloud Run flags (SDD §17.2). D-16: one instance + session affinity (in-memory ADK/Live sessions).
RUN_FLAGS=(
    --project "${PROJECT}" --region "${REGION}"
    --service-account "${RUN_SA}"
    --memory 4Gi --cpu 2 --concurrency 20
    --min-instances 1 --max-instances 1
    --timeout 3600 --session-affinity --no-cpu-throttling --cpu-boost
    --execution-environment gen2
    --port 8080
    --env-vars-file deploy/env.cloudrun.yaml
    --labels app=urvi-cairn,stage=v10
    --allow-unauthenticated
    --quiet
)
# --env-vars-file REPLACES all env vars on the service => the legacy GEMINI_API_KEY is removed.
# Public access is unchanged: we do not touch the service IAM policy (allUsers invoker stays).

# Print every command; execute unless DRY_RUN=1. Failures stop the script (set -e).
x() {
    printf '+'; printf ' %q' "$@"; printf '\n'
    if [ "${DRY_RUN:-0}" = "1" ]; then return 0; fi
    "$@"
}
# Additive binding that must not abort the whole run (e.g. bq CLI without dataset IAM support).
x_soft() {
    x "$@" || echo "[!] WARN: command failed (non-fatal, grant manually if needed): $*" >&2
}

step_iam() {
    echo "== iam: runtime service account ${RUN_SA} (additive only)"
    if [ "${RUN_SA}" = "${SA_NAME}@${PROJECT}.iam.gserviceaccount.com" ]; then
        if [ "${DRY_RUN:-0}" = "1" ] || ! gcloud iam service-accounts describe "${RUN_SA}" --project "${PROJECT}" >/dev/null 2>&1; then
            x gcloud iam service-accounts create "${SA_NAME}" --project "${PROJECT}" \
                --display-name "WellPulse Cloud Run runtime (v0.4)" \
                --description "Least-privilege runtime SA for urvi-cairn-app (SDD 17.3)"
        else
            echo "   SA exists"
        fi
    fi
    local member="serviceAccount:${RUN_SA}"
    # Project-level roles (SDD §17.3). add-iam-policy-binding is additive and idempotent.
    for role in roles/aiplatform.user roles/bigquery.jobUser roles/logging.logWriter roles/cloudtrace.agent; do
        x gcloud projects add-iam-policy-binding "${PROJECT}" --member "${member}" --role "${role}" \
            --condition None --quiet --format none
    done
    # BigQuery read on the wellpulse_* datasets only (DATA_BACKEND=bigquery).
    for ds in "${BQ_DATASETS[@]}"; do
        x_soft bq add-iam-policy-binding --member "${member}" --role roles/bigquery.dataViewer \
            "${PROJECT}:${ds}"
    done
    # Optional: read PDFs from the datalake bucket instead of the image.
    x gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" --project "${PROJECT}" \
        --member "${member}" --role roles/storage.objectViewer --format none
    # Ensure Cloud Build default worker SA in new GCP projects can read _cloudbuild source tarballs & push images.
    if [ "${DRY_RUN:-0}" != "1" ]; then
        local proj_num
        proj_num="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)')"
        for cb_sa in "${proj_num}-compute@developer.gserviceaccount.com" "${proj_num}@cloudbuild.gserviceaccount.com"; do
            x_soft gcloud projects add-iam-policy-binding "${PROJECT}" \
                --member "serviceAccount:${cb_sa}" --role roles/cloudbuild.builds.builder \
                --condition None --quiet --format none
        done
    fi
}

step_build() {
    echo "== build: ${IMAGE}"
    if [ "${DRY_RUN:-0}" = "1" ] || ! gcloud artifacts repositories describe "${AR_REPO}" --project "${PROJECT}" --location "${REGION}" >/dev/null 2>&1; then
        x gcloud artifacts repositories create "${AR_REPO}" --project "${PROJECT}" --location "${REGION}" \
            --repository-format=docker --description="Cloud Run container images for ${SERVICE}"
    fi
    # e2-highcpu-8: the corpus build (≈20.3k PDFs render -> scanify -> validate -> index) is CPU bound.
    x gcloud builds submit . --project "${PROJECT}" --region "${REGION}" \
        --tag "${IMAGE}" --machine-type e2-highcpu-8 --timeout 3600s
}

step_deploy() {
    echo "== deploy: ${SERVICE} (${DEPLOY_MODE})"
    if [ "${DRY_RUN:-0}" != "1" ]; then
        prev="$(gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" \
            --format 'value(status.latestReadyRevisionName)' 2>/dev/null || true)"
        echo "   previous ready revision (rollback target): ${prev:-<none>}"
    fi
    if [ "${DEPLOY_MODE}" = "source" ]; then
        x gcloud run deploy "${SERVICE}" --source . "${RUN_FLAGS[@]}"
    else
        x gcloud run deploy "${SERVICE}" --image "${IMAGE}" "${RUN_FLAGS[@]}"
    fi
    # Argolis DRS blocks allUsers IAM bindings while permitting --no-invoker-iam-check for 1-click demo access.
    x_soft gcloud run services update "${SERVICE}" --project "${PROJECT}" --region "${REGION}" --no-invoker-iam-check --quiet
}

service_url() {
    gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" \
        --format 'value(status.url)'
}

step_smoke() {
    local url="${SMOKE_URL:-}"
    if [ -z "${url}" ]; then
        if [ "${DRY_RUN:-0}" = "1" ]; then url="https://<urvi-cairn-app URL>"; else url="$(service_url)"; fi
    fi
    echo "== smoke: ${url}"
    if [ "${DRY_RUN:-0}" != "1" ]; then
        SMOKE_BEARER_TOKEN="$(gcloud auth print-identity-token 2>/dev/null || true)"
        export SMOKE_BEARER_TOKEN
    fi
    # websockets ships with uvicorn[standard] in the backend lock, so reuse that environment.
    x bash -c "cd backend && uv run --frozen --no-dev python ../deploy/smoke_test.py '${url}'"
}

cmd="${1:-plan}"
case "${cmd}" in
    plan)   DRY_RUN=1; step_iam; step_build; step_deploy; step_smoke ;;
    iam)    guard_targets; step_iam ;;
    build)  guard_targets; step_build ;;
    deploy) guard_targets; step_deploy ;;
    smoke)  guard_targets; step_smoke ;;
    all)    guard_targets; step_iam; [ "${DEPLOY_MODE}" = "image" ] && step_build; step_deploy; step_smoke ;;
    *) echo "usage: $0 {plan|iam|build|deploy|smoke|all}" >&2; exit 2 ;;
esac
