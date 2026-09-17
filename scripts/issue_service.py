#!/usr/bin/env python3
"""Validate and forward normalized Modus issue requests.

This is the standalone adapter for the shared issue service. It is deliberately
dry-run by default: callers must opt into ``--send`` and provide the webhook
URL/token through environment variables. The n8n sub-workflow uses the same
payload contract documented in docs/chat-bots/issue-service.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ALLOWED_REPO = "trimble-oss/modus-wc-2.0"
ALLOWED_TYPES = frozenset({"feature", "bug", "design", "docs"})
IDEMPOTENT_SOURCES = frozenset({"google-chat", "gemini-notes", "backlog-sheet"})


@dataclass(frozen=True)
class ValidatedRequest:
    """Normalized request accepted by the shared service."""

    payload: dict[str, Any]


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def validate_request(raw: dict[str, Any]) -> ValidatedRequest:
    """Validate caller input without contacting GitHub or n8n."""

    if not isinstance(raw, dict):
        raise ValueError("request must be a JSON object")

    repo = _require_string(raw, "repo")
    if repo != ALLOWED_REPO:
        raise ValueError(f"repo must be {ALLOWED_REPO!r}")

    request_type = _require_string(raw, "type")
    if request_type not in ALLOWED_TYPES:
        raise ValueError(f"type must be one of {sorted(ALLOWED_TYPES)}")

    source = raw.get("source")
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    source_kind = _require_string(source, "kind")

    title = _require_string(raw, "title")
    summary = _require_string(raw, "summary")
    components = raw.get("components", [])
    labels = raw.get("labels", [])
    evidence = raw.get("contextEvidence", [])
    conversation = raw.get("rawConversation", [])
    additional_context = raw.get("additionalContext", {})

    if not isinstance(components, list) or not all(
        isinstance(component, str) and component.strip() for component in components
    ):
        raise ValueError("components must be a list of non-empty strings")
    if not isinstance(labels, list) or not all(
        isinstance(label, str) and label.strip() for label in labels
    ):
        raise ValueError("labels must be a list of non-empty strings")
    if not isinstance(evidence, list):
        raise ValueError("contextEvidence must be a list")
    if not isinstance(conversation, list):
        raise ValueError("rawConversation must be a list")
    if not isinstance(additional_context, dict):
        raise ValueError("additionalContext must be an object")

    idempotency_key = raw.get("idempotencyKey")
    if source_kind in IDEMPOTENT_SOURCES and (
        not isinstance(idempotency_key, str) or not idempotency_key.strip()
    ):
        raise ValueError(f"idempotencyKey is required for {source_kind}")

    if raw.get("autoApprove") is True:
        raise ValueError("autoApprove must be false for shared issue service calls")

    normalized = {
        "repo": repo,
        "title": title[:200],
        "summary": summary[:12000],
        "type": request_type,
        "components": [component.strip() for component in components],
        "labels": sorted(set(label.strip() for label in labels)),
        "source": source,
        "rawConversation": conversation[-100:],
        "contextEvidence": evidence[-100:],
        "additionalContext": additional_context,
        "idempotencyKey": idempotency_key
        or _fallback_idempotency_key(source, title, summary),
        "autoApprove": False,
    }
    return ValidatedRequest(payload=normalized)


def _fallback_idempotency_key(
    source: dict[str, Any], title: str, summary: str
) -> str:
    """Give cursor/local calls a stable key without guessing external IDs."""

    source_text = json.dumps(source, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(
        f"{source_text}\n{title}\n{summary}".encode("utf-8")
    ).hexdigest()[:24]
    return f"local:{digest}"


def build_scaffolding_payload(request: ValidatedRequest) -> dict[str, Any]:
    """Map the public contract to the Issue Scaffolding webhook contract."""

    payload = request.payload
    return {
        "prompt": (
            "Create or enrich this Modus issue using the research-first "
            "Issue Scaffolding v2 instructions. Do not auto-approve."
        ),
        "issue_url": payload["additionalContext"].get("issueUrl"),
        "repo": payload["repo"],
        "labels": payload["labels"] or ["needs-scaffolding"],
        "additional_context": {
            "normalized_request": payload,
            "source": payload["source"],
            "context_evidence": payload["contextEvidence"],
            "raw_conversation": payload["rawConversation"],
        },
        "auto_approve": False,
        "idempotency_key": payload["idempotencyKey"],
    }


def _post_json(url: str, token: str, body: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"issue service HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"issue service connection failed: {error.reason}") from error

    try:
        decoded = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise RuntimeError("issue service returned non-JSON response") from error
    if not isinstance(decoded, dict):
        raise RuntimeError("issue service response must be a JSON object")
    return decoded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and optionally forward a Modus issue request."
    )
    parser.add_argument(
        "--input",
        default="-",
        help="JSON input path; '-' reads stdin (default)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="POST to ISSUE_SERVICE_WEBHOOK_URL instead of printing a dry run",
    )
    parser.add_argument(
        "--webhook-url",
        default=os.environ.get("ISSUE_SERVICE_WEBHOOK_URL"),
        help="Issue Scaffolding webhook URL; prefer ISSUE_SERVICE_WEBHOOK_URL",
    )
    return parser.parse_args()


def read_input(path: str) -> dict[str, Any]:
    if path == "-":
        content = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as input_file:
            content = input_file.read()
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("input JSON must be an object")
    return value


def main() -> int:
    args = parse_args()
    try:
        validated = validate_request(read_input(args.input))
        scaffolding_payload = build_scaffolding_payload(validated)
        if not args.send:
            print(json.dumps(scaffolding_payload, indent=2, sort_keys=True))
            return 0

        if not args.webhook_url:
            raise ValueError(
                "--send requires --webhook-url or ISSUE_SERVICE_WEBHOOK_URL"
            )
        token = os.environ.get("ISSUE_SERVICE_WEBHOOK_TOKEN")
        if not token:
            raise ValueError("--send requires ISSUE_SERVICE_WEBHOOK_TOKEN")
        print(
            json.dumps(
                _post_json(args.webhook_url, token, scaffolding_payload),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
