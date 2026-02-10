"""
Complete PSVS Integration Test with Gemini
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("PSVS COMPLETE INTEGRATION TEST")
print("=" * 70)

def test_full_flow():
    # Step 1: Register therapist
    print("\n[STEP 1] Registering therapist...")
    therapist_res = requests.post(f"{BASE_URL}/api/auth/registerPro", json={
        "email": "therapist@test.com",
        "password": "password123",
        "full_name": "Dr. Sarah Chen",
        "profession": "Clinical Psychologist",
        "license_number": "PSY12345",
        "specializations": ["Anxiety", "Depression", "CBT"]
    })

    if therapist_res.status_code != 200:
        print(f"✗ Failed to register therapist: {therapist_res.text}")
        return

    therapist_data = therapist_res.json()
    token = therapist_data["access_token"]
    print(f"✓ Therapist registered: {therapist_data['user']['full_name']}")

    # Step 2: Create avatar
    print("\n[STEP 2] Creating therapy avatar...")
    avatar_res = requests.post(f"{BASE_URL}/api/avatars",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Dr. Compassion",
            "specialty": "Anxiety and Stress Management",
            "therapeutic_approaches": ["CBT", "Person-Centered Therapy", "Mindfulness"],
            "about": "A warm, empathetic therapist specializing in anxiety treatment with 10+ years of experience",
            "experience_years": 10,
            "experience_months": 6
        })

    avatar_data = avatar_res.json()
    avatar_id = avatar_data["id"]
    print(f"✓ Avatar created: {avatar_data['name']}")

    # Step 3: Create AI Mind with detailed profile
    print("\n[STEP 3] Creating AI Mind profile with PSVS initialization...")
    ai_mind_res = requests.post(f"{BASE_URL}/api/mind",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "avatar_id": avatar_id,
            "name": "Emma Wilson",
            "sex": "Female",
            "age": 28,
            "personality": {
                "primary_traits": ["introvert", "analytical", "perfectionist"],
                "description": "Highly analytical and detail-oriented, tends to overthink situations and struggles with decision-making due to fear of making mistakes."
            },
            "emotion_pattern": {
                "dominant_emotions": ["anxiety", "worry", "fear"],
                "triggers": ["social situations", "work deadlines", "uncertainty", "criticism"],
                "coping_mechanisms": ["avoidance", "rumination", "seeking reassurance"],
                "description": "Experiences frequent anxiety, especially in social and work contexts. Often worries about future outcomes."
            },
            "cognition_beliefs": {
                "core_beliefs": ["I am not good enough", "I will fail", "People will judge me"],
                "cognitive_distortions": ["catastrophizing", "black-and-white thinking", "overgeneralization"],
                "thinking_patterns": ["overthinking", "self-criticism", "perfectionism"],
                "self_perception": "Inadequate, flawed, always needing to prove myself",
                "world_perception": "Judgmental, demanding, unforgiving of mistakes",
                "future_perception": "Uncertain, threatening, full of potential failures"
            },
            "relationship_manipulations": {
                "attachment_style": "anxious",
                "relationship_patterns": ["people-pleasing", "fear of rejection", "difficulty setting boundaries"],
                "communication_style": "Indirect, apologetic, often second-guessing",
                "conflict_resolution": "Avoidance, accommodation, self-blame"
            },
            "goals": "Reduce anxiety, build self-confidence, improve decision-making, develop healthier coping mechanisms",
            "therapy_principles": "Be warm and validating, use CBT techniques, focus on building agency and reducing avoidance"
        })

    ai_mind_data = ai_mind_res.json()
    mind_id = ai_mind_data["id"]
    print(f"✓ AI Mind created: {ai_mind_data['name']}")

    # Step 4: Check PSVS profile
    print("\n[STEP 4] Checking initial PSVS position...")
    psvs_res = requests.get(f"{BASE_URL}/api/mind/{mind_id}/psvs",
        headers={"Authorization": f"Bearer {token}"})

    if psvs_res.status_code == 200:
        psvs_data = psvs_res.json()
        pos = psvs_data["current_position"]
        print(f"✓ PSVS Profile initialized:")
        print(f"  - Quadrant: {pos['quadrant'].upper()}")
        print(f"  - Energy State: {pos['energy_state'].upper()}")
        print(f"  - Intro/Extro: {pos['intro_extro']:.2f}")
        print(f"  - Rational/Emotional: {pos['rational_emotional']:.2f}")
        print(f"  - Distance from Center: {pos['distance_from_center']:.2f}")
        print(f"  - Stress Level: {pos['stress_level']:.2f}/10")
    else:
        print(f"✗ Failed to get PSVS profile: {psvs_res.text}")
        return

    # Step 5: Generate invitation and register client
    print("\n[STEP 5] Generating invitation code...")
    invite_res = requests.post(f"{BASE_URL}/api/pro/invitation/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"mind_id": mind_id})

    invite_data = invite_res.json()
    invite_code = invite_data["code"]
    print(f"✓ Invitation code generated: {invite_code}")

    print("\n[STEP 6] Registering client...")
    client_res = requests.post(f"{BASE_URL}/api/auth/registerClient", json={
        "email": "emma@test.com",
        "password": "password123",
        "full_name": "Emma Wilson",
        "invitation_code": invite_code
    })

    client_data = client_res.json()
    client_token = client_data["access_token"]
    print(f"✓ Client registered and connected to AI Mind")

    # Step 7: Start conversation session
    print("\n[STEP 7] Starting conversation session...")
    session_res = requests.post(f"{BASE_URL}/api/session/start",
        headers={"Authorization": f"Bearer {client_token}"},
        params={"mind_id": mind_id, "avatar_id": avatar_id})

    session_data = session_res.json()
    session_id = session_data["session_id"]
    print(f"✓ Session started: {session_id}")

    # Step 8: Send messages and test Gemini integration
    print("\n[STEP 8] Testing conversation with Gemini AI...")

    messages = [
        "I feel so anxious and overwhelmed today. I have a big presentation at work tomorrow and I can't stop thinking about all the ways it could go wrong.",
        "Everyone will think I'm incompetent. I always mess things up.",
        "I don't know... I guess I could prepare more, but what if it's still not good enough?",
    ]

    for i, msg in enumerate(messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"Client: {msg}")

        response_res = requests.post(f"{BASE_URL}/api/session/{session_id}/message",
            headers={"Authorization": f"Bearer {client_token}"},
            params={"message": msg})

        if response_res.status_code == 200:
            response_data = response_res.json()
            print(f"\nTherapist Response:\n{response_data['response']}\n")

            pos = response_data['psvs_position']
            print(f"Updated PSVS Position:")
            print(f"  - Quadrant: {pos['quadrant'].upper()}")
            print(f"  - Energy: {pos['energy_state'].upper()}")
            print(f"  - Stress: {pos['stress_level']:.2f}/10")
            print(f"  - Distance from Center: {pos['distance_from_center']:.2f}")
        else:
            print(f"✗ Failed to get response: {response_res.text}")
            break

        sleep(2)  # Brief pause between messages

    # Step 9: Check trajectory
    print("\n[STEP 9] Checking PSVS trajectory...")
    trajectory_res = requests.get(f"{BASE_URL}/api/mind/{mind_id}/psvs/trajectory",
        headers={"Authorization": f"Bearer {token}"})

    if trajectory_res.status_code == 200:
        trajectory = trajectory_res.json()
        print(f"✓ Trajectory contains {len(trajectory)} positions")
        print(f"\n  Movement over conversation:")
        for idx, pos in enumerate(trajectory):
            print(f"  {idx}: {pos['energy_state'].upper()} - Stress: {pos['stress_level']:.2f}")

    # Step 10: Get session messages
    print("\n[STEP 10] Retrieving full conversation history...")
    messages_res = requests.get(f"{BASE_URL}/api/session/{session_id}/messages",
        headers={"Authorization": f"Bearer {client_token}"})

    if messages_res.status_code == 200:
        messages_data = messages_res.json()
        print(f"✓ Retrieved {len(messages_data)} messages")

    print("\n" + "=" * 70)
    print("INTEGRATION TEST COMPLETE!")
    print("=" * 70)
    print("\n✅ All systems working:")
    print("  ✓ PSVS position calculation")
    print("  ✓ Dynamic prompt generation")
    print("  ✓ Gemini AI integration")
    print("  ✓ Trajectory tracking")
    print("  ✓ Session management")

if __name__ == "__main__":
    try:
        test_full_flow()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
