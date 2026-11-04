#!/usr/bin/env sh
# Daily 05:05 Toronto time, one burst (idle CPU in a job is billed; never spread the crawl).
set -eu
PROJECT_ID=${PROJECT_ID:?}
REGION=${REGION:-northamerica-northeast1}
gcloud scheduler jobs create http mcdocpp-daily \
  --project "$PROJECT_ID" --location "$REGION" \
  --schedule "5 5 * * *" --time-zone "America/Toronto" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/mcdocpp-collector:run" \
  --http-method POST \
  --oauth-service-account-email "mcdocpp-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"
