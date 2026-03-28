"""Alerting helpers (webhook)."""
from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class AlertSender:
    """Send event notifications to a webhook endpoint."""

    def __init__(self, webhook_url: str, timeout_seconds: float = 4.0) -> None:
        self.webhook_url = webhook_url.strip()
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def send(self, title: str, payload: dict[str, Any]) -> bool:
        if not self.enabled:
            return False

        body = {
            "title": title,
            "timestamp": payload.get("created_at"),
            "payload": payload,
        }
        try:
            response = requests.post(
                self.webhook_url,
                json=body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("Alert send failed: %s", exc)
            return False
