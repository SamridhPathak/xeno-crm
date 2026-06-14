import logging
import random
import threading
import time
from datetime import datetime, timezone

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _post_receipt(communication_id: int, event_type: str) -> bool:
    payload = {
        "communication_id": communication_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                settings.receipts_endpoint,
                json=payload,
            )
            response.raise_for_status()

        logger.info(
            "Receipt posted: comm_id=%d event=%s",
            communication_id,
            event_type,
        )
        return True

    except httpx.HTTPError as exc:
        logger.error(
            "Failed receipt: comm_id=%d event=%s error=%s",
            communication_id,
            event_type,
            str(exc),
        )
        return False


def simulate_clicked(communication_id: int) -> None:
    _post_receipt(communication_id, "clicked")


def simulate_opened(communication_id: int) -> None:
    _post_receipt(communication_id, "opened")

    if random.random() < 0.30:
        delay = random.uniform(5.0, 20.0)
        time.sleep(delay)
        simulate_clicked(communication_id)


def simulate_delivery(communication_id: int) -> None:
    roll = random.random()

    if roll < 0.80:
        _post_receipt(communication_id, "delivered")

        if random.random() < 0.60:
            delay = random.uniform(5.0, 45.0)
            time.sleep(delay)
            simulate_opened(communication_id)

    else:
        _post_receipt(communication_id, "failed")


def start_delivery_thread(
    communication_id: int,
    initial_delay: float,
) -> None:
    def worker():
        time.sleep(initial_delay)
        simulate_delivery(communication_id)

    thread = threading.Thread(
        target=worker,
        daemon=True,
    )

    thread.start()