#!/bin/bash

# PSVS API Integration Test Script

echo "=================================="
echo "PSVS API INTEGRATION TEST"
echo "=================================="

BASE_URL="http://localhost:8000"

echo ""
echo "[1] Testing server health..."
curl -s $BASE_URL/ | jq '.'

echo ""
echo "[2] Registering therapist..."
THERAPIST=$(curl -s -X POST "$BASE_URL/api/auth/registerPro" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "therapist@test.com",
    "password": "password123",
    "full_name": "Dr. Test",
    "profession": "Clinical Psychologist",
    "specializations": ["Anxiety", "Depression"]
  }')

echo "$THERAPIST" | jq '.'
TOKEN=$(echo "$THERAPIST" | jq -r '.access_token')

echo ""
echo "[3] Creating avatar..."
AVATAR=$(curl -s -X POST "$BASE_URL/api/avatars" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Dr. Compassion",
    "specialty": "Anxiety Treatment",
    "therapeutic_approaches": ["CBT", "Person-Centered"],
    "about": "Warm and empathetic therapist",
    "experience_years": 10,
    "experience_months": 6
  }')

echo "$AVATAR" | jq '.'
AVATAR_ID=$(echo "$AVATAR" | jq -r '.id')

echo ""
echo "[4] Creating AI Mind with PSVS profile..."
AI_MIND=$(curl -s -X POST "$BASE_URL/api/mind" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "avatar_id": "'$AVATAR_ID'",
    "name": "Test Client",
    "sex": "Female",
    "age": 28,
    "personality": {
      "primary_traits": ["introvert", "analytical"],
      "description": "Tends to overthink and analyze situations"
    },
    "emotion_pattern": {
      "dominant_emotions": ["anxiety", "worry"],
      "triggers": ["social situations", "deadlines"],
      "coping_mechanisms": ["avoidance", "rumination"],
      "description": "Experiences frequent anxiety"
    },
    "cognition_beliefs": {
      "core_beliefs": ["I am not good enough", "I will fail"],
      "cognitive_distortions": ["catastrophizing", "black-and-white thinking"],
      "thinking_patterns": ["overthinking", "self-criticism"],
      "self_perception": "Inadequate and flawed",
      "world_perception": "Judgmental and demanding",
      "future_perception": "Uncertain and threatening"
    },
    "relationship_manipulations": {
      "attachment_style": "anxious",
      "relationship_patterns": ["people-pleasing", "fear of rejection"],
      "communication_style": "Indirect and apologetic",
      "conflict_resolution": "Avoidance"
    },
    "goals": "Reduce anxiety and build confidence",
    "therapy_principles": "Be warm, validating, and solution-focused"
  }')

echo "$AI_MIND" | jq '.'
MIND_ID=$(echo "$AI_MIND" | jq -r '.id')

echo ""
echo "[5] Getting PSVS profile..."
curl -s -X GET "$BASE_URL/api/mind/$MIND_ID/psvs" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo ""
echo "[6] Registering client..."
INVITATION=$(curl -s -X POST "$BASE_URL/api/pro/invitation/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "mind_id": "'$MIND_ID'"
  }')

echo "$INVITATION" | jq '.'
INVITE_CODE=$(echo "$INVITATION" | jq -r '.code')

CLIENT=$(curl -s -X POST "$BASE_URL/api/auth/registerClient" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@test.com",
    "password": "password123",
    "full_name": "Test Client",
    "invitation_code": "'$INVITE_CODE'"
  }')

echo "$CLIENT" | jq '.'
CLIENT_TOKEN=$(echo "$CLIENT" | jq -r '.access_token')
USER_ID=$(echo "$CLIENT" | jq -r '.user.id')

echo ""
echo "[7] Starting conversation session..."
SESSION=$(curl -s -X POST "$BASE_URL/api/session/start?mind_id=$MIND_ID&avatar_id=$AVATAR_ID" \
  -H "Authorization: Bearer $CLIENT_TOKEN")

echo "$SESSION" | jq '.'
SESSION_ID=$(echo "$SESSION" | jq -r '.session_id')

echo ""
echo "[8] Sending first message..."
curl -s -X POST "$BASE_URL/api/session/$SESSION_ID/message?message=I%20feel%20so%20anxious%20and%20overwhelmed%20today.%20Everything%20seems%20impossible." \
  -H "Authorization: Bearer $CLIENT_TOKEN" | jq '.'

echo ""
echo "[9] Getting updated PSVS position..."
curl -s -X GET "$BASE_URL/api/mind/$MIND_ID/psvs" \
  -H "Authorization: Bearer $TOKEN" | jq '.current_position'

echo ""
echo "=================================="
echo "PSVS API TEST COMPLETE"
echo "=================================="
