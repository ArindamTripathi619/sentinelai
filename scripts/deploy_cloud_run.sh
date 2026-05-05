#!/usr/bin/env bash
set -euo pipefail

# Deploy backend to Cloud Run using gcloud builds + deploy
# Requires: gcloud auth done and user has permissions

PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT" ] || [ "$PROJECT" = "(unset)" ]; then
  echo "ERROR: gcloud project not set. Run 'gcloud config set project <PROJECT_ID>'"
  exit 1
fi

SERVICE_NAME=sentinelai-backend
REGION=us-central1
IMAGE="gcr.io/${PROJECT}/${SERVICE_NAME}:$(date +%s)"

echo "Building image: $IMAGE (using backend/Dockerfile)"
gcloud builds submit --tag "$IMAGE" backend --gcs-log-dir=gs://$(gcloud config get-value project)-cloudbuild-logs || gcloud builds submit --tag "$IMAGE" backend --dockerfile backend/Dockerfile

# Expect required env vars to be present; fail if missing
: "${DATABASE_URL:?Need to set DATABASE_URL}"
: "${SUPABASE_URL:?Need to set SUPABASE_URL}"
: "${SUPABASE_SERVICE_ROLE_KEY:?Need to set SUPABASE_SERVICE_ROLE_KEY}"
: "${JWT_SECRET:?Need to set JWT_SECRET}"

echo "Deploying Cloud Run service $SERVICE_NAME in $REGION"
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=${DATABASE_URL},SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},JWT_SECRET=${JWT_SECRET}"

echo "Cloud Run deploy complete. Service URL:"
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)'
