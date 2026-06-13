"""
Channel Service — FastAPI Application Entry Point.

A lightweight service that accepts campaign send requests from
the CRM backend and simulates message delivery via Celery tasks.

The /send endpoint returns 200 immediately (non-blocking), while
Celery workers process delivery simulation in the background and
POST receipt callbacks to the CRM.
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.simulator import process_send_request

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── FastAPI Application ──────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Simulated message delivery service for XenoCRM. "
        "Accepts send requests, simulates delivery outcomes "
        "(delivered/failed/opened/clicked), and fires callbacks."
    ),
)

# ── CORS Middleware ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class Recipient(BaseModel):
    """A single message recipient."""
    communication_id: int
    customer_name: str = ""
    customer_email: str = ""
    customer_phone: str = ""
    message: str = ""


class SendRequest(BaseModel):
    """
    Payload from the CRM backend's campaign launch.

    Contains the campaign metadata, delivery channel, CRM callback
    URL, and the full list of recipients with their personalised
    messages.
    """
    campaign_id: int = Field(..., description="CRM campaign ID.")
    channel: str = Field(..., description="Delivery channel: sms, email, whatsapp.")
    callback_url: str = Field(..., description="CRM receipts endpoint URL.")
    recipients: list[Recipient] = Field(
        ..., min_length=1,
        description="List of recipients to deliver messages to.",
    )


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@app.post("/send", status_code=200)
async def send_messages(payload: SendRequest) -> dict[str, Any]:
    """
    Accept a campaign send request and begin simulated delivery.

    Returns 200 immediately — all delivery simulation happens
    asynchronously via Celery background tasks. The CRM will
    receive delivery receipts at the callback_url as messages
    are "delivered", "opened", and "clicked".

    Delivery timeline:
        - 1-3s:   80% delivered, 20% failed
        - 5-8s:   60% of delivered → opened
        - 10-15s: 30% of opened → clicked
    """
    logger.info(
        "📬 Received send request: campaign=%d channel=%s recipients=%d",
        payload.campaign_id, payload.channel, len(payload.recipients),
    )

    # Convert Pydantic models to dicts for the simulator.
    recipients_data = [r.model_dump() for r in payload.recipients]

    try:
        result = process_send_request(
            campaign_id=payload.campaign_id,
            channel=payload.channel,
            callback_url=payload.callback_url,
            recipients=recipients_data,
        )
    except Exception as exc:
        logger.error("Send request failed: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Send simulation failed: {str(exc)}")

    return {
        "status": "accepted",
        "message": (
            f"Delivery simulation started for {result['dispatched']} "
            f"recipients on {payload.channel}."
        ),
        **result,
    }


# ── Health Check ─────────────────────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check for monitoring and deploy probes."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
