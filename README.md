# 🧠 Hamo-UME (Unified Mind Engine)

> Backend API Server for the Hamo AI Therapy Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 Overview

**Hamo-UME** (Hamo Unified Mind Engine) is the core backend service that powers the Hamo AI Therapy ecosystem. It provides APIs for managing user psychological profiles (AI Mind), processing therapy conversations, and collecting session feedback.

### Hamo Ecosystem

| Component | Description |
|-----------|-------------|
| **hamo-pro** | Therapist/Professional dashboard (React frontend) |
| **hamo-client** | Client/Patient mobile app for therapy sessions |
| **hamo-ume** | Backend API server (this project) |

## ✨ Features

- **User AI Mind Profile** - Comprehensive psychological modeling including personality, emotions, cognition, and relationships
- **Training Pipeline** - Process therapy conversations to refine AI Mind models
- **Session Feedback** - Capture client's Being, Feeling, and Knowing states
- **RESTful API** - Clean, documented API with automatic OpenAPI/Swagger docs
- **CORS Support** - Ready for frontend integration

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐
│  hamo-pro   │     │ hamo-client │
│  (React)    │     │   (Mobile)  │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
                 ▼
        ┌────────────────┐
        │   hamo-ume     │
        │   (FastAPI)    │
        └────────┬───────┘
                 │
                 ▼
        ┌────────────────┐
        │   LLM Backend  │
        │ (Claude/GPT)   │
        └────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/hamo-ume.git
cd hamo-ume

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Verify Installation

Open your browser and visit:
- **API Root**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Documentation

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/v1/mind/{user_id}/{avatar_id}` | Get User AI Mind |
| `POST` | `/api/v1/mind/train` | Submit training request |
| `POST` | `/api/v1/feedback/session` | Submit session feedback |
| `GET` | `/api/v1/feedback/{user_id}` | Get feedback history |
| `GET` | `/api/v1/training/status/{training_id}` | Check training status |

---

### 1. Get User AI Mind

Retrieves the complete AI Mind profile for a user-avatar pair.

**Endpoint**: `GET /api/v1/mind/{user_id}/{avatar_id}`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Client user identifier |
| `avatar_id` | string | Pro Avatar identifier |

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/mind/user123/avatar456"
```

**Example Response**:
```json
{
  "user_id": "user123",
  "avatar_id": "avatar456",
  "personality": {
    "primary_traits": ["introvert", "perfectionist"],
    "openness": 0.72,
    "conscientiousness": 0.85,
    "extraversion": 0.35,
    "agreeableness": 0.68,
    "neuroticism": 0.55,
    "description": "Client shows introverted tendencies..."
  },
  "emotion_pattern": {
    "dominant_emotions": ["anxiety", "neutral"],
    "triggers": ["Work deadlines...", "Social situations..."],
    "coping_mechanisms": ["Withdrawal...", "Over-preparation..."],
    "emotional_stability": 0.52,
    "description": "Experiences heightened anxiety..."
  },
  "cognition_beliefs": {
    "core_beliefs": ["I must perform perfectly..."],
    "cognitive_distortions": ["All-or-nothing thinking..."],
    "thinking_patterns": ["Rumination..."],
    "self_perception": "Views self as capable but flawed",
    "world_perception": "World is demanding",
    "future_perception": "Success depends on performance"
  },
  "relationship_manipulations": {
    "attachment_style": "anxious",
    "relationship_patterns": ["Difficulty expressing needs..."],
    "communication_style": "Indirect",
    "conflict_resolution": "Avoidant",
    "trust_level": 0.55,
    "intimacy_comfort": 0.42
  },
  "last_updated": "2026-01-22T10:30:00",
  "confidence_score": 0.87
}
```

**Usage Scenario**:
```python
# In hamo-pro: Build context prompt for LLM
user_mind = get_user_ai_mind(user_id, avatar_id)
avatar_profile = get_avatar_profile(avatar_id)
conversation_history = get_conversation_history(user_id, avatar_id)

context_prompt = f"""
## User AI Mind Profile
{user_mind}

## Therapist Avatar Profile
Theory: {avatar_profile.theory}
Methodology: {avatar_profile.methodology}
Principles: {avatar_profile.principles}

## Previous Conversation
{conversation_history}
"""

# Call LLM with context_prompt + system_instruction
response = call_llm(system_prompt, context_prompt, user_message)
```

---

### 2. Submit Training Request

Submit conversation data to train/refine the User AI Mind model.

**Endpoint**: `POST /api/v1/mind/train`

**Request Body**:
```json
{
  "user_id": "user123",
  "avatar_id": "avatar456",
  "session_id": "session789",
  "conversation": [
    {
      "sender": "client",
      "content": "I've been feeling anxious about work lately.",
      "timestamp": "2026-01-22T14:23:00"
    },
    {
      "sender": "avatar",
      "content": "I hear that work brings up anxiety. What specifically triggers these feelings?",
      "timestamp": "2026-01-22T14:24:00"
    }
  ],
  "session_notes": "Client showing progress in identifying triggers"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/mind/train" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","avatar_id":"avatar456","session_id":"s1","conversation":[{"sender":"client","content":"Hello","timestamp":"2026-01-22T10:00:00"}]}'
```

**Example Response**:
```json
{
  "success": true,
  "message": "Training request queued successfully. Processing 2 messages.",
  "training_id": "abc123-def456",
  "estimated_completion": "2026-01-22T14:30:00"
}
```

---

### 3. Submit Session Feedback

Client submits feedback on their Being, Feeling, and Knowing states.

**Endpoint**: `POST /api/v1/feedback/session`

**Request Body**:
```json
{
  "user_id": "user123",
  "session_id": "session789",
  "being_energy_level": 6.5,
  "being_physical_comfort": 7.0,
  "being_description": "Feeling more relaxed physically",
  "feeling_primary_emotion": "neutral",
  "feeling_intensity": 4.0,
  "feeling_description": "Calmer than before the session",
  "knowing_clarity": 8.0,
  "knowing_insights": [
    "I realize my anxiety is tied to perfectionism",
    "I can separate my worth from my performance"
  ],
  "knowing_description": "Gained new perspective on work stress",
  "overall_rating": 8.5
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Session feedback recorded successfully",
  "feedback_id": "feedback-xyz789"
}
```

---

### 4. Get Feedback History

Retrieve all session feedback for a specific user.

**Endpoint**: `GET /api/v1/feedback/{user_id}`

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/feedback/user123"
```

---

### 5. Check Training Status

Check the status of a training request.

**Endpoint**: `GET /api/v1/training/status/{training_id}`

**Example Response**:
```json
{
  "training_id": "abc123-def456",
  "status": "completed",
  "progress": 100,
  "message": "AI Mind model updated successfully"
}
```

## 📊 Data Models

### User AI Mind Structure

```
UserAIMind
├── user_id: string
├── avatar_id: string
├── personality: PersonalityCharacteristics
│   ├── primary_traits: list[PersonalityTrait]
│   ├── openness: float (0-1)
│   ├── conscientiousness: float (0-1)
│   ├── extraversion: float (0-1)
│   ├── agreeableness: float (0-1)
│   ├── neuroticism: float (0-1)
│   └── description: string
├── emotion_pattern: EmotionPattern
│   ├── dominant_emotions: list[EmotionType]
│   ├── triggers: list[string]
│   ├── coping_mechanisms: list[string]
│   ├── emotional_stability: float (0-1)
│   └── description: string
├── cognition_beliefs: CognitionBeliefs
│   ├── core_beliefs: list[string]
│   ├── cognitive_distortions: list[string]
│   ├── thinking_patterns: list[string]
│   ├── self_perception: string
│   ├── world_perception: string
│   └── future_perception: string
├── relationship_manipulations: RelationshipManipulations
│   ├── attachment_style: RelationshipStyle
│   ├── relationship_patterns: list[string]
│   ├── communication_style: string
│   ├── conflict_resolution: string
│   ├── trust_level: float (0-1)
│   └── intimacy_comfort: float (0-1)
├── last_updated: datetime
└── confidence_score: float (0-1)
```

### Enums

**EmotionType**: `anxiety`, `depression`, `anger`, `fear`, `sadness`, `joy`, `neutral`

**PersonalityTrait**: `introvert`, `extrovert`, `analytical`, `creative`, `perfectionist`, `people_pleaser`, `independent`, `dependent`

**RelationshipStyle**: `secure`, `anxious`, `avoidant`, `disorganized`

## 🛠️ Development

### Project Structure

```
hamo-ume/
├── main.py              # Main API application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
└── tests/              # Unit tests (coming soon)
    └── test_api.py
```

### Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/ -v
```

### Code Style

```bash
# Install linters
pip install black flake8

# Format code
black main.py

# Check style
flake8 main.py
```

## 🗺️ Roadmap

- [x] Core API endpoints
- [x] Mock data generator
- [ ] Database integration (PostgreSQL)
- [ ] Authentication & Authorization (JWT)
- [ ] Real AI Mind training pipeline
- [ ] WebSocket support for real-time updates
- [ ] Rate limiting & caching
- [ ] Docker containerization
- [ ] Kubernetes deployment configs

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **Project**: Hamo AI Therapy Platform
- **Email**: chris@hamo.ai
- **GitHub**: https://github.com/chrischengzh/hamo-ume

---

<p align="center">Made with ❤️ for mental health</p>
