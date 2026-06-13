"""
Insights API Router.

Computes live database statistics and passes them to the AI service
to generate growth recommendations and insights for the marketer.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal


from app.core.database import get_db
from app.models.customer import Customer
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.services.ai_service import generate_insights

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/insights", tags=["Insights"])


@router.get("", response_model=List[str])
async def get_insights_endpoint(
    db: AsyncSession = Depends(get_db),
) -> List[str]:
    """
    Get AI-generated growth marketing insights.

    Aggregates live DB customer metrics, purchase patterns, and campaign performance,
    then prompts Gemini to deliver 3-4 proactive insights.
    """
    try:
        # ── 1. Gather Customer Stats ──────────────────────────────────
        cust_count_res = await db.execute(select(func.count(Customer.id)))
        total_customers = cust_count_res.scalar_one() or 0

        avg_spend_res = await db.execute(select(func.avg(Customer.total_spend)))
        avg_spend = float(avg_spend_res.scalar_one() or 0)

        avg_orders_res = await db.execute(select(func.avg(Customer.order_count)))
        avg_orders = float(avg_orders_res.scalar_one() or 0)

        total_spend_res = await db.execute(select(func.sum(Customer.total_spend)))
        total_spend = float(total_spend_res.scalar_one() or 0)

        # ── 2. Gather City Stats ──────────────────────────────────────
        city_res = await db.execute(
            select(
                Customer.city,
                func.count(Customer.id).label("count"),
                func.sum(Customer.total_spend).label("spend")
            )
            .group_by(Customer.city)
            .order_by(func.count(Customer.id).desc())
            .limit(5)
        )
        top_cities = [
            {
                "city": row[0],
                "customer_count": row[1],
                "total_spend": round(float(row[2] or 0), 2)
            }
            for row in city_res.all()
        ]

        # ── 3. Gather Campaign Stats ──────────────────────────────────
        camp_count_res = await db.execute(select(func.count(Campaign.id)))
        total_campaigns = camp_count_res.scalar_one() or 0

        comm_count_res = await db.execute(select(func.count(Communication.id)))
        total_communications = comm_count_res.scalar_one() or 0

        # Aggregate statuses
        status_res = await db.execute(
            select(Communication.status, func.count(Communication.id))
            .group_by(Communication.status)
        )
        status_counts = dict(status_res.all())

        total_delivered = sum(
            status_counts.get(s, 0) for s in ["delivered", "opened", "read", "clicked"]
        )
        total_opened = sum(status_counts.get(s, 0) for s in ["opened", "read", "clicked"])
        total_clicked = status_counts.get("clicked", 0) + status_counts.get("read", 0)

        delivery_rate = (total_delivered / total_communications * 100) if total_communications > 0 else 0.0
        open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0.0
        click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0.0

        # Compile final stats payload for AI
        stats_payload = {
            "customer_summary": {
                "total_customers": total_customers,
                "total_spend": round(total_spend, 2),
                "avg_spend_per_customer": round(avg_spend, 2),
                "avg_orders_per_customer": round(avg_orders, 1)
            },
            "top_cities": top_cities,
            "campaign_summary": {
                "total_campaigns": total_campaigns,
                "total_messages_sent": total_communications,
                "overall_delivery_rate_pct": round(delivery_rate, 1),
                "overall_open_rate_pct": round(open_rate, 1),
                "overall_click_rate_pct": round(click_rate, 1)
            }
        }

        # ── 4. Call AI Service ────────────────────────────────────────
        insights = await generate_insights(stats_payload)
        return insights

    except ValueError as exc:
        # Catch settings/configuration errors (e.g. missing API key)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to generate growth insights: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(exc)}")
