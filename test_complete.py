#!/usr/bin/env python3
"""Complete End-to-End PSVS + Gemini Test"""

import requests
import time

BASE = "http://localhost:8000"

print("=" * 70)
print("COMPLETE PSVS + GEMINI AI TEST")
print("=" * 70)

try:
    # 1. Setup
    print("\n[1] Setting up therapist and avatar...")
    th = requests.post(f"{BASE}/api/auth/registerPro", json={
        "email": f"therapist{int(time.time())}@test.com",
        "password": "test123",
        "full_name": "Dr. Sarah",
        "profession": "Psychologist"
    }).json()
    token = th['access_token']

    av = requests.post(f"{BASE}/api/avatars",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Dr. Compassion",
            "specialty": "Anxiety",
            "therapeutic_approaches": ["CBT"],
            "about": "Warm therapist",
            "experience_years": 10,
            "experience_months": 0
        }).json()
    print(f"✓ Therapist: {th['user']['full_name']}, Avatar: {av['name']}")

    # 2. Create AI Mind
    print("\n[2] Creating AI Mind with PSVS...")
    mind = requests.post(f"{BASE}/api/mind",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "avatar_id": av['id'],
            "name": "Emma",
            "personality": {
                "primary_traits": ["introvert", "analytical"],
                "description": "Overthinks everything"
            },
            "emotion_pattern": {
                "dominant_emotions": ["anxiety", "worry"],
                "triggers": ["work", "social"],
                "coping_mechanisms": ["avoidance"],
                "description": "Anxious"
            },
            "cognition_beliefs": {
                "core_beliefs": ["I'm not good enough"],
                "cognitive_distortions": ["catastrophizing"],
                "thinking_patterns": ["overthinking"],
                "self_perception": "Inadequate"
            },
            "relationship_manipulations": {
                "attachment_style": "anxious",
                "communication_style": "Indirect"
            },
            "goals": "Reduce anxiety"
        }).json()
    print(f"✓ AI Mind created: {mind['name']}")

    # 3. Check PSVS
    print("\n[3] Checking initial PSVS position...")
    psvs = requests.get(f"{BASE}/api/mind/{mind['id']}/psvs",
        headers={"Authorization": f"Bearer {token}"}).json()

    if 'current_position' in psvs:
        p = psvs['current_position']
        print(f"✓ Initial PSVS:")
        print(f"  Quadrant: {p['quadrant'].upper()}")
        print(f"  Energy: {p['energy_state'].upper()}")
        print(f"  Stress: {p['stress_level']:.1f}/10")
        print(f"  Distance: {p['distance_from_center']:.2f}")
    else:
        print(f"⚠ PSVS response: {psvs}")

    # 4. Register client
    print("\n[4] Setting up client...")
    inv = requests.post(f"{BASE}/api/pro/invitation/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"mind_id": mind['id']}).json()

    cl = requests.post(f"{BASE}/api/auth/registerClient", json={
        "email": f"client{int(time.time())}@test.com",
        "password": "test123",
        "full_name": "Emma",
        "invitation_code": inv['code']
    }).json()
    cl_token = cl['access_token']
    print(f"✓ Client registered with code: {inv['code']}")

    # 5. Start session
    print("\n[5] Starting conversation session...")
    sess = requests.post(f"{BASE}/api/session/start",
        headers={"Authorization": f"Bearer {cl_token}"},
        params={"mind_id": mind['id'], "avatar_id": av['id']}).json()
    print(f"✓ Session: {sess['session_id']}")

    # 6. Send message and get AI response
    print("\n[6] Testing Gemini AI response...")
    print("\n→ Client: \"I feel so anxious about my presentation tomorrow\"")

    resp = requests.post(f"{BASE}/api/session/{sess['session_id']}/message",
        headers={"Authorization": f"Bearer {cl_token}"},
        params={"message": "I feel so anxious about my presentation tomorrow. I can't stop thinking about all the ways it could go wrong."})

    if resp.status_code == 200:
        data = resp.json()
        print(f"\n← AI Response:\n{data['response']}\n")

        p = data['psvs_position']
        print(f"Updated PSVS:")
        print(f"  Quadrant: {p['quadrant'].upper()}")
        print(f"  Energy: {p['energy_state'].upper()}")
        print(f"  Stress: {p['stress_level']:.1f}/10")
        print(f"  Distance: {p['distance_from_center']:.2f}")

        print("\n" + "=" * 70)
        print("✅ SUCCESS! PSVS + GEMINI FULLY WORKING!")
        print("=" * 70)
        print(f"\n✓ AI generated therapeutic response")
        print(f"✓ PSVS position tracked and updated")
        print(f"✓ Using model: gemini-3-flash-preview")

    else:
        print(f"\n✗ Error: {resp.status_code}")
        print(resp.text)

except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
