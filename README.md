# Hamo-UME (Unified Mind Engine)

> Backend API Server for the Hamo AI Therapy Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

**Hamo-UME** (Unified Mind Engine) is the core backend service powering the Hamo AI Therapy ecosystem. It provides RESTful APIs for therapist and client authentication, avatar-based therapy management, AI Mind psychological profiling, invitation-based onboarding, session feedback, supervision, and platform analytics.

**The code was written entirely by AI.**

### Hamo Ecosystem

| Component | Description |
|-----------|-------------|
| **hamo-pro** | Therapist/Professional dashboard (React frontend) |
| **hamo-client** | Client/Patient mobile app for therapy sessions |
| **hamo-ume** | Backend API server (this project) |

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com) 0.109
- **Runtime**: Python 3.10+
- **Server**: Uvicorn 0.27 / Gunicorn 21.2
- **Authentication**: JWT via python-jose (HS256)
- **Validation**: Pydantic v2
- **Deployment**: Vercel, AWS Elastic Beanstalk, Heroku-compatible (Procfile)

## Architecture

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

## Features

- **JWT Authentication** — Separate registration and login flows for therapists (Pro) and clients, with access and refresh token support
- **Avatar Management** — Therapists create and manage therapeutic avatars with specialties, therapeutic approaches, and experience details
- **AI Mind Profiling** — Comprehensive psychological modeling across four dimensions: personality, emotion patterns, cognition/beliefs, and relationship dynamics
- **Invitation System** — Therapists generate time-limited invitation codes (7-day expiry) to onboard clients and link them to AI Minds
- **Multi-Avatar Support** — Clients can connect to multiple therapist avatars and maintain separate therapeutic relationships
- **Session Feedback** — Clients submit Being, Feeling, and Knowing (BFK) feedback after sessions with overall ratings
- **Supervision** — Therapists provide structured supervision feedback on client AI Minds by section
- **Discover Page** — Public avatar discovery for clients to find and connect with therapists
- **Portal Analytics** — Admin endpoints for platform-wide statistics, therapist overviews, and client details
- **Auto-generated Docs** — Interactive Swagger UI and ReDoc available out of the box

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/chrischengzh/hamo-ume.git
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

- **API Root**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Reference

All endpoints are prefixed with `/api` unless noted otherwise.

### Authentication — Pro (Therapist)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/registerPro` | Register a new therapist account |
| `POST` | `/api/auth/loginPro` | Login and receive access + refresh tokens |
| `POST` | `/api/auth/refreshPro` | Refresh an expired access token |

### Authentication — Client

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/registerClient` | Register with an invitation code |
| `POST` | `/api/auth/loginClient` | Login and receive tokens |
| `POST` | `/api/auth/refreshClient` | Refresh an expired access token |

### User Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users/me/pro` | Get current therapist profile |
| `GET` | `/api/users/me/client` | Get current client profile |

### Avatars

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/avatars` | List therapist's avatars |
| `POST` | `/api/avatars` | Create a new avatar |
| `GET` | `/api/avatars/{avatar_id}` | Get avatar details |
| `PUT` | `/api/avatars/{avatar_id}` | Update an avatar |
| `GET` | `/api/discover/avatars` | Public avatar discovery |

### AI Mind

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/mind` | Create an AI Mind profile |
| `GET` | `/api/mind/{mind_id}` | Get AI Mind by ID |
| `GET` | `/api/mind/{user_id}/{avatar_id}` | Get AI Mind by user + avatar pair |
| `POST` | `/api/mind/{mind_id}/supervise` | Submit supervision feedback |

### Clients

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/clients` | List therapist's clients |
| `POST` | `/api/clients` | Create a client profile (legacy) |
| `GET` | `/api/clients/{client_id}` | Get client details |

### Client Avatar Connections

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/client/avatars` | List client's connected avatars |
| `POST` | `/api/client/avatar/connect` | Connect via invitation code |
| `POST` | `/api/client/avatar/connect-by-id` | Connect directly from discover page |

### Invitations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pro/invitation/generate` | Generate an invitation code |
| `POST` | `/api/invitations` | Create invitation (legacy) |
| `GET` | `/api/invitations/{code}` | Validate an invitation code |
| `POST` | `/api/client/invitation/validate` | Client-side invitation validation |

### Session Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/feedback/session` | Submit BFK session feedback |
| `GET` | `/api/feedback/{user_id}` | Get feedback history |

### Portal / Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/portal/stats` | Platform-wide statistics |
| `GET` | `/api/portal/pro-users` | All therapist summaries |
| `GET` | `/api/portal/pro-users/{pro_id}/details` | Therapist detail with clients |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |

## Data Models

### AI Mind Structure

The AI Mind profile captures four psychological dimensions for each client-avatar pair:

```
UserAIMind
├── personality_characteristics
│   ├── primary_traits: list[PersonalityTrait]
│   ├── big_five: openness, conscientiousness, extraversion, agreeableness, neuroticism (0-1)
│   └── description: string
├── emotion_pattern
│   ├── dominant_emotions: list[EmotionType]
│   ├── triggers, coping_mechanisms: list[string]
│   ├── emotional_stability: float (0-1)
│   └── description: string
├── cognition_beliefs
│   ├── core_beliefs, cognitive_distortions, thinking_patterns: list[string]
│   └── self_perception, world_perception, future_perception: string
└── relationship_manipulations
    ├── attachment_style: secure | anxious | avoidant | disorganized
    ├── communication_style, conflict_resolution: string
    └── trust_level, intimacy_comfort: float (0-1)
```

### Enums

| Enum | Values |
|------|--------|
| **EmotionType** | `anxiety`, `depression`, `anger`, `fear`, `sadness`, `joy`, `neutral` |
| **PersonalityTrait** | `introvert`, `extrovert`, `analytical`, `creative`, `perfectionist`, `people_pleaser`, `independent`, `dependent` |
| **RelationshipStyle** | `secure`, `anxious`, `avoidant`, `disorganized` |

## Project Structure

```
hamo-ume/
├── main.py                # FastAPI application (all routes and models)
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel deployment config
├── Procfile               # Heroku / generic deployment
├── .ebextensions/         # AWS Elastic Beanstalk config
│   └── python.config
├── model/                 # Personality/AI model schemas and examples
│   ├── detector.json
│   ├── instance.json
│   ├── personality_traits.schema
│   └── status_transform.json
├── LICENSE                # MIT License
└── README.md              # This file
```

## Deployment

### Vercel

The project includes a `vercel.json` for one-click deployment:

```bash
vercel --prod
```

### AWS Elastic Beanstalk

Configuration is provided in `.ebextensions/`. Set the `JWT_SECRET_KEY` environment variable in your EB environment.

### Heroku / Procfile

```bash
web: uvicorn main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | Dev default (change in production) |

## Development

### Code Style

```bash
pip install black flake8

# Format code
black main.py

# Check style
flake8 main.py
```

### Running Tests

```bash
pip install pytest httpx

pytest tests/ -v
```

## Roadmap

- [x] Core API endpoints
- [x] JWT authentication (Pro + Client)
- [x] Avatar management with CRUD
- [x] AI Mind profiling system
- [x] Invitation-based client onboarding
- [x] Multi-avatar client support
- [x] Session feedback (BFK model)
- [x] Supervision feedback
- [x] Discover page API
- [x] Portal analytics
- [ ] Database integration (PostgreSQL)
- [ ] Real AI Mind training pipeline
- [ ] WebSocket support for real-time updates
- [ ] Rate limiting and caching
- [ ] Docker containerization

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Contact

- **Project**: Hamo AI Therapy Platform
- **Email**: chris@hamo.ai
- **GitHub**: https://github.com/chrischengzh/hamo-ume
