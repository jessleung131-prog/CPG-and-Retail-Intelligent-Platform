"""
Alert dispatcher.

Formats MonitorResult and AnomalyAlert objects into structured alert payloads
and optionally sends them to Slack (if SLACK_WEBHOOK_URL is configured).
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Union

import httpx

from config import settings
from monitoring.anomaly_detection import AnomalyAlert
from monitoring.pipeline_monitor import MonitorResult

logger = logging.getLogger(__name__)

AlertItem = Union[MonitorResult, AnomalyAlert]


def format_alert(item: AlertItem) -> dict:
    """Convert an alert object to a structured dict payload."""
    if isinstance(item, MonitorResult):
        return {
            "type": "pipeline_monitor",
            "severity": item.status,
            "table": item.table,
            "check": item.check,
            "detail": item.detail,
            "root_cause_hint": item.root_cause_hint,
            "checked_at": item.checked_at,
        }
    elif isinstance(item, AnomalyAlert):
        return {
            "type": "anomaly",
            "severity": item.severity,
            "table": item.table,
            "column": item.column,
            "date": item.date,
            "value": item.value,
            "expected_range": item.expected_range,
            "root_cause_hint": item.root_cause_hint,
            "check_type": item.check_type,
        }
    return {"type": "unknown", "raw": str(item)}


def _slack_color(severity: str) -> str:
    return {"critical": "danger", "warning": "warning", "ok": "good"}.get(severity, "#cccccc")


def send_slack_alert(items: list[AlertItem], webhook_url: str | None = None) -> bool:
    """
    Post alerts to Slack. Returns True if successful.
    Silently skips if no webhook URL is configured.
    """
    url = webhook_url or settings.slack_webhook_url
    if not url:
        return False

    critical = [i for i in items if getattr(i, "severity", getattr(i, "status", "")) == "critical"]
    warnings = [i for i in items if getattr(i, "severity", getattr(i, "status", "")) == "warning"]

    if not critical and not warnings:
        return True

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*CPG Platform Alert*\n"
                    f":red_circle: {len(critical)} critical  |  :warning: {len(warnings)} warnings"
                ),
            },
        }
    ]

    for item in (critical + warnings)[:5]:  # Cap at 5 items per message
        payload = format_alert(item)
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*[{payload['severity'].upper()}]* `{payload.get('table', '')}` "
                        f"— {payload.get('detail', payload.get('root_cause_hint', ''))}"
                    ),
                },
            }
        )

    try:
        resp = httpx.post(url, json={"blocks": blocks}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Slack alert failed: {e}")
        return False


def dispatch(items: list[AlertItem], send_slack: bool = True) -> list[dict]:
    """
    Format all alerts, log them, and optionally send to Slack.

    Returns the list of formatted alert dicts.
    """
    formatted = [format_alert(i) for i in items]

    for alert in formatted:
        sev = alert.get("severity", "info")
        if sev == "critical":
            logger.error(json.dumps(alert))
        elif sev == "warning":
            logger.warning(json.dumps(alert))
        else:
            logger.info(json.dumps(alert))

    if send_slack:
        send_slack_alert(items)

    return formatted
