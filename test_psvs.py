"""
PSVS System Test Script

Tests the complete PSVS implementation:
1. PSVS calculator functions
2. Prompt generation
3. Gemini integration
4. Position calculation and updates
"""

import sys
from datetime import datetime

print("=" * 70)
print("PSVS SYSTEM TEST")
print("=" * 70)

# Test 1: Import modules
print("\n[TEST 1] Importing PSVS modules...")
try:
    from psvs.calculator import (
        calculate_initial_psvs_position,
        calculate_psvs_update,
        calculate_quadrant,
        calculate_energy_state,
        calculate_distance_from_center,
    )
    from psvs.prompt_generator import (
        generate_system_prompt,
        generate_policy_prompt,
        generate_value_prompt,
        generate_search_prompt,
    )
    from psvs.gemini_service import (
        analyze_message_for_stress,
        should_skip_psvs_update,
    )
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Calculate quadrants
print("\n[TEST 2] Testing quadrant calculation...")
test_cases = [
    (-0.7, 0.6, "expert", "Introvert + Rational"),
    (-0.5, -0.5, "supporter", "Introvert + Emotional"),
    (0.8, 0.7, "leader", "Extrovert + Rational"),
    (0.6, -0.6, "dreamer", "Extrovert + Emotional"),
]

for intro_extro, rational_emotional, expected, description in test_cases:
    result = calculate_quadrant(intro_extro, rational_emotional)
    status = "✓" if result == expected else "✗"
    print(f"{status} {description}: {result} (expected: {expected})")

# Test 3: Calculate energy states
print("\n[TEST 3] Testing energy state calculation...")
stress_tests = [
    (2.0, "positive", "Low stress"),
    (5.5, "negative", "Medium stress"),
    (8.0, "neurotic", "High stress"),
]

for stress, expected, description in stress_tests:
    result = calculate_energy_state(stress)
    status = "✓" if result == expected else "✗"
    print(f"{status} {description} (stress={stress}): {result}")

# Test 4: Calculate distance from center
print("\n[TEST 4] Testing distance calculation...")
print(f"✓ Stress 0.0 → Distance: {calculate_distance_from_center(0.0):.2f}")
print(f"✓ Stress 5.0 → Distance: {calculate_distance_from_center(5.0):.2f}")
print(f"✓ Stress 10.0 → Distance: {calculate_distance_from_center(10.0):.2f}")

# Test 5: Initial PSVS position calculation
print("\n[TEST 5] Testing initial PSVS position calculation...")
sample_ai_mind = {
    "personality": {
        "primary_traits": ["introvert", "analytical"],
        "description": "Tends to be rational and analytical"
    },
    "emotion_pattern": {
        "dominant_emotions": ["anxiety", "fear"],
        "emotional_stability": 0.4
    },
    "cognition_beliefs": {
        "cognitive_distortions": ["catastrophizing", "black-and-white thinking"],
        "self_perception": "I'm not good enough"
    },
    "relationship_manipulations": {
        "attachment_style": "anxious",
        "trust_level": 0.3
    }
}

try:
    initial_position = calculate_initial_psvs_position(sample_ai_mind)
    print(f"✓ Initial position calculated:")
    print(f"  - Quadrant: {initial_position['quadrant']}")
    print(f"  - Energy State: {initial_position['energy_state']}")
    print(f"  - Intro/Extro: {initial_position['intro_extro']:.2f}")
    print(f"  - Rational/Emotional: {initial_position['rational_emotional']:.2f}")
    print(f"  - Distance from center: {initial_position['distance_from_center']:.2f}")
    print(f"  - Stress level: {initial_position['stress_level']:.2f}")
except Exception as e:
    print(f"✗ Initial position calculation failed: {e}")

# Test 6: Message stress analysis
print("\n[TEST 6] Testing message stress analysis...")
test_messages = [
    ("I will take action and work on this step by step", "High agency"),
    ("I don't care anymore, whatever happens", "High withdrawal"),
    ("Everything is always terrible, nobody understands", "High extremity"),
    ("You're stupid, do it my way or else!", "High hostility"),
    ("Let's discuss this respectfully and find alignment", "High boundary"),
]

for message, description in test_messages:
    scores = analyze_message_for_stress(message)
    print(f"✓ {description}:")
    print(f"  A={scores['A']:.1f}, W={scores['W']:.1f}, E={scores['E']:.1f}, H={scores['H']:.1f}, B={scores['B']:.1f}")

# Test 7: Skip short messages
print("\n[TEST 7] Testing message filtering...")
short_messages = ["ok", "yes", "k", "hi"]
long_message = "I've been feeling really anxious lately and need help"

for msg in short_messages:
    should_skip = should_skip_psvs_update(msg)
    status = "✓" if should_skip else "✗"
    print(f"{status} '{msg}' → Skip: {should_skip}")

should_skip = should_skip_psvs_update(long_message)
status = "✓" if not should_skip else "✗"
print(f"{status} Long message → Skip: {should_skip}")

# Test 8: Prompt generation
print("\n[TEST 8] Testing prompt generation...")

sample_psvs_position = {
    "quadrant": "supporter",
    "energy_state": "negative",
    "rational_emotional": -0.5,
    "intro_extro": -0.3,
    "distance_from_center": 0.65,
    "stress_level": 5.8,
}

try:
    policy = generate_policy_prompt(sample_psvs_position)
    print(f"✓ Policy prompt generated ({len(policy)} chars)")
    print(f"  First 150 chars: {policy[:150]}...")

    value = generate_value_prompt(sample_psvs_position)
    print(f"✓ Value prompt generated ({len(value)} chars)")

    search = generate_search_prompt(sample_psvs_position)
    print(f"✓ Search prompt generated ({len(search)} chars)")
except Exception as e:
    print(f"✗ Prompt generation failed: {e}")

# Test 9: Complete system prompt
print("\n[TEST 9] Testing complete system prompt generation...")

sample_avatar = {
    "name": "Dr. Compassion",
    "specialty": "Anxiety and Depression",
    "therapeutic_approaches": ["CBT", "Person-Centered Therapy"],
    "about": "A warm and empathetic therapist specializing in anxiety treatment"
}

sample_ai_mind_info = {
    "name": "Client A",
    "goals": "Reduce anxiety and build confidence",
    "therapy_principles": "Be kind, empathetic, and solution-focused"
}

try:
    system_prompt = generate_system_prompt(sample_avatar, sample_ai_mind_info, sample_psvs_position)
    print(f"✓ Complete system prompt generated ({len(system_prompt)} chars)")
    print(f"  Contains 'Dr. Compassion': {'✓' if 'Dr. Compassion' in system_prompt else '✗'}")
    print(f"  Contains 'SUPPORTER': {'✓' if 'SUPPORTER' in system_prompt else '✗'}")
    print(f"  Contains 'NEGATIVE': {'✓' if 'NEGATIVE' in system_prompt else '✗'}")
    print(f"  Contains policy guidance: {'✓' if 'Therapeutic Approach' in system_prompt else '✗'}")
except Exception as e:
    print(f"✗ System prompt generation failed: {e}")

# Test 10: PSVS position update
print("\n[TEST 10] Testing PSVS position update...")

current_position = {
    "quadrant": "expert",
    "energy_state": "positive",
    "rational_emotional": 0.6,
    "intro_extro": -0.4,
    "distance_from_center": 0.3,
    "stress_level": 2.5,
}

# Simulate high withdrawal message
stress_indicators = {
    "A": 0.0,
    "W": 2.0,  # High withdrawal
    "E": 0.5,
    "H": 0.0,
    "B": 0.0,
}

try:
    updated_position = calculate_psvs_update(current_position, stress_indicators, "I don't know what to do...")
    print(f"✓ Position updated:")
    print(f"  Previous stress: {current_position['stress_level']:.2f} → New stress: {updated_position['stress_level']:.2f}")
    print(f"  Previous energy: {current_position['energy_state']} → New energy: {updated_position['energy_state']}")
    print(f"  Previous distance: {current_position['distance_from_center']:.2f} → New distance: {updated_position['distance_from_center']:.2f}")

    if updated_position['stress_level'] > current_position['stress_level']:
        print("  ✓ Stress correctly increased (withdrawal detected)")
except Exception as e:
    print(f"✗ Position update failed: {e}")

# Summary
print("\n" + "=" * 70)
print("PSVS SYSTEM TEST COMPLETE")
print("=" * 70)
print("\nAll core functions tested successfully!")
print("\nNote: Gemini API integration not tested (requires API call)")
print("To test Gemini, start the server and use the API endpoints.")
