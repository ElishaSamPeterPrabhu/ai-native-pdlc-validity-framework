#!/usr/bin/env python3
"""Prepare and dispatch human-approved Gemini meeting-note items.

This adapter deliberately does not call GitHub or n8n. It converts the
classifier output into:

* a review payload containing every classified item; or
* validated Issue Service request bodies for approved repo/design work.

The caller owns persistence of the review payload and the approval token.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from typing import Any, Iterable


ELIGIBLE_CLASSIFICATIONS = frozenset({"repo-work", "design-work"})
NON_CREATING_CLASSIFICATIONS = frozenset(
    {"process/meta", "decision-record", "already-tracked"}
)
ALL_CLASSIFICATIONS = ELIGIBLE_CLASSIFICATIONS | NON_CREATING_CLASSIFICATIONS
ALLOWED_TYPES = frozenset({"feature", "bug", "design", "docs"})


@dataclass(frozen=True)
class DispatchError:
    item_id: str
    message: str


def _string(value: Any, field: str, *, required: bool = True) -> str:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return ""
    result = str(value).strip()
    if required and not result:
        raise ValueError(f"{field} is required")
    return result


def _stable_key(doc_id: str, item_id: str, classification: str) -> str:
    digest = hashlib.sha256(
        f"{doc_id}:{item_id}:{classification}".encode("utf-8")
    ).hexdigest()[:24]
    return f"gemini:{doc_id}:{digest}"


def _items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = payload.get("items")
    if not isinstance(result, list):
        raise ValueError("items must be an array")
    return [item for item in result if isinstance(item, dict)]


def validate_classification(payload: dict[str, Any]) -> list[DispatchError]:
    """Return classification errors without discarding any source item."""

    errors: list[DispatchError] = []
    for index, item in enumerate(_items(payload)):
        item_id = str(item.get("itemId") or f"item-{index + 1}")
        classification = item.get("classification")
        if classification not in ALL_CLASSIFICATIONS:
            errors.append(
                DispatchError(
                    item_id,
                    f"classification must be one of {sorted(ALL_CLASSIFICATIONS)}",
                )
            )
        if not str(item.get("rawText") or "").strip():
            errors.append(DispatchError(item_id, "rawText is required"))
    return errors


def build_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a complete review model and CardsV2-compatible card."""

    doc_id = _string(payload.get("docId"), "docId")
    doc_url = _string(payload.get("docUrl"), "docUrl", required=False)
    review_id = f"meeting-{doc_id}"
    items = _items(payload)
    errors = validate_classification(payload)

    review_items: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        item_id = str(item.get("itemId") or f"item-{index + 1}")
        classification = str(item.get("classification") or "not-classified")
        eligible = bool(
            item.get("createEligible")
            and classification in ELIGIBLE_CLASSIFICATIONS
            and not any(error.item_id == item_id for error in errors)
        )
        review_items.append(
            {
                "itemId": item_id,
                "classification": classification,
                "rawText": str(item.get("rawText") or ""),
                "sourceExcerpt": str(item.get("sourceExcerpt") or ""),
                "owner": item.get("owner"),
                "componentHints": item.get("componentHints") or [],
                "duplicateCandidates": item.get("duplicateCandidates") or [],
                "reason": str(item.get("reason") or ""),
                "createEligible": eligible,
                "idempotencyKey": _stable_key(doc_id, item_id, classification),
            }
        )

    widgets: list[dict[str, Any]] = [
        {
            "textParagraph": {
                "text": (
                    f"<b>{payload.get('meetingType', 'Meeting')}</b><br>"
                    f"Doc: {doc_url or doc_id}<br>"
                    f"Items: {len(review_items)}"
                )
            }
        }
    ]
    for item in review_items:
        text = (
            f"<b>[{item['classification']}] {item['itemId']}</b><br>"
            f"{item['rawText']}<br><i>{item['reason']}</i>"
        )
        widgets.append({"textParagraph": {"text": text}})

    widgets.append(
        {
            "textInput": {
                "name": "reviewComment",
                "label": "Review comment (optional)",
                "type": "MULT_LINE",
            }
        }
    )
    widgets.append(
        {
            "buttonList": {
                "buttons": [
                    {
                        "text": "Approve selected",
                        "onClick": {
                            "action": {
                                "actionMethodName": "approve_selected",
                                "parameters": [
                                    {"key": "reviewId", "value": review_id}
                                ],
                            }
                        },
                    },
                    {
                        "text": "Request changes",
                        "onClick": {
                            "action": {
                                "actionMethodName": "request_changes",
                                "parameters": [
                                    {"key": "reviewId", "value": review_id}
                                ],
                            }
                        },
                    },
                    {
                        "text": "Discard review",
                        "onClick": {
                            "action": {
                                "actionMethodName": "discard_review",
                                "parameters": [
                                    {"key": "reviewId", "value": review_id}
                                ],
                            }
                        },
                    },
                ]
            }
        }
    )

    return {
        "reviewId": review_id,
        "docId": doc_id,
        "docUrl": doc_url or None,
        "items": review_items,
        "errors": [error.__dict__ for error in errors],
        "chatResponse": {
            "cardsV2": [
                {
                    "cardId": review_id,
                    "card": {
                        "header": {
                            "title": "Meeting notes intake review",
                            "subtitle": "Human selection required",
                        },
                        "sections": [{"widgets": widgets}],
                    },
                }
            ]
        },
    }


def build_issue_requests(
    review: dict[str, Any],
    selected_item_ids: Iterable[str],
    *,
    comment: str = "",
) -> dict[str, Any]:
    """Convert approved item IDs into Issue Service request bodies."""

    selected = set(selected_item_ids)
    items = review.get("items") or []
    requests: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for item in items:
        if item.get("itemId") not in selected:
            continue
        if not item.get("createEligible"):
            rejected.append(
                {
                    "itemId": item.get("itemId"),
                    "reason": "Item is not eligible for issue creation.",
                }
            )
            continue

        classification = item.get("classification")
        request_type = "design" if classification == "design-work" else "feature"
        title = str(item.get("rawText") or "").strip()[:200]
        summary = str(item.get("sourceExcerpt") or item.get("reason") or "").strip()
        if not title or not summary:
            rejected.append(
                {
                    "itemId": item.get("itemId"),
                    "reason": "Approved item lacks a title or summary.",
                }
            )
            continue

        requests.append(
            {
                "repo": "ElishaSamPeterPrabhu/modus-wc-2.0",
                "title": title,
                "summary": summary,
                "type": request_type,
                "components": item.get("componentHints") or [],
                "labels": (
                    ["needs-scaffolding", "design-research"]
                    if request_type == "design"
                    else ["needs-scaffolding"]
                ),
                "source": {
                    "kind": "gemini-notes",
                    "meetingDocId": review.get("docId"),
                    "url": review.get("docUrl"),
                },
                "rawConversation": [
                    {"sender": "Gemini meeting notes", "text": item["rawText"]}
                ],
                "contextEvidence": [
                    {
                        "claim": item.get("reason") or "Selected during human review.",
                        "source": review.get("docUrl") or "meeting-notes",
                    }
                ],
                "additionalContext": {
                    "reviewId": review.get("reviewId"),
                    "reviewComment": comment,
                    "acceptanceCriteria": [],
                    "designNeeded": request_type == "design",
                },
                "idempotencyKey": item.get("idempotencyKey"),
                "autoApprove": False,
            }
        )

    return {"requests": requests, "rejected": rejected}


def read_json(path: str) -> dict[str, Any]:
    source = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    value = json.loads(source)
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("review", "approve"), required=True)
    parser.add_argument("--input", default="-", help="JSON input path or '-'")
    parser.add_argument("--selected", nargs="*", default=[])
    parser.add_argument("--comment", default="")
    args = parser.parse_args()

    try:
        payload = read_json(args.input)
        if args.mode == "review":
            result = build_review_payload(payload)
        else:
            result = build_issue_requests(
                payload, args.selected, comment=args.comment
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
