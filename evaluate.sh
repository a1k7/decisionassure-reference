#!/usr/bin/env sh
# Runs the complete HTTP evaluation against a local Docker instance.
set -eu

base_url="http://localhost:8000"

docker compose up --build -d

attempt=0
until curl -fsS "$base_url/docs" >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -eq 30 ]; then
    echo "Service did not become ready at $base_url" >&2
    exit 1
  fi
  sleep 1
done

receipt=$(curl -fsS -X POST "$base_url/decision" -H 'content-type: application/json' --data @sample/valid_request.json)
receipt_id=$(printf '%s' "$receipt" | python3 -c 'import json, sys; print(json.load(sys.stdin)["receipt_id"])')
echo "✓ create decision ($receipt_id)"

curl -fsS "$base_url/receipt/$receipt_id" >/dev/null
echo "✓ retrieve receipt"

replay() {
  label=$1
  state=$2
  result=$(curl -fsS -X POST "$base_url/replay" -H 'content-type: application/json' \
    --data "{\"receipt_id\":\"$receipt_id\",\"current_state\":$state}")
  status=$(printf '%s' "$result" | python3 -c 'import json, sys; print(json.load(sys.stdin)["status"])')
  printf '✓ %s: %s\n' "$label" "$status"
}

replay "replay healthy" '{}'
replay "revoke authority" "$(cat sample/authority_revoked.json)"
replay "stale evidence" "$(cat sample/stale_evidence.json)"
replay "policy change" "$(cat sample/policy_changed.json)"
replay "runtime unhealthy" '{"runtime_healthy":false}'

tamper=$(curl -fsS -X POST "$base_url/tamper" -H 'content-type: application/json' \
  --data "{\"receipt_id\":\"$receipt_id\",\"field\":\"policy_version\",\"value\":\"2026.09\"}")
tampered_receipt=$(printf '%s' "$tamper" | python3 -c 'import json, sys; print(json.dumps(json.load(sys.stdin)["receipt"]))')
verification=$(curl -fsS -X POST "$base_url/verify" -H 'content-type: application/json' \
  --data "{\"receipt\":$tampered_receipt}")
valid=$(printf '%s' "$verification" | python3 -c 'import json, sys; print(json.load(sys.stdin)["VALID"])')
[ "$valid" = "False" ]
echo "✓ tamper receipt: verification invalidated"
