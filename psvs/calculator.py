"""
PSVS Calculator Module

Calculates user position in the Psychological Semantic Vector Space (PSVS)
based on personality traits, conversation patterns, and stress indicators.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import math


def calculate_quadrant(intro_extro: float, rational_emotional: float) -> str:
    """
    Calculate PSVS quadrant based on two axes.

    Args:
        intro_extro: -1 (introvert) to +1 (extrovert)
        rational_emotional: -1 (emotional) to +1 (rational)

    Returns:
        One of: "expert", "supporter", "leader", "dreamer"

    Quadrant mapping:
    - EXPERT: Introvert + Rational (task-oriented, analytical)
    - SUPPORTER: Introvert + Emotional (people-oriented, empathetic)
    - LEADER: Extrovert + Rational (task-oriented, decisive)
    - DREAMER: Extrovert + Emotional (people-oriented, inspiring)
    """
    # Determine primary orientation
    is_extrovert = intro_extro > 0
    is_rational = rational_emotional > 0

    if is_extrovert:
        if is_rational:
            return "leader"    # High task + Extrovert
        else:
            return "dreamer"   # High people + Extrovert
    else:
        if is_rational:
            return "expert"    # High task + Introvert
        else:
            return "supporter" # High people + Introvert


def calculate_energy_state(stress_level: float) -> str:
    """
    Calculate energy state based on stress level.

    Based on status_transform.json thresholds:
    - POSITIVE (orange center): S < 4.0
    - NEGATIVE (gray middle): 4.0 <= S < 7.0
    - NEUROTIC (red outer): S >= 7.0

    Args:
        stress_level: Stress value from 0 to 10

    Returns:
        One of: "positive", "negative", "neurotic"
    """
    if stress_level < 4.0:
        return "positive"
    elif stress_level < 7.0:
        return "negative"
    else:
        return "neurotic"


def calculate_distance_from_center(stress_level: float) -> float:
    """
    Calculate normalized distance from homeostatic center.

    Args:
        stress_level: Stress value from 0 to 10

    Returns:
        Distance from 0.0 (center) to 1.0 (edge)
    """
    # Normalize stress to 0-1 range
    return min(stress_level / 10.0, 1.0)


def calculate_stress_from_indicators(
    agency: float = 0.0,
    withdrawal: float = 0.0,
    extremity: float = 0.0,
    hostility: float = 0.0,
    boundary: float = 0.0,
    current_stress: float = 1.5,
    quadrant: str = "expert"
) -> float:
    """
    Calculate stress level based on A/W/E/H/B indicators.

    Based on status_transform.json formula:
    S = clamp(S + 0.9*W + 1.2*E + 1.6*H - 1.0*A - 1.1*B, 0, 10)

    With quadrant modifiers:
    - EXPERT: W*1.2, H_fastpath*1.3
    - SUPPORTER: W*1.3
    - LEADER: H*1.2, A*1.2
    - DREAMER: E*1.2, H*1.2, B*1.2

    Args:
        agency: Action-oriented, responsibility-taking (reduces stress)
        withdrawal: Disengagement, avoidance (increases stress)
        extremity: All-or-nothing thinking (increases stress)
        hostility: Coercion, threats, insults (strongly increases stress)
        boundary: Respect, clarification (reduces stress)
        current_stress: Current stress level
        quadrant: Current quadrant for modifiers

    Returns:
        Updated stress level (0-10)
    """
    # Apply quadrant modifiers
    if quadrant == "expert":
        withdrawal *= 1.2
        hostility *= 1.3
    elif quadrant == "supporter":
        withdrawal *= 1.3
    elif quadrant == "leader":
        hostility *= 1.2
        agency *= 1.2
    elif quadrant == "dreamer":
        extremity *= 1.2
        hostility *= 1.2
        boundary *= 1.2

    # Calculate stress update
    stress_delta = (
        0.9 * withdrawal +
        1.2 * extremity +
        1.6 * hostility -
        1.0 * agency -
        1.1 * boundary
    )

    new_stress = current_stress + stress_delta

    # Clamp to valid range
    return max(0.0, min(new_stress, 10.0))


def parse_personality_traits(personality_data: Optional[Dict[str, Any]]) -> tuple[float, float]:
    """
    Parse personality traits from AI Mind data to extract axes values.

    Expects personality_data with:
    - primary_traits: list of trait strings
    - description: text description

    Or direct Social Orientation / Decision Style values.

    Returns:
        (intro_extro, rational_emotional) both in range [-1, 1]
    """
    if not personality_data:
        # Default to center if no data
        return (0.0, 0.0)

    intro_extro = 0.0
    rational_emotional = 0.0

    # Check if we have explicit values (from UI sliders)
    if isinstance(personality_data, dict):
        # Try to extract from primary_traits
        primary_traits = personality_data.get("primary_traits", [])
        if isinstance(primary_traits, list):
            for trait in primary_traits:
                trait_lower = str(trait).lower()
                # Intro/Extro axis
                if "introvert" in trait_lower:
                    intro_extro -= 0.5
                elif "extrovert" in trait_lower:
                    intro_extro += 0.5
                # Rational/Emotional axis
                if "analytical" in trait_lower or "rational" in trait_lower:
                    rational_emotional += 0.4
                elif "creative" in trait_lower or "emotional" in trait_lower:
                    rational_emotional -= 0.4

        # Check description for additional clues
        description = personality_data.get("description", "")
        if description:
            desc_lower = description.lower()
            if "introvert" in desc_lower:
                intro_extro -= 0.3
            if "extrovert" in desc_lower:
                intro_extro += 0.3
            if "rational" in desc_lower or "logical" in desc_lower:
                rational_emotional += 0.3
            if "emotional" in desc_lower or "feeling" in desc_lower:
                rational_emotional -= 0.3

    # Clamp to valid range
    intro_extro = max(-1.0, min(intro_extro, 1.0))
    rational_emotional = max(-1.0, min(rational_emotional, 1.0))

    return (intro_extro, rational_emotional)


def estimate_initial_stress(ai_mind_data: Dict[str, Any]) -> float:
    """
    Estimate initial stress level from AI Mind profile data.

    Args:
        ai_mind_data: AI Mind data including emotion_pattern, cognition_beliefs, etc.

    Returns:
        Initial stress level (0-10)
    """
    stress = 1.5  # Default baseline

    # Check emotion patterns
    emotion_pattern = ai_mind_data.get("emotion_pattern", {})
    if emotion_pattern:
        dominant_emotions = emotion_pattern.get("dominant_emotions", [])
        for emotion in dominant_emotions:
            emotion_str = str(emotion).lower()
            if emotion_str in ["anxiety", "depression", "fear"]:
                stress += 1.5
            elif emotion_str in ["anger"]:
                stress += 2.0
            elif emotion_str in ["sadness"]:
                stress += 1.0

        # Emotional stability (inverted - lower stability = higher stress)
        emotional_stability = emotion_pattern.get("emotional_stability", 0.5)
        stress += (1.0 - emotional_stability) * 2.0

    # Check cognition beliefs for distortions
    cognition = ai_mind_data.get("cognition_beliefs", {})
    if cognition:
        cognitive_distortions = cognition.get("cognitive_distortions", [])
        # More distortions = higher stress
        stress += len(cognitive_distortions) * 0.5

        # Check for negative perceptions
        self_perception = cognition.get("self_perception", "")
        if self_perception:
            if any(word in self_perception.lower() for word in ["negative", "bad", "worthless", "failure"]):
                stress += 1.0

    # Check relationship patterns
    relationship = ai_mind_data.get("relationship_manipulations", {})
    if relationship:
        attachment_style = relationship.get("attachment_style", "secure")
        if attachment_style in ["anxious", "disorganized"]:
            stress += 1.5
        elif attachment_style == "avoidant":
            stress += 1.0

        # Trust and intimacy (inverted)
        trust_level = relationship.get("trust_level", 0.5)
        stress += (1.0 - trust_level) * 1.5

    # Clamp to valid range
    return max(0.0, min(stress, 10.0))


def calculate_initial_psvs_position(ai_mind_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate initial PSVS position from AI Mind profile data.

    Args:
        ai_mind_data: Complete AI Mind data with personality, emotion, cognition, relationship

    Returns:
        PSVSCoordinates dictionary
    """
    # Extract personality axes
    personality = ai_mind_data.get("personality", {})
    intro_extro, rational_emotional = parse_personality_traits(personality)

    # Calculate quadrant
    quadrant = calculate_quadrant(intro_extro, rational_emotional)

    # Estimate initial stress
    stress_level = estimate_initial_stress(ai_mind_data)

    # Calculate energy state
    energy_state = calculate_energy_state(stress_level)

    # Calculate distance from center
    distance = calculate_distance_from_center(stress_level)

    return {
        "quadrant": quadrant,
        "energy_state": energy_state,
        "rational_emotional": rational_emotional,
        "intro_extro": intro_extro,
        "distance_from_center": distance,
        "stress_level": stress_level,
        "timestamp": datetime.now()
    }


def calculate_psvs_update(
    current_position: Dict[str, Any],
    stress_indicators: Dict[str, float],
    message_content: str
) -> Dict[str, Any]:
    """
    Update PSVS position based on new message and stress indicators.

    Args:
        current_position: Current PSVSCoordinates
        stress_indicators: Dict with A, W, E, H, B values
        message_content: The user's message (for context)

    Returns:
        Updated PSVSCoordinates dictionary
    """
    # Get current values
    current_stress = current_position.get("stress_level", 1.5)
    quadrant = current_position.get("quadrant", "expert")
    intro_extro = current_position.get("intro_extro", 0.0)
    rational_emotional = current_position.get("rational_emotional", 0.0)

    # Calculate new stress level
    new_stress = calculate_stress_from_indicators(
        agency=stress_indicators.get("A", 0.0),
        withdrawal=stress_indicators.get("W", 0.0),
        extremity=stress_indicators.get("E", 0.0),
        hostility=stress_indicators.get("H", 0.0),
        boundary=stress_indicators.get("B", 0.0),
        current_stress=current_stress,
        quadrant=quadrant
    )

    # Recalculate energy state and distance
    new_energy_state = calculate_energy_state(new_stress)
    new_distance = calculate_distance_from_center(new_stress)

    # Quadrant might shift slightly based on conversation patterns
    # (For now, keep it stable - could add logic to shift quadrant over time)

    return {
        "quadrant": quadrant,
        "energy_state": new_energy_state,
        "rational_emotional": rational_emotional,
        "intro_extro": intro_extro,
        "distance_from_center": new_distance,
        "stress_level": new_stress,
        "timestamp": datetime.now()
    }
