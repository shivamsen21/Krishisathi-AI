import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends

from schemas.chatbot import ChatRequest, ChatResponse, ChatMessageResponse
from services.supabase_service import supabase_service
from dependencies import get_optional_user, get_current_user

logger = logging.getLogger("agrovision.routes.chatbot")
router = APIRouter(prefix="/api/chat", tags=["Agricultural Assistant"])

# Knowledge base answers for common agronomic topics
AGRI_KNOWLEDGE = [
    {
        "keywords": ["tomato", "brown", "spot", "blight"],
        "reply": "Brown spots on tomato leaves are frequently caused by <strong>Early Blight</strong> (<em>Alternaria solani</em>). 🍅\n\n<b>Recommended Steps:</b>\n• Remove and destroy infected lower leaves\n• Apply copper-based fungicide or mancozeb every 7–10 days\n• Avoid overhead irrigation to keep foliage dry\n• Ensure wide spacing between plants for adequate airflow\n\nUpload a leaf photo to our <a href='detection.html' style='color:var(--primary);font-weight:600;'>AI Disease Detection</a> tool for instant confirmation!"
    },
    {
        "keywords": ["fungal", "fungus", "prevent", "prevention"],
        "reply": "Proven strategies to prevent fungal outbreaks in your crops: 🌿\n\n<b>Cultural Management:</b>\n• Rotate plant families every season (avoid nightshades successively)\n• Choose certified disease-resistant seed varieties\n• Avoid standing water and ensure well-draining soil ridges\n• Clear and burn or bury infected harvest debris\n\n<b>Protective Sprays:</b>\n• Apply preventive bio-fungicides (e.g., <em>Trichoderma viride</em>)\n• Use protective copper hydroxide at early vegetative stages"
    },
    {
        "keywords": ["water", "wheat", "irrigat"],
        "reply": "Wheat water requirements across critical growth stages: 🌾\n\n<b>Key Irrigation Windows:</b>\n1. Crown Root Initiation (CRI) — 20–25 days after sowing (most critical!)\n2. Tillering stage — 40–45 days\n3. Jointing stage — 65–70 days\n4. Flowering & Grain filling — 90–95 days\n\nGenerally, 4 to 6 light irrigations produce optimal grain yield without waterlogging root zones."
    },
    {
        "keywords": ["potato", "late blight", "rot"],
        "reply": "Common potato leaf & tuber diseases: 🥔\n\n1. <strong>Late Blight</strong> — Fast-spreading dark water-soaked lesions; spray systemic metalaxyl-M or cymoxanil.\n2. <strong>Early Blight</strong> — Concentric bullseye rings on mature leaves; apply chlorothalonil.\n3. <strong>Common Scab</strong> — Corky surface lesions; maintain soil pH between 5.0–5.2.\n4. <strong>Black Leg</strong> — Bacterial stem rot; always plant certified pathogen-free seed tubers."
    },
    {
        "keywords": ["spray", "pesticide", "timing", "when"],
        "reply": "Optimal agricultural spraying guidelines: ⏰\n\n<b>Timing:</b>\n• Early morning (6:00 – 9:00 AM) or late afternoon (4:30 – 6:30 PM)\n• Avoid midday heat when rapid chemical evaporation occurs\n• Avoid spraying when rain is forecast within 4 to 6 hours\n\n<b>Field Conditions:</b>\n• Wind velocity below 10 km/h to prevent spray drift\n• Temperature under 30°C\n• Always wear protective gloves and respirator mask"
    },
    {
        "keywords": ["soil", "fertilizer", "organic", "manure", "compost"],
        "reply": "Natural soil enrichment practices: 🌱\n\n1. <strong>Well-rotted Farmyard Manure (FYM):</strong> Apply 10–12 tons/ha during land preparation.\n2. <strong>Green Manuring:</strong> Incorporate Sunnhemp or Dhaincha 45 days after germination.\n3. <strong>Biofertilizers:</strong> Seed treatment with <em>Rhizobium</em> (for legumes) and <em>Azotobacter</em> / <em>PSB</em> (for cereals).\n4. <strong>Mulching:</strong> Spread straw or organic mulch to conserve moisture and foster beneficial microbes."
    }
]

DEFAULT_BOT_REPLY = (
    "Thank you for reaching out to Krishi AI! 🌿\n\n"
    "I am your dedicated digital agronomist. To give you the most accurate prescription, "
    "could you tell me:\n"
    "• Which crop are you currently cultivating?\n"
    "• What specific symptoms are visible (color, spot shape, wilting)?\n"
    "• Have you noticed any pests on the leaf undersides?\n\n"
    "You can also upload a close-up photo of the affected leaf in our "
    "<a href='detection.html' style='color:var(--primary);font-weight:600;'>Disease Detection</a> tool."
)

def generate_bot_reply(message: str) -> str:
    msg_lower = message.lower()
    for item in AGRI_KNOWLEDGE:
        if any(kw in msg_lower for kw in item["keywords"]):
            return item["reply"]
    return DEFAULT_BOT_REPLY

@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Handle a user conversation query:
    1. Generates agronomic answer.
    2. Persists the conversation exchange in Supabase chat_messages if user is authenticated.
    """
    reply_text = generate_bot_reply(data.message)

    msg_id = None
    if current_user:
        user_id = current_user["id"]
        # Save user message
        supabase_service.add_chat_message(user_id=user_id, role="user", message=data.message)
        # Save bot response
        bot_record = supabase_service.add_chat_message(user_id=user_id, role="assistant", message=reply_text)
        msg_id = bot_record.get("id")

    return ChatResponse(
        reply=reply_text,
        message_id=msg_id,
        role="assistant"
    )

@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieve previous chat conversation messages for the authenticated user.
    """
    history = supabase_service.get_chat_history(user_id=current_user["id"], limit=50)
    return [
        ChatMessageResponse(
            id=str(m.get("id")),
            user_id=m.get("user_id"),
            role=m.get("role", "assistant"),
            message=m.get("message", ""),
            created_at=m.get("created_at", "")
        )
        for m in history
    ]
