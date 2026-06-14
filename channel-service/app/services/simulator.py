"""
Delivery simulator — orchestrates the message send simulation.

Receives a batch of recipients from the FastAPI /send endpoint,
assigns each a randomised initial delivery delay, and dispatches
individual Celery tasks for each recipient. The Celery tasks then
handle the full delivery chain (delivered → opened → clicked).

This module is the bridge between the HTTP layer (synchronous
request handling) and the async Celery task chain.
"""

import logging
import random

from app.tasks.callback_tasks import start_delivery_thread

logger = logging.getLogger(__name__)


def process_send_request(
    campaign_id: int,
    channel: str,
    callback_url: str,
    recipients: list[dict],
) -> dict:
    """
    Process an incoming send request by dispatching Celery tasks.

    For each recipient, schedules a `simulate_delivery` task with
    a random 1-3 second delay to simulate network latency and
    message queue processing time.

    Args:
        campaign_id: The CRM campaign ID (for logging context).
        channel: Delivery channel — "sms", "email", or "whatsapp".
        callback_url: CRM receipts endpoint (stored in task for callbacks).
        recipients: List of recipient dicts, each containing at minimum:
                    - communication_id: int
                    - customer_name: str
                    - message: str

    Returns:
        Summary dict with the count of dispatched tasks.
    """
    dispatched = 0
    errors = 0

    for recipient in recipients:
        communication_id = recipient.get("communication_id")

        if not communication_id:
            logger.warning(
                "Recipient missing communication_id in campaign %d — skipping.",
                campaign_id,
            )
            errors += 1
            continue

        # Random initial delay (5-15 seconds) simulates network/queue latency.
        initial_delay = random.uniform(10.0, 60.0)

        try:
            start_delivery_thread(
                communication_id=communication_id,
                initial_delay=initial_delay,
            )
            dispatched += 1

        except Exception as exc:
            logger.error(
                "Failed to dispatch task for comm_id=%d: %s",
                communication_id, str(exc),
            )
            errors += 1

    logger.info(
        "📨 Campaign %d [%s]: dispatched %d tasks (%d errors) for %d recipients.",
        campaign_id, channel, dispatched, errors, len(recipients),
    )

    return {
        "campaign_id": campaign_id,
        "channel": channel,
        "dispatched": dispatched,
        "errors": errors,
        "total_recipients": len(recipients),
    }
