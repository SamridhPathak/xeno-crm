"""
Segment service — translates JSON filter rules into SQLAlchemy queries.

This is the bridge between AI-generated intent (JSON filter rules)
and actual database queries. Supports all comparison operators
the AI might produce.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Select, and_, cast, Date, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer


# ═══════════════════════════════════════════════════════════════════
# OPERATOR MAPPING
# ═══════════════════════════════════════════════════════════════════

# Maps string operators from filter rules to SQLAlchemy column comparisons.
# Each function takes (column, value) and returns a BinaryExpression.
OPERATOR_MAP = {
    "==": lambda col, val: col == val,
    "!=": lambda col, val: col != val,
    ">": lambda col, val: col > val,
    "<": lambda col, val: col < val,
    ">=": lambda col, val: col >= val,
    "<=": lambda col, val: col <= val,
    "in": lambda col, val: col.in_(val if isinstance(val, list) else [val]),
    "not_in": lambda col, val: col.notin_(val if isinstance(val, list) else [val]),
    "contains": lambda col, val: col.ilike(f"%{val}%"),
}

# Fields that should be compared as dates (parse string values).
DATE_FIELDS = {"last_purchase_date", "created_at"}

# Valid customer fields that can be filtered on.
ALLOWED_FIELDS = {
    "name", "phone", "email", "city",
    "total_spend", "order_count", "last_purchase_date", "created_at",
}


def _coerce_value(field: str, value: Any) -> Any:
    """
    Coerce a filter value to the correct Python type for the field.

    The AI might return date strings or numeric strings — this ensures
    proper type matching against the database column.
    """
    if field in DATE_FIELDS and isinstance(value, str):
        # Try ISO date format first, then datetime.
        try:
            return date.fromisoformat(value)
        except ValueError:
            return datetime.fromisoformat(value).date()
    return value


def build_customer_query(filter_rules: list[dict[str, Any]]) -> Select:
    """
    Build a SQLAlchemy SELECT query from a list of filter rule dicts.

    Args:
        filter_rules: List of {"field": ..., "op": ..., "value": ...} dicts.

    Returns:
        A SQLAlchemy Select statement filtered by all rules (AND logic).

    Raises:
        ValueError: If an unknown field or operator is encountered.
    """
    query = select(Customer)
    conditions = []

    for rule in filter_rules:
        field_name = rule.get("field", "")
        op = rule.get("op", "==")
        value = rule.get("value")

        # Validate field name against allowed set to prevent injection.
        if field_name not in ALLOWED_FIELDS:
            raise ValueError(
                f"Unknown filter field: '{field_name}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_FIELDS))}"
            )

        # Validate operator.
        if op not in OPERATOR_MAP:
            raise ValueError(
                f"Unknown operator: '{op}'. "
                f"Allowed: {', '.join(sorted(OPERATOR_MAP.keys()))}"
            )

        # Get the SQLAlchemy column from the Customer model.
        column = getattr(Customer, field_name)

        # Coerce value to the right type.
        coerced_value = _coerce_value(field_name, value)

        # Handle 'in' operator with list of values that may need coercion.
        if op in ("in", "not_in") and isinstance(coerced_value, list):
            coerced_value = [_coerce_value(field_name, v) for v in coerced_value]

        # Build the condition.
        if coerced_value is None:
            continue
        
        condition = OPERATOR_MAP[op](column, coerced_value)
        conditions.append(condition)

    if conditions:
        query = query.where(and_(*conditions))

    return query


async def count_segment_customers(
    db: AsyncSession,
    filter_rules: list[dict[str, Any]],
) -> int:
    """
    Count how many customers match the given filter rules.

    Used when creating a segment to populate the customer_count field.
    """
    query = build_customer_query(filter_rules)
    # Replace the select columns with a count.
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    return result.scalar_one()


async def get_segment_customers(
    db: AsyncSession,
    filter_rules: list[dict[str, Any]],
    limit: int | None = None,
    offset: int = 0,
) -> list[Customer]:
    """
    Fetch customers matching the given filter rules.

    Used both for segment preview and campaign targeting.
    """
    query = build_customer_query(filter_rules).order_by(Customer.id)
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())



import re

def parse_segment_intent_rules(user_message: str) -> dict:
    """
    Fallback parser when Gemini is unavailable.
    """

    text = user_message.lower()

    channel = "email"

    if "whatsapp" in text:
        channel = "whatsapp"
    elif "sms" in text:
        channel = "sms"

    cities = [
        "delhi",
        "mumbai",
        "pune",
        "bangalore",
        "bengaluru",
        "hyderabad",
        "chennai",
        "kolkata",
    ]

    city_found = None

    for city in cities:
        if city in text:
            city_found = city.title()
            break

    rules = []
    segment_name = "All Customers"
    description = "All customers"

    if city_found:
        rules.append({
            "field": "city",
            "op": "==",
            "value": city_found
        })

        segment_name = f"Customers in {city_found}"
        description = f"Customers located in {city_found}"

    if "high value" in text:
        rules.append({
            "field": "total_spend",
            "op": ">=",
            "value": 5000
        })

        segment_name = f"High Value {segment_name}"
        description = f"High value {description}"

    if "repeat" in text:
        rules.append({
            "field": "order_count",
            "op": ">=",
            "value": 3
        })

        segment_name = f"Repeat {segment_name}"
        description = f"Repeat purchase {description}"

    return {
        "name": segment_name,
        "description": description,
        "channel": channel,
        "goal": "Promote BrewBox menu items",
        "filter_rules": rules,
    }