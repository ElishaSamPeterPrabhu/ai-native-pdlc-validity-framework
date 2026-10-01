#!/usr/bin/env bash
# Preflight for Issue Scaffolding v2 sheet-pilot test.
# See docs/pilot/scaffolding-sheet-test-execution.md

set -euo pipefail

ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-https://script.google.com/macros/s/AKfycbx2ytZQabxL0UVVCt56zjbiklM6xvlSFvI8NTQXwmqzqHPw6q9x8-FPcsTR-QSXeFOawg/exec}"
PILOT_SCAFFOLDING_WEBHOOK_URL="https://api2.cursor.sh/automations/webhook/288c955b-aaad-11f1-b532-320a589b8025"

echo "=== Issue Scaffolding sheet-pilot preflight ==="
echo

echo "1. Orchestrator doGet"
curl -sL "$ORCHESTRATOR_URL" | python3 -m json.tool

echo
echo "2. Manual checks (Cursor console)"
echo "   - [PILOT] Modus Issue Scaffolding (288c955b): v2 + pilot append saved"
echo "   - [Pilot] Review Ledger Approve: short approve block saved"
echo "   - GitHub MCP + Drive MCP enabled on both"
echo
echo "3. Scaffolding webhook URL (orchestrator Script Property or Approve env):"
echo "   $PILOT_SCAFFOLDING_WEBHOOK_URL"
echo
echo "4. Apps Script — run in orchestrator editor:"
echo "   readScaffoldingSheetTestPreflight()"
echo "   configureScaffoldingWebhookUrl()  // if issueScaffoldingUrlSet is false"
echo "   // add ISSUE_SCAFFOLDING_WEBHOOK_TOKEN in Script Properties"
echo
echo "5. Execute tests (one phase at a time; wait for Cursor run + poll):"
echo "   runScaffoldingSheetTestPhaseA_T3bClarify()"
echo "   pollScaffoldingResultAndRelayWriteback('<idempotencyKey from log>')"
echo "   runScaffoldingSheetTestPhaseB_T3aHappy()"
echo "   pollScaffoldingResultAndRelayWriteback('<idempotencyKey>')"
echo "   runScaffoldingSheetTestPhaseC_T4aIdempotency()"
echo "   runScaffoldingSheetTestCleanup()"
