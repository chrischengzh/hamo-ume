"""
Gemini AI Service Module

Integrates with Google's Gemini API for therapeutic response generation
and message analysis for PSVS stress indicators.
"""

import google.generativeai as genai
from typing import Dict, List, Any, Optional
import re
from .config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GENERATION_CONFIG,
)


# Initialize Gemini client
_gemini_client = None


def initialize_gemini(api_key: Optional[str] = None) -> None:
    """
    Initialize Gemini API client.

    Args:
        api_key: Optional API key (uses default from config if not provided)
    """
    global _gemini_client
    key = api_key or GEMINI_API_KEY
    genai.configure(api_key=key)
    _gemini_client = genai.GenerativeModel(GEMINI_MODEL)


def get_gemini_client():
    """Get initialized Gemini client, initializing if needed."""
    global _gemini_client
    if _gemini_client is None:
        initialize_gemini()
    return _gemini_client


def generate_response(
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Generate therapeutic response using Gemini.

    Args:
        system_prompt: Complete system prompt with role, policy, value, search
        user_message: User's latest message
        conversation_history: Optional list of previous messages [{"role": "user"|"model", "content": "..."}]

    Returns:
        Generated response text
    """
    client = get_gemini_client()

    # Build conversation context
    messages = []

    # Add system context as first user message
    messages.append({
        "role": "user",
        "parts": [f"[SYSTEM CONTEXT - READ CAREFULLY]\n\n{system_prompt}\n\n[END SYSTEM CONTEXT]\n\nPlease acknowledge you understand your role and the therapeutic framework."]
    })
    messages.append({
        "role": "model",
        "parts": ["I understand my role and the PSVS therapeutic framework. I'm ready to provide supportive, guided therapy based on the client's current position and needs."]
    })

    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = "model" if msg.get("role") == "assistant" else "user"
            messages.append({
                "role": role,
                "parts": [msg.get("content", "")]
            })

    # Add current user message
    messages.append({
        "role": "user",
        "parts": [user_message]
    })

    # Generate response
    try:
        chat = client.start_chat(history=messages[:-1])
        response = chat.send_message(
            user_message,
            generation_config=genai.types.GenerationConfig(**GENERATION_CONFIG)
        )
        return response.text
    except Exception as e:
        # Fallback response if API fails
        return f"I'm here to support you. I apologize, but I'm having trouble processing right now. Could you tell me more about what you're experiencing? [Error: {str(e)}]"


def analyze_message_for_stress(message: str) -> Dict[str, float]:
    """
    Analyze user message to extract stress indicators (A/W/E/H/B).

    Based on status_transform.json:
    - A (Agency): action-oriented, responsibility-taking
    - W (Withdrawal): disengagement, avoidance, delay
    - E (Extremity): all-or-nothing, absolutism
    - H (Hostility): coercion, threats, insults
    - B (Boundary): respect, clarification, alignment

    Args:
        message: User's message text

    Returns:
        Dict with A, W, E, H, B scores (0.0-3.0 scale)
    """
    message_lower = message.lower()

    # Initialize scores
    scores = {
        "A": 0.0,  # Agency
        "W": 0.0,  # Withdrawal
        "E": 0.0,  # Extremity
        "H": 0.0,  # Hostility
        "B": 0.0,  # Boundary
    }

    # Agency indicators (positive actions, taking responsibility)
    agency_patterns = [
        r"\b(i will|i'll|i'm going to|i plan to|i'm taking|i decided|i choose)\b",
        r"\b(my responsibility|i can|i'm able to|let me|i'll handle)\b",
        r"\b(step by step|next step|action plan|i'll start|i'm working on)\b",
        r"\b(我会|我要|我打算|我决定|我选择|我能|我来)\b",
    ]
    for pattern in agency_patterns:
        if re.search(pattern, message_lower):
            scores["A"] += 0.5

    # Withdrawal indicators (avoidance, delay, disengagement)
    withdrawal_patterns = [
        r"\b(whatever|doesn't matter|don't care|i don't mind|not sure|maybe later)\b",
        r"\b(avoid|ignore|put off|delay|postpone|can't deal|too hard)\b",
        r"\b(i give up|no point|why bother|hopeless|helpless)\b",
        r"\b(随便|无所谓|不在乎|算了|懒得|回避|拖延)\b",
    ]
    for pattern in withdrawal_patterns:
        if re.search(pattern, message_lower):
            scores["W"] += 0.6

    # Extremity indicators (all-or-nothing, absolutism)
    extremity_patterns = [
        r"\b(always|never|everyone|no one|everything|nothing|all or)\b",
        r"\b(completely|totally|absolutely|must|can't|impossible)\b",
        r"\b(every time|all the time|nobody|everybody)\b",
        r"\b(总是|从不|所有人|没人|一切|什么都|绝对|必须|不可能)\b",
    ]
    for pattern in extremity_patterns:
        matches = len(re.findall(pattern, message_lower))
        scores["E"] += min(matches * 0.4, 2.0)

    # Hostility indicators (coercion, threats, insults, attacks)
    hostility_patterns = [
        r"\b(my way or|do it now|you must|you have to|shut up|stupid|idiot)\b",
        r"\b(i hate|i'll make you|you better|or else|threaten)\b",
        r"\b(pathetic|worthless|useless|disgusting|piece of)\b",
        r"\b(要么|必须|闭嘴|蠢|白痴|恨|威胁|废物|垃圾)\b",
    ]
    for pattern in hostility_patterns:
        if re.search(pattern, message_lower):
            scores["H"] += 1.0  # High weight for hostility

    # Boundary indicators (respect, clarification, alignment)
    boundary_patterns = [
        r"\b(respect|clarify|understand|align|boundary|scope|clear)\b",
        r"\b(let's discuss|can we talk|i'd like to|what if|help me understand)\b",
        r"\b(i need|i feel|from my perspective|it seems)\b",
        r"\b(尊重|澄清|理解|边界|范围|讨论|我需要|我觉得)\b",
    ]
    for pattern in boundary_patterns:
        if re.search(pattern, message_lower):
            scores["B"] += 0.4

    # Cap all scores at reasonable maximums
    for key in scores:
        scores[key] = min(scores[key], 3.0)

    return scores


def should_skip_psvs_update(message: str) -> bool:
    """
    Determine if message is too short/meaningless to warrant PSVS update.

    Args:
        message: User's message

    Returns:
        True if should skip PSVS update, False otherwise
    """
    from .config import MIN_MESSAGE_LENGTH_FOR_PSVS_UPDATE

    # Remove whitespace and check length
    cleaned = message.strip()

    # Skip very short messages
    if len(cleaned) < MIN_MESSAGE_LENGTH_FOR_PSVS_UPDATE:
        return True

    # Skip common short responses
    short_responses = {
        "ok", "okay", "k", "yes", "no", "yeah", "nope", "yep", "sure",
        "fine", "good", "bad", "hi", "hello", "hey", "bye", "thanks",
        "好", "是", "不", "嗯", "哦", "谢谢", "再见"
    }

    if cleaned.lower() in short_responses:
        return True

    return False
