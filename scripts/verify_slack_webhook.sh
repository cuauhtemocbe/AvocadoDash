#!/usr/bin/env bash
set -euo pipefail

# Verifies that the Slack incoming webhook configured for Railway
# deploy-failure notifications is reachable and posts to the channel.
#
# Usage:
#   SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..." ./scripts/verify_slack_webhook.sh
#
# This posts directly to the Slack webhook URL using Slack's own payload
# format -- it does not exercise Railway's payload Muxer (that transform
# only runs when Railway itself sends the request on a real deploy
# failure). It only confirms the webhook URL is valid and the configured
# Slack channel receives messages.

if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  echo "Error: SLACK_WEBHOOK_URL is not set." >&2
  echo "Usage: SLACK_WEBHOOK_URL=<url> $0" >&2
  exit 1
fi

payload=$(cat <<'JSON'
{
  "text": ":rotating_light: [verify_slack_webhook.sh] Synthetic test message -- if you see this, the AvocadoDash Railway deploy-failure Slack webhook is configured correctly."
}
JSON
)

http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "$SLACK_WEBHOOK_URL")

if [[ "$http_status" == "200" ]]; then
  echo "OK: Slack accepted the webhook payload (HTTP 200). Check the channel for the test message."
else
  echo "FAILED: Slack returned HTTP $http_status. Check that SLACK_WEBHOOK_URL is correct and active." >&2
  exit 1
fi
