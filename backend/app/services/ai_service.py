"""
AI Service — integrates with the Google Gemini API using the new google-genai SDK.

Handles natural language segment parsing, message drafting, and insight generation.
"""

import json
import logging
import asyncio
from typing import Any, List, Optional
from pydantic import BaseModel, Field
import re

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Lazy initialization of the GenAI Client ──────────────────────────
_client = None

def _get_client() -> genai.Client:
    """
    Returns a lazily-initialized Google GenAI client.
    Raises ValueError if the GEMINI_API_KEY settings are not configured.
    """
    global _client
    if _client is None:
        api_key = settings.GEMINI_API_KEY
        if not api_key or "your-gemini-api-key" in api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured or contains the placeholder. "
                "Please configure a valid Gemini API key in your .env file."
            )
        api_key = settings.GEMINI_API_KEY

        logger.info("Gemini client initialized successfully")
        _client = genai.Client(api_key=api_key)
    return _client


# ── Pydantic models for structured generation ───────────────────────

class FilterRuleModel(BaseModel):
    field: str = Field(
        ...,
        description="Customer table field: name, phone, email, city, total_spend, order_count, last_purchase_date, created_at"
    )
    op: str = Field(
        ...,
        description="Comparison operator: ==, !=, >, <, >=, <=, in, not_in, contains"
    )
    value: Any = Field(
        ...,
        description="Value to compare. For dates, must be YYYY-MM-DD string. For list comparison (in/not_in), must be a list."
    )


class SegmentIntentModel(BaseModel):
    name: str = Field(
        ...,
        description="Short, descriptive title for this segment (e.g., 'Delhi High Spenders')"
    )
    description: str = Field(
        ...,
        description="A concise summary of what this segment contains (e.g., 'Customers from Delhi with lifetime spend > 5000')"
    )
    filter_rules: List[FilterRuleModel] = Field(
        ...,
        description="List of database filter rules combined with AND logic"
    )
    channel: str = Field(
        default="email",
        description="Predicted communication channel based on user intent: 'sms', 'email', or 'whatsapp'"
    )
    goal: str = Field(
        default="Promote BrewBox coffee and menu items",
        description="Extracted campaign goal (e.g. 'discount offer', 'new item launch')"
    )


class InsightsModel(BaseModel):
    insights: List[str] = Field(
        ...,
        description="A list of exactly 3 to 4 actionable growth marketing insights or recommendations"
    )


# ── Main AI Service Functions ────────────────────────────────────────

async def parse_segment_intent(text: str) -> dict:
    """
    Translate a natural language segment intent into structured DB filters.

    Args:
        text: User description of the segment (e.g., "Delhi customers with lifetime spend > 5000").

    Returns:
        A dictionary matching SegmentIntentModel structure.
    """
    logger.info("Parsing segment intent: %s", text)
    client = _get_client()

    prompt = (
        "Translate the following user marketing intent into a database segment configuration.\n\n"
        f"Intent: \"{text}\"\n\n"
        "Rules:\n"
        "1. Allowed fields are: name, phone, email, city, total_spend, order_count, last_purchase_date, created_at.\n"
        "2. Allowed operators are: ==, !=, >, <, >=, <=, in, not_in, contains.\n"
        "3. For date comparisons (last_purchase_date, created_at), values must be 'YYYY-MM-DD' formatted strings.\n"
        "4. Standardize city names (e.g. capitalize: 'Mumbai', 'Bengaluru', 'Delhi', 'Pune', 'Kolkata', 'Chennai', 'Hyderabad', 'Ahmedabad').\n"
        "5. Keep rules realistic. Choose appropriate fields and values matching the intent.\n"
        "6. Channel MUST be exactly one of: email, sms, whatsapp.\n"
        "7. Never return values like Marketing, Promotion, Campaign, Social Media, Email Marketing, etc.\n"
        "8. The channel field must always be lowercase."
    )

    try:
        logger.info("Gemini Intent Parser called")
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt + """
            Respond with ONLY a valid JSON object matching this schema:

            {
            "name": string,
            "description": string,
            "filter_rules": [
                {
                "field": string,
                "op": string,
                "value": any
                }
            ],
            "channel": "email" | "sms" | "whatsapp",
            "goal": string
            }
            """,
            config=types.GenerateContentConfig(
                temperature=0.1,
            )
        )
        raw = response.text
        if raw:
            clean = raw.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        raise RuntimeError("Empty response from Gemini")
    except Exception as exc:
        logger.error("Failed to parse segment intent via Gemini: %s", str(exc))
        raise RuntimeError(f"AI intent parsing failed: {str(exc)}") from exc


async def generate_campaign_message(segment_desc: str, goal: str, channel: str) -> str:
    """
    Generate an engaging campaign message template targeted at a specific segment.

    Args:
        segment_desc: Description of the target segment.
        goal: The campaign's goal (e.g., promote a new drink, send discount).
        channel: Delivery channel ('sms', 'email', 'whatsapp').

    Returns:
        The drafted message template containing the '{name}' placeholder.
    """
    logger.info("Drafting campaign message for channel: %s, goal: %s", channel, goal)
    client = _get_client()

    channel_rules = ""
    if channel == "sms":
        channel_rules = (
            "Keep it under 160 characters. Make it punchy, direct, and include a clear call to action. "
            "Must include the exact placeholder '{name}' to address the customer."
        )
    elif channel == "whatsapp":
        channel_rules = (
            "Keep it relatively brief, friendly, use emojis to increase engagement, and a casual tone. "
            "Must include the exact placeholder '{name}' to address the customer."
        )
    else:  # email
        channel_rules = (
            "Must start with 'Subject: [Subject Line]' on the first line, followed by a double newline, "
            "then the email body. Tone should be professional yet energetic. "
            "Must include the exact placeholder '{name}' to address the customer."
        )

    prompt = (
        "You are an expert copywriter for 'BrewBox' (a premium coffee chain).\n"
        f"Target Segment: {segment_desc}\n"
        f"Campaign Goal: {goal}\n"
        f"Delivery Channel: {channel}\n\n"
        f"Requirements:\n"
        f"1. You MUST include the exact customer placeholder '{{name}}' in the body.\n"
        f"2. {channel_rules}\n"
        f"3. Focus on coffee-related themes (cappuccino, cold brew, beans) and a welcoming, premium tone.\n"
        f"Do not return any introductory comments, formatting wrapper, or other text besides the message copy itself."
    )

    try:
        logger.info(
            "Gemini Campaign Generator called | channel=%s | goal=%s",
            channel,
            goal
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )
        return response.text.strip()
    except Exception as exc:
        logger.error("Failed to generate campaign message via Gemini: %s", str(exc))
        raise RuntimeError(f"AI message generation failed: {str(exc)}") from exc


async def generate_insights(customer_stats: dict) -> List[str]:
    """
    Analyze aggregated CRM database stats and produce 3 to 4 growth marketing recommendations.

    Args:
        customer_stats: Dict of live database statistics.

    Returns:
        List of 3–4 insight strings.
    """
    logger.info("Generating growth insights from database statistics.")
    

    prompt = (
        "You are the AI growth marketing advisor for the coffee chain 'BrewBox'.\n"
        "Analyze the following database and campaign statistics from XenoCRM and generate "
        "3 to 4 actionable growth insights and recommendations.\n\n"
        f"Database Statistics:\n{json.dumps(customer_stats, indent=2)}\n\n"
        "Requirements:\n"
        "1. Generate exactly 3 to 4 insights.\n"
        "2. Keep each insight action-oriented, specific, and directly tied to the provided stats "
        "(e.g., target specific cities, segment by spending habits, optimize campaign channels).\n"
        "3. Output must be a list of strings, with each string being 1-2 clear sentences."
    )

    try:
        client = _get_client()
        logger.info("Gemini Insights Generator called")
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InsightsModel,
                temperature=0.3,
            )
        )
        parsed_result = response.parsed
        if parsed_result and hasattr(parsed_result, "insights"):
            return parsed_result.insights
        else:
            data = json.loads(response.text)
            if isinstance(data, dict) and "insights" in data:
                return data["insights"]
            elif isinstance(data, list):
                return data
            return ["No insights generated."]
    except Exception as exc:
        logger.error(
            "Failed to generate insights via Gemini: %s",
            str(exc)
        )

        customer_summary = customer_stats.get("customer_summary", {})
        campaign_summary = customer_stats.get("campaign_summary", {})

        return [
            f"Total customers in CRM: {customer_summary.get('total_customers', 0)}",
            f"Total campaigns launched: {campaign_summary.get('total_campaigns', 0)}",
            f"Current delivery rate: {campaign_summary.get('overall_delivery_rate_pct', 0)}%",
            "AI-generated insights are temporarily unavailable. Showing database-based analytics."
        ]


class ChatConfirmationModel(BaseModel):
    confirmed: bool = Field(..., description="True if the user explicitly wants to proceed, launch, run, or approve the campaign/segment.")
    cancelled: bool = Field(..., description="True if the user explicitly cancels, aborts, stops, or says no to launching.")
    updated_name: Optional[str] = Field(None, description="The new campaign name if the user requested to rename it or modify its name.")
    updated_channel: Optional[str] = Field(None, description="The new channel ('sms', 'email', 'whatsapp') if the user requested to change the channel.")
    updated_message: Optional[str] = Field(None, description="The new message template if the user requested to change the message copy.")


async def parse_confirmation(text: str, current_state: dict) -> dict:
    """
    Parse the user's confirmation message during the campaign review step.

    Determines if they confirmed, cancelled, or wanted to modify details.
    """
    logger.info("Parsing chat confirmation message: %s", text)
    client = _get_client()

    prompt = (
        "You are parsing a user's reply to a drafted campaign in XenoCRM.\n"
        f"User Reply: \"{text}\"\n\n"
        f"Current Draft Details:\n{json.dumps(current_state, indent=2)}\n\n"
        "Analyze the user's reply and determine:\n"
        "1. confirmed: Set to true if they confirm, say yes, launch it, approve it, or say 'go ahead'.\n"
        "2. cancelled: Set to true if they say cancel, abort, no, stop, or reject it.\n"
        "3. updated_name: Extract the new name if they want to rename/change the campaign name.\n"
        "4. updated_channel: Extract the new channel ('sms', 'email', 'whatsapp') if they request a channel change.\n"
        "5. updated_message: Extract the new message template if they request to edit/change the message copy."
    )

    for attempt in range(3):
        try:
            logger.info("Gemini Confirmation Parser called")
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt + "\n\nRespond with ONLY valid JSON: {\"confirmed\": bool, \"cancelled\": bool, \"updated_name\": string or null, \"updated_channel\": string or null, \"updated_message\": string or null}",
                config=types.GenerateContentConfig(
                    temperature=0.1,
                )
            )

            raw = response.text

            if raw:
                clean = raw.strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean)

            raise RuntimeError("Empty response from Gemini")

        except Exception as exc:

            if attempt < 2:
                logger.warning(
                    "Gemini confirmation attempt %d failed. Retrying...",
                    attempt + 1
                )
                await asyncio.sleep(2)
                continue

            logger.error(
                "Failed to parse confirmation via Gemini after retries: %s",
                str(exc)
            )

            text_lower = text.strip().lower()

            if text_lower in {
                "yes",
                "y",
                "launch",
                "launch it",
                "send",
                "send it",
                "go ahead",
                "approve",
                "confirm"
            }:
                return {
                    "confirmed": True,
                    "cancelled": False,
                    "updated_name": None,
                    "updated_channel": None,
                    "updated_message": None
                }

            if text_lower in {
                "no",
                "cancel",
                "abort",
                "stop",
                "reject"
            }:
                return {
                    "confirmed": False,
                    "cancelled": True,
                    "updated_name": None,
                    "updated_channel": None,
                    "updated_message": None
                }

            raise RuntimeError(
                f"AI confirmation parsing failed: {str(exc)}"
            ) from exc


def generate_template_campaign(
    segment_desc: str,
    channel: str,
    goal: str = "promotion",
) -> str:
    """
    Fallback campaign generator when Gemini is unavailable.
    """

    if goal == "loyalty":
        return f"""
Hello {{name}},

Thank you for being one of BrewBox's most valued customers.

Audience: {segment_desc}

As a token of our appreciation, we're delighted to offer you an exclusive loyalty reward.

We look forward to serving you again soon.

Warm regards,
BrewBox Team
""".strip()

    if goal == "winback":
        return f"""
Hello {{name}},

We've missed you at BrewBox.

Audience: {segment_desc}

Come back and enjoy a special offer waiting just for you.

We'd love to welcome you again.

Warm regards,
BrewBox Team
""".strip()

    if goal == "upsell":
        return f"""
Hello {{name}},

Thank you for choosing BrewBox.

Audience: {segment_desc}

Based on your previous purchases, we think you'll love our premium drinks and exclusive menu selections.

Visit BrewBox today and discover something new.

Warm regards,
BrewBox Team
""".strip()

    return f"""
Hello {{name}},

We're excited to share exclusive BrewBox offers with our valued audience.

Audience: {segment_desc}

Enjoy handcrafted beverages, loyalty rewards, and special promotions curated for you.

Visit BrewBox today and discover your next favorite brew.

Warm regards,
BrewBox Team
""".strip()

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

    campaign_goal = "promotion"
    customer_tier = "normal"

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

    # Spend Threshold Detection
    spend_match = re.search(
        r"spent\s+(?:over|above|more than)\s*₹?(\d+)",
        text
    )

    if spend_match:
        amount = int(spend_match.group(1))

        rules.append({
            "field": "total_spend",
            "op": ">=",
            "value": amount
        })

        segment_name = f"High Spend {segment_name}"
        description = f"Customers with spend above ₹{amount}"

    # High Value Customers
    if (
        "high value" in text
        or "top spender" in text
        or "top spenders" in text
        or "top 10%" in text
        or "vip" in text
        or "premium" in text
    ):
        rules.append({
            "field": "total_spend",
            "op": ">=",
            "value": 5000
        })

        customer_tier = "vip"
        segment_name = f"VIP {segment_name}"
        description = f"VIP {description}"

    # Order Count Detection
    order_match = re.search(
        r"(?:at least|minimum|more than)\s*(\d+)\s*orders?",
        text
    )

    count = None

    if order_match:
        count = int(order_match.group(1))

    
        rules.append({
            "field": "order_count",
            "op": ">=",
            "value": count
        })

        segment_name = f"Frequent Buyers {segment_name}"
        description = f"{description} with at least {count} orders"


    if "first-time" in text or "first purchase" in text:
        rules.append({
            "field": "order_count",
            "op": "==",
            "value": 1
        })

        segment_name = f"First-Time {segment_name}"
        description = f"First-time buyer {description}"


    # Repeat / Frequent Buyers
    if (
        "repeat" in text
        or "frequent" in text
        or "loyal" in text
    ):
        rules.append({
            "field": "order_count",
            "op": ">=",
            "value": 3
        })

        segment_name = f"Repeat {segment_name}"
        description = f"Repeat purchase {description}"

    # First-Time Buyers
    if (
        "first-time" in text
        or "first time" in text
        or "first-order" in text
        or "first order" in text
        or "first purchase" in text
    ):
        rules.append({
            "field": "order_count",
            "op": "==",
            "value": 1
        })

        customer_tier = "first_time"
        segment_name = f"First-Time Buyers {segment_name}"
        description = f"First-time buyer {description}"

    # Campaign Goal Detection
    if "loyalty" in text or "reward" in text:
        campaign_goal = "loyalty"

    elif (
        "re-engage" in text
        or "inactive" in text
        or "haven't visited" in text
        or "discount" in text
    ):
        campaign_goal = "winback"

    elif "upsell" in text:
        campaign_goal = "upsell"

    return {
        "name": segment_name,
        "description": description,
        "channel": channel,
        "goal": campaign_goal,
        "customer_tier": customer_tier,
        "filter_rules": rules,
    }