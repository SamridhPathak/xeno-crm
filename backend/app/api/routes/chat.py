"""
Chat API Router — XenoCRM Hero Endpoint.

Handles multi-turn conversational onboarding for campaign creation:
1. Parse segment intent, query database for preview and size, draft message template.
2. Maintain wizard state in the request session.
3. Finalize and launch campaign upon user confirmation.
"""

from app.services.ai_service import (
    parse_segment_intent,
    generate_campaign_message,
    parse_confirmation,
    parse_segment_intent_rules,
    generate_template_campaign,
)

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.segment import Segment
from app.models.campaign import Campaign
from app.services.ai_service import (
    parse_segment_intent,
    generate_campaign_message,
    parse_confirmation,
)
from app.services.segment_service import (
    count_segment_customers,
    get_segment_customers,
)
from app.services.campaign_service import launch_campaign

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


# ── Pydantic Request/Response Schemas ────────────────────────────────

class SessionState(BaseModel):
    step: str = Field("initial", description="Current step in the wizard: initial or confirm")
    segment: Optional[Dict[str, Any]] = Field(None, description="Current parsed segment metadata and filter rules")
    draft_campaign: Optional[Dict[str, Any]] = Field(None, description="Current campaign draft details (name, channel, template)")


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="The user's chat message input.")
    session_state: Optional[SessionState] = Field(None, description="Conversation session state passed back from frontend.")


class PreviewData(BaseModel):
    segment_name: str
    segment_description: str
    customer_count: int
    sample_customers: List[str]
    draft_message: str
    channel: str


class ChatMessageResponse(BaseModel):
    reply: str = Field(..., description="Markdown response text for the user.")
    session_state: SessionState = Field(..., description="Updated conversation session state.")
    preview: Optional[PreviewData] = Field(None, description="Structured preview data for UI rendering.")


# ── Route Handler ───────────────────────────────────────────────────

@router.post("", response_model=ChatMessageResponse)
async def chat_endpoint(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """
    Stateful CRM Copilot Chat interface.

    Allows marketers to define a segment, preview target customers, draft campaign copy,
    and launch a campaign entirely through natural language.
    """
    user_message = payload.message.strip()
    state = payload.session_state or SessionState()

    # If the user input is empty, do nothing
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # ── STEP 1: INITIAL STATE (Parse Intent & Draft Campaign) ────────
    if state.step == "initial":
        try:
            # Parse natural language intent into segment query
            parsed = await parse_segment_intent(user_message)
        
        except Exception:
            logger.warning(
                "Gemini unavailable. Switching to Smart Rules Mode."
            )

            parsed = parse_segment_intent_rules(user_message)
            logger.warning("SMART RULES PARSED: %s", parsed)

        rules = parsed.get("filter_rules", [])
        if not rules:
            return ChatMessageResponse(
                reply="I couldn't identify any clear segment criteria in your message. Could you try specifying a city or spend amount? For example: 'Find customers in Mumbai who ordered at least 3 times.'",
                session_state=state,
            )

        # Count matching customers from the DB to preview the size
        try:
            customer_count = await count_segment_customers(db, rules)
            # Fetch a sample of 3 customers
            samples = await get_segment_customers(db, rules, limit=3)
            sample_names = [c.name for c in samples]
        except Exception as exc:
            logger.error("Failed to query DB for segment preview: %s", str(exc))
            raise HTTPException(status_code=400, detail=f"Database query failed for rules generated: {str(exc)}")

        # Draft campaign message
        channel = parsed.get("channel", "email")
        goal = parsed.get("goal", "Promote BrewBox menu items with a special discount")
        segment_desc = parsed.get("description", "Target Audience")

        try:
            draft_message = await generate_campaign_message(segment_desc, goal, channel)
        except Exception:
            logger.warning(
                "Gemini draft generation unavailable. Using template mode."
            )

            draft_message = generate_template_campaign(
                segment_desc,
                channel,
                parsed.get("goal", "promotion")
            )

        # Construct copilot reply
        sample_text = ", ".join(sample_names) if sample_names else "No matching customers found"
        reply = (
            f"🔍 I've parsed your segment intent:\n"
            f"- **Segment Name**: {parsed['name']}\n"
            f"- **Target Audience**: {segment_desc}\n"
            f"- **Audience Size**: **{customer_count}** customer(s) matched\n"
            f"- **Samples**: {sample_text}\n\n"
            f"✍️ I've drafted a campaign template for **{channel.upper()}**:\n"
            f"```\n{draft_message}\n```\n\n"
            f"Would you like me to launch this campaign? Reply with **'Yes'** to launch it immediately. "
            f"Alternatively, you can request modifications (e.g. 'change channel to whatsapp' or 'rename the campaign to Summer Promo')."
        )

        # Update and return state
        next_state = SessionState(
            step="confirm",
            segment={
                "name": parsed["name"],
                "description": segment_desc,
                "filter_rules": rules,
            },
            draft_campaign={
                "name": f"Campaign: {parsed['name']}",
                "channel": channel,
                "message_template": draft_message,
            }
        )

        preview = PreviewData(
            segment_name=parsed["name"],
            segment_description=segment_desc,
            customer_count=customer_count,
            sample_customers=sample_names,
            draft_message=draft_message,
            channel=channel,
        )

        return ChatMessageResponse(reply=reply, session_state=next_state, preview=preview)

    # ── STEP 2: CONFIRMATION STATE (Finalize, Create & Launch) ───────
    elif state.step == "confirm":
        if not state.segment or not state.draft_campaign:
            # Fallback if state got lost
            state.step = "initial"
            return ChatMessageResponse(
                reply="Sorry, I lost track of the campaign draft. What would you like to do?",
                session_state=state
            )

        try:
            # Send message to Gemini to classify confirmation/modification intent
            action = await parse_confirmation(
                user_message,
                state.model_dump()
            )

        except Exception:
            logger.warning(
                "Gemini confirmation unavailable. Using fallback confirmation parser."
            )

            text_lower = user_message.strip().lower()

            updated_channel = None

            if "whatsapp" in text_lower:
                updated_channel = "whatsapp"
            elif "sms" in text_lower:
                updated_channel = "sms"
            elif "email" in text_lower:
                updated_channel = "email"

            action = {
                "confirmed": text_lower in {
                    "yes",
                    "y",
                    "launch",
                    "launch it",
                    "send",
                    "send it",
                    "go",
                    "go ahead",
                    "confirm",
                    "proceed",
                },
                "cancelled": text_lower in {
                    "cancel",
                    "stop",
                    "abort",
                    "reject",
                    "no",
                },
                "updated_name": None,
                "updated_channel": updated_channel,
                "updated_message": None,
            }

        # Handle Cancel
        if action.get("cancelled"):
            return ChatMessageResponse(
                reply="Campaign draft cancelled. What segment would you like to build next?",
                session_state=SessionState(step="initial"),
            )

        # Handle Modifications (user wants to change name, channel, or message)
        modified = False
        updated_draft = state.draft_campaign.copy()

        if action.get("updated_name"):
            updated_draft["name"] = action["updated_name"]
            modified = True
        if action.get("updated_channel"):
            updated_draft["channel"] = action["updated_channel"].lower()
            modified = True
        if action.get("updated_message"):
            updated_draft["message_template"] = action["updated_message"]
            modified = True

        if modified and not action.get("confirmed"):
            # Update state draft with changes and regenerate message if channel changed without a custom message
            state.draft_campaign = updated_draft
            
            # Re-evaluate campaign size just in case, and generate new message if channel changed but no message provided
            rules = state.segment["filter_rules"]
            customer_count = await count_segment_customers(db, rules)
            samples = await get_segment_customers(db, rules, limit=3)
            sample_names = [c.name for c in samples]

            # If channel changed and user didn't write a specific message body, draft a new one for that channel
            if action.get("updated_channel") and not action.get("updated_message"):
                try:
                    new_template = await generate_campaign_message(
                        state.segment["description"],
                        "Promote BrewBox menu items with a special discount",
                        updated_draft["channel"]
                    )
                    updated_draft["message_template"] = new_template
                except Exception:
                    pass

            reply = (
                f"I've updated the campaign copy details as requested:\n"
                f"- **Campaign Name**: {updated_draft['name']}\n"
                f"- **Channel**: {updated_draft['channel'].upper()}\n\n"
                f"Drafted Message template:\n"
                f"```\n{updated_draft['message_template']}\n```\n\n"
                f"Would you like me to launch this now? Reply with **'Yes'** to confirm."
            )

            preview = PreviewData(
                segment_name=state.segment["name"],
                segment_description=state.segment["description"],
                customer_count=customer_count,
                sample_customers=sample_names,
                draft_message=updated_draft["message_template"],
                channel=updated_draft["channel"],
            )

            return ChatMessageResponse(reply=reply, session_state=state, preview=preview)

        # Handle Confirmation (Proceed to Launch)
        if action.get("confirmed") or user_message.lower() in ("yes", "y", "launch", "go", "confirm", "proceed"):
            final_name = updated_draft["name"]
            final_channel = updated_draft["channel"].lower()

              # Normalize AI output
            channel_map = {
                "marketing": "email",
                "email": "email",
                "sms": "sms",
                "whatsapp": "whatsapp"
        }   

            final_channel = channel_map.get(final_channel, "email")

            final_template = updated_draft["message_template"]

            # Save the segment
            rules = state.segment["filter_rules"]
            customer_count = await count_segment_customers(db, rules)

            # Create DB Segment
            db_segment = Segment(
                name=state.segment["name"],
                description=state.segment["description"],
                filter_rules=rules,
                customer_count=customer_count
            )
            db.add(db_segment)
            await db.flush()

            final_channel = updated_draft["channel"].lower()

            channel_map = {
                "marketing": "email",
                "email": "email",
                "sms": "sms",
                "whatsapp": "whatsapp"
            }

            final_channel = channel_map.get(final_channel, "email")

            # Create DB Campaign
            db_campaign = Campaign(
                name=final_name,
                segment_id=db_segment.id,
                message_template=final_template,
                channel=final_channel,
                status="draft"
            )
            db.add(db_campaign)
            await db.flush()

            # Launch the campaign asynchronously to the channel service
            try:
                launch_result = await launch_campaign(db, db_campaign.id)
                logger.info("Campaign launched from chat: %s", str(launch_result))
            except Exception as exc:
                logger.error("Failed to launch campaign from chat: %s", str(exc))
                raise HTTPException(
                    status_code=500,
                    detail=f"Segment/Campaign created, but launch failed: {str(exc)}"
                )

            reply = (
                f"🚀 **Campaign launched successfully!**\n\n"
                f"- **Campaign**: *{final_name}*\n"
                f"- **Segment**: *{state.segment['name']}*\n"
                f"- **Target Recipients**: **{customer_count}** customer(s)\n"
                f"- **Channel**: {final_channel.upper()}\n\n"
                f"Message sent:\n"
                f"```\n{final_template}\n```\n\n"
                f"The channel service is dispatching messages and will stream callbacks back in real-time. "
                f"You can view the delivery charts in the dashboard. What else can I help you with?"
            )

            return ChatMessageResponse(reply=reply, session_state=SessionState(step="initial"))

        # User sent a message that didn't match cancel, modification or confirm
        reply = (
            "I'm waiting for your confirmation to launch the campaign. "
            "Reply with **'Yes'** to send, **'Cancel'** to cancel, or ask for changes."
        )
        return ChatMessageResponse(reply=reply, session_state=state)

    # Unknown step
    state.step = "initial"
    return ChatMessageResponse(
        reply="Something went wrong. Let's restart the campaign creation. Describe your target segment:",
        session_state=state
    )
