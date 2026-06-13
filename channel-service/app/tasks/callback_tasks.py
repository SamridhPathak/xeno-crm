"""
Celery callback tasks — simulate the message delivery lifecycle.

Each task represents one stage in the delivery chain and fires an
HTTP callback to the CRM backend's /receipts endpoint. Tasks chain
themselves: a delivered message may schedule an "opened" task, and
an opened message may schedule a "clicked" task.

Delivery chain & probabilities:
    send
     ├─ 80% → delivered  (1-3s delay)
     │        ├─ 60% → opened  (5-8s delay after delivered)
     │        │        └─ 30% → clicked  (10-15s delay after opened)
     │        └─ 40% → stops at delivered
     └─ 20% → failed    (1-3s delay)

All delays are randomised within the specified ranges to simulate
realistic async delivery behaviour.
"""

import logging
import random
from datetime import datetime, timezone

import httpx
from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Celery App ───────────────────────────────────────────────────

celery_app = Celery(
    "channel_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration for reliable task execution.
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Don't store results for fire-and-forget tasks.
    task_ignore_result=True,
    # Retry connecting to broker on startup.
    broker_connection_retry_on_startup=True,
)


# ═══════════════════════════════════════════════════════════════════
# HELPER — POST receipt to CRM
# ═══════════════════════════════════════════════════════════════════


def _post_receipt(communication_id: int, event_type: str) -> bool:
    """
    POST a single delivery receipt to the CRM backend.

    Uses synchronous httpx since Celery tasks run in a sync worker.
    Returns True on success, False on failure (logged but not raised
    to avoid retrying the whole chain).
    """
    payload = {
        "communication_id": communication_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(settings.receipts_endpoint, json=payload)
            response.raise_for_status()

        logger.info(
            "✅ Receipt posted: comm_id=%d event=%s",
            communication_id, event_type,
        )
        return True

    except httpx.HTTPError as exc:
        logger.error(
            "❌ Failed to post receipt: comm_id=%d event=%s error=%s",
            communication_id, event_type, str(exc),
        )
        return False


# ═══════════════════════════════════════════════════════════════════
# CELERY TASKS — Delivery Chain
# ═══════════════════════════════════════════════════════════════════


@celery_app.task(name="simulate_delivery")
def simulate_delivery(communication_id: int) -> None:
    """
    Stage 1: Simulate initial delivery outcome.

    - 80% probability → delivered (then maybe schedule "opened")
    - 20% probability → failed (terminal state)

    This task is the entry point — called immediately when a
    campaign is sent to the channel service.
    """
    roll = random.random()

    if roll < 0.80:
        # ── Delivered ────────────────────────────────────────────
        _post_receipt(communication_id, "delivered")

        # 60% of delivered messages get opened (scheduled with delay).
        if random.random() < 0.60:
            delay_seconds = random.uniform(5.0, 8.0)
            simulate_opened.apply_async(
                args=[communication_id],
                countdown=delay_seconds,
            )
            logger.debug(
                "Scheduled 'opened' for comm_id=%d in %.1fs",
                communication_id, delay_seconds,
            )
    else:
        # ── Failed ───────────────────────────────────────────────
        _post_receipt(communication_id, "failed")
        logger.debug("comm_id=%d marked as failed.", communication_id)


@celery_app.task(name="simulate_opened")
def simulate_opened(communication_id: int) -> None:
    """
    Stage 2: Simulate message being opened.

    Called only for the 60% of delivered messages that get opened.
    Of those, 30% will proceed to "clicked".
    """
    _post_receipt(communication_id, "opened")

    # 30% of opened messages get clicked.
    if random.random() < 0.30:
        delay_seconds = random.uniform(10.0, 15.0)
        simulate_clicked.apply_async(
            args=[communication_id],
            countdown=delay_seconds,
        )
        logger.debug(
            "Scheduled 'clicked' for comm_id=%d in %.1fs",
            communication_id, delay_seconds,
        )


@celery_app.task(name="simulate_clicked")
def simulate_clicked(communication_id: int) -> None:
    """
    Stage 3: Simulate a click-through on the message.

    Terminal event — the delivery chain ends here.
    Only ~14.4% of all messages reach this stage
    (80% × 60% × 30% = 14.4%).
    """
    _post_receipt(communication_id, "clicked")
    logger.debug("comm_id=%d clicked — chain complete.", communication_id)
