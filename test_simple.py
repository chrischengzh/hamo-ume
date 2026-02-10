#!/usr/bin/env python3
"""Simple PSVS System Test"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("SIMPLE PSVS SYSTEM TEST")
print("=" * 60)

# Test 1: Health check
print("\n[1] Server health check...")
r = requests.get(f"{BASE_URL}/")
print(f"✓ Server: {r.json()}")

# Test 2: Register therapist
print("\n[2] Registering therapist...")
therapist = requests.post(f"{BASE_URL}/api/auth/registerPro", json={
    "email": "dr.test@hamo.ai",
    "password": "test123",
    "full_name": "Dr. Test",
    "profession": "Psychologist"
}).json()
print(f"✓ Therapist: {therapist['user']['full_name']}")
token = therapist['access_token']

# Test 3: Create avatar
print("\n[3] Creating avatar...")
avatar = requests.post(f"{BASE_URL}/api/avatars",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "Dr. Calm",
        "specialty": "Anxiety",
        "therapeutic_approaches": ["CBT"],
        "about": "Calming therapist",
        "experience_years": 5,
        "experience_months": 0
    }).json()
print(f"✓ Avatar: {avatar['name']}")

# Test 4: Create AI Mind with PSVS
print("\n[4] Creating AI Mind (PSVS auto-initializes)...")
mind = requests.post(f"{BASE_URL}/api/mind",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "avatar_id": avatar['id'],
        "name": "Test Client",
        "personality": {
            "primary_traits": ["introvert", "analytical"],
            "description": "Analytical person"
        },
        "emotion_pattern": {
            "dominant_emotions": ["anxiety"],
            "triggers": ["work"],
            "coping_mechanisms": ["avoidance"],
            "description": "Anxious"
        },
        "goals": "Reduce anxiety"
    }).json()
print(f"✓ AI Mind: {mind['name']}")

# Test 5: Get PSVS profile
print("\n[5] Getting PSVS profile...")
psvs = requests.get(f"{BASE_URL}/api/mind/{mind['id']}/psvs",
    headers={"Authorization": f"Bearer {token}"}).json()
pos = psvs['current_position']
print(f"✓ PSVS Position:")
print(f"  - Quadrant: {pos['quadrant'].upper()}")
print(f"  - Energy: {pos['energy_state'].upper()}")
print(f"  - Stress: {pos['stress_level']:.1f}/10")
print(f"  - Distance from center: {pos['distance_from_center']:.2f}")

print("\n" + "=" * 60)
print("✅ PSVS SYSTEM WORKING CORRECTLY!")
print("=" * 60)
print(f"\nInitial state: {pos['quadrant'].upper()} + {pos['energy_state'].upper()}")
print(f"Ready for conversation with Gemini AI!")
