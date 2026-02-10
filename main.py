"""
Hamo-UME: Hamo Unified Mind Engine
Backend API Server with JWT Authentication

Tech Stack: Python + FastAPI + JWT
Version: 1.4.5
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import random
import uuid
import hashlib
import os

# JWT dependencies
from jose import JWTError, jwt

# Database module
from database import db

# IMPORTANT: DynamoDB Field Name Mappings
# The database schema uses different field names than the Pydantic models:
# - Model: therapist_id → Database: pro_user_id (in avatars, invitations, AI minds)
# - Model: client_id → Database: client_user_id (in connections)
# These mappings need to be handled when saving/loading data

# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hamo-ume-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

# ============================================================
# ENUMS
# ============================================================

class UserRole(str, Enum):
    THERAPIST = "therapist"
    CLIENT = "client"

class EmotionType(str, Enum):
    ANXIETY = "anxiety"
    DEPRESSION = "depression"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    JOY = "joy"
    NEUTRAL = "neutral"

class PersonalityTrait(str, Enum):
    INTROVERT = "introvert"
    EXTROVERT = "extrovert"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PERFECTIONIST = "perfectionist"
    PEOPLE_PLEASER = "people_pleaser"
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"

class RelationshipStyle(str, Enum):
    SECURE = "secure"
    ANXIOUS = "anxious"
    AVOIDANT = "avoidant"
    DISORGANIZED = "disorganized"

class PSVSQuadrant(str, Enum):
    EXPERT = "expert"
    SUPPORTER = "supporter"
    LEADER = "leader"
    DREAMER = "dreamer"

class PSVSEnergyState(str, Enum):
    POSITIVE = "positive"      # Orange center - homeostatic/balanced
    NEGATIVE = "negative"      # Gray middle - unstable
    NEUROTIC = "neurotic"      # Red outer - crisis

# ============================================================
# PASSWORD UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# ============================================================
# AUTH MODELS - PRO (THERAPIST)
# ============================================================

class ProRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    profession: str
    license_number: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)

class ProLogin(BaseModel):
    email: EmailStr
    password: str

class ProRefreshRequest(BaseModel):
    refresh_token: str

# ============================================================
# AUTH MODELS - CLIENT
# ============================================================

class ClientRegister(BaseModel):
    email: EmailStr
    password: str
    nickname: str  # Changed from full_name to match hamo-client frontend
    invitation_code: str  # Required for client registration

class ClientLogin(BaseModel):
    email: EmailStr
    password: str

class ClientRefreshRequest(BaseModel):
    refresh_token: str

# ============================================================
# USER MODELS
# ============================================================

class UserInDB(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    # Pro (Therapist) specific
    profession: Optional[str] = None
    license_number: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)
    # Client specific
    therapist_id: Optional[str] = None
    avatar_id: Optional[str] = None
    client_profile_id: Optional[str] = None

class ProResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole = UserRole.THERAPIST
    created_at: datetime
    is_active: bool
    profession: Optional[str] = None
    license_number: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)

class ClientResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole = UserRole.CLIENT
    created_at: datetime
    is_active: bool
    therapist_id: Optional[str] = None
    avatar_id: Optional[str] = None
    client_profile_id: Optional[str] = None

class ProTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: ProResponse

class ConnectedAvatar(BaseModel):
    """Legacy model for backward compatibility"""
    id: str
    name: str
    therapist_name: Optional[str] = None

class ConnectedAvatarDetail(BaseModel):
    """Detailed connected avatar information for multi-avatar support"""
    id: str
    avatar_name: str
    pro_name: str
    specialty: str
    therapeutic_approaches: list[str] = Field(default_factory=list)
    about: Optional[str] = None
    avatar_picture: Optional[str] = None
    last_chat_time: datetime

class ClientTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: ClientResponse
    connected_avatars: list[ConnectedAvatarDetail] = Field(default_factory=list)  # Multi-avatar support
    connected_avatar: Optional[ConnectedAvatar] = None  # Legacy field for backward compatibility

# ============================================================
# AVATAR MODELS
# ============================================================

class AvatarCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Avatar name (required)")
    specialty: str = Field(..., min_length=1, description="Specialty area (required, single select)")
    therapeutic_approaches: list[str] = Field(..., min_length=1, max_length=3, description="Therapeutic approaches (required, 1-3)")
    about: str = Field(..., min_length=1, max_length=280, description="About description (required, max 280 chars)")
    experience_years: int = Field(..., ge=0, description="Years of experience (required)")
    experience_months: int = Field(..., ge=0, le=11, description="Months of experience (required, 0-11)")

class AvatarUpdate(BaseModel):
    """Model for updating an avatar - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, description="Avatar name")
    specialty: Optional[str] = Field(None, min_length=1, description="Specialty area")
    therapeutic_approaches: Optional[list[str]] = Field(None, min_length=1, max_length=3, description="Therapeutic approaches (1-3)")
    about: Optional[str] = Field(None, min_length=1, max_length=280, description="About description (max 280 chars)")
    experience_years: Optional[int] = Field(None, ge=0, description="Years of experience")
    experience_months: Optional[int] = Field(None, ge=0, le=11, description="Months of experience (0-11)")

class AvatarInDB(BaseModel):
    id: str
    therapist_id: str
    name: str
    specialty: str
    therapeutic_approaches: list[str] = Field(default_factory=list)
    about: str = ""
    experience_years: int = 0
    experience_months: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_active: bool = True
    client_count: int = 0

class AvatarResponse(AvatarInDB):
    pass

class AvatarUpdateResponse(BaseModel):
    """Response model for avatar update with pro_id"""
    id: str
    name: str
    specialty: str
    therapeutic_approaches: list[str] = Field(default_factory=list)
    about: str = ""
    experience_years: int = 0
    experience_months: int = 0
    pro_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# ============================================================
# CLIENT PROFILE MODELS
# ============================================================

class ClientProfileCreate(BaseModel):
    name: str
    avatar_id: str
    sex: Optional[str] = None
    age: Optional[int] = None
    emotion_pattern: Optional[str] = None
    personality: Optional[str] = None
    cognition: Optional[str] = None
    goals: Optional[str] = None
    therapy_principles: Optional[str] = None

class ClientProfileInDB(BaseModel):
    id: str
    therapist_id: str
    avatar_id: str
    user_id: Optional[str] = None  # Linked user account
    name: str
    sex: Optional[str] = None
    age: Optional[int] = None
    emotion_pattern: Optional[str] = None
    personality: Optional[str] = None
    cognition: Optional[str] = None
    goals: Optional[str] = None
    therapy_principles: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    sessions: int = 0
    avg_time: int = 0

class ClientProfileResponse(ClientProfileInDB):
    avatar_name: Optional[str] = None
    connected_at: Optional[datetime] = None  # When client registered via invitation code

# ============================================================
# CLIENT-AVATAR CONNECTION MODELS (Many-to-Many)
# ============================================================

class ClientAvatarConnectionInDB(BaseModel):
    """Represents a connection between a client and an avatar"""
    id: str
    client_id: str  # User ID (not client profile ID)
    avatar_id: str
    connected_at: datetime = Field(default_factory=datetime.now)
    last_chat_time: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

# ============================================================
# INVITATION MODELS
# ============================================================

class InvitationCreate(BaseModel):
    client_id: str
    avatar_id: str

class InvitationInDB(BaseModel):
    code: str
    therapist_id: str
    client_id: str  # Legacy field
    avatar_id: str
    mind_id: Optional[str] = None  # New: link to AI Mind
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    is_used: bool = False

class InvitationResponse(BaseModel):
    code: str
    client_id: str
    avatar_id: str
    mind_id: Optional[str] = None
    expires_at: datetime
    qr_data: str

# ============================================================
# AI MIND MODELS
# ============================================================

class PersonalityCharacteristics(BaseModel):
    primary_traits: list[PersonalityTrait] = Field(default_factory=list)
    openness: float = Field(ge=0, le=1)
    conscientiousness: float = Field(ge=0, le=1)
    extraversion: float = Field(ge=0, le=1)
    agreeableness: float = Field(ge=0, le=1)
    neuroticism: float = Field(ge=0, le=1)
    description: str = ""

class EmotionPattern(BaseModel):
    dominant_emotions: list[EmotionType] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    coping_mechanisms: list[str] = Field(default_factory=list)
    emotional_stability: float = Field(ge=0, le=1)
    description: str = ""

class CognitionBeliefs(BaseModel):
    core_beliefs: list[str] = Field(default_factory=list)
    cognitive_distortions: list[str] = Field(default_factory=list)
    thinking_patterns: list[str] = Field(default_factory=list)
    self_perception: str = ""
    world_perception: str = ""
    future_perception: str = ""

class RelationshipManipulations(BaseModel):
    attachment_style: RelationshipStyle = RelationshipStyle.SECURE
    relationship_patterns: list[str] = Field(default_factory=list)
    communication_style: str = ""
    conflict_resolution: str = ""
    trust_level: float = Field(ge=0, le=1)
    intimacy_comfort: float = Field(ge=0, le=1)

class UserAIMind(BaseModel):
    """Legacy model for mock data generation"""
    user_id: str
    avatar_id: str
    personality: PersonalityCharacteristics
    emotion_pattern: EmotionPattern
    cognition_beliefs: CognitionBeliefs
    relationship_manipulations: RelationshipManipulations
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(ge=0, le=1)

# New AI Mind models for Pro-created client profiles
class PersonalityInput(BaseModel):
    """Personality input from Pro"""
    primary_traits: list[str] = Field(default_factory=list)
    description: str = ""

class EmotionPatternInput(BaseModel):
    """Emotion pattern input from Pro"""
    dominant_emotions: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    coping_mechanisms: list[str] = Field(default_factory=list)
    description: str = ""

class CognitionBeliefsInput(BaseModel):
    """Cognition beliefs input from Pro"""
    core_beliefs: list[str] = Field(default_factory=list)
    cognitive_distortions: list[str] = Field(default_factory=list)
    thinking_patterns: list[str] = Field(default_factory=list)
    self_perception: str = ""
    world_perception: str = ""
    future_perception: str = ""

class RelationshipInput(BaseModel):
    """Relationship input from Pro"""
    attachment_style: str = "secure"
    relationship_patterns: list[str] = Field(default_factory=list)
    communication_style: str = ""
    conflict_resolution: str = ""

class AIMindCreate(BaseModel):
    """Request body for creating AI Mind"""
    avatar_id: str
    name: str
    sex: Optional[str] = None
    age: Optional[int] = None
    personality: Optional[PersonalityInput] = None
    emotion_pattern: Optional[EmotionPatternInput] = None
    cognition_beliefs: Optional[CognitionBeliefsInput] = None
    relationship_manipulations: Optional[RelationshipInput] = None
    goals: Optional[str] = None
    therapy_principles: Optional[str] = None

class AIMindInDB(BaseModel):
    """AI Mind stored in database"""
    id: str
    user_id: Optional[str] = None  # null until client registers
    avatar_id: str
    therapist_id: str
    name: str
    sex: Optional[str] = None
    age: Optional[int] = None
    personality: Optional[PersonalityInput] = None
    emotion_pattern: Optional[EmotionPatternInput] = None
    cognition_beliefs: Optional[CognitionBeliefsInput] = None
    relationship_manipulations: Optional[RelationshipInput] = None
    goals: Optional[str] = None
    therapy_principles: Optional[str] = None
    connected_at: Optional[datetime] = None  # null until client registers
    created_at: datetime = Field(default_factory=datetime.now)
    sessions: int = 0
    avg_time: int = 0

class AIMindResponse(AIMindInDB):
    """AI Mind response with avatar info"""
    avatar_name: Optional[str] = None
    invitation_code: Optional[str] = None  # Include if not connected

# ============================================================
# FEEDBACK MODELS
# ============================================================

class SessionFeedback(BaseModel):
    session_id: str
    being_energy_level: float = Field(ge=0, le=10)
    being_physical_comfort: float = Field(ge=0, le=10)
    being_description: Optional[str] = None
    feeling_primary_emotion: EmotionType
    feeling_intensity: float = Field(ge=0, le=10)
    feeling_description: Optional[str] = None
    knowing_clarity: float = Field(ge=0, le=10)
    knowing_insights: list[str] = Field(default_factory=list)
    knowing_description: Optional[str] = None
    overall_rating: float = Field(ge=0, le=10)

class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str

# ============================================================
# PSVS (Psychological Semantic Vector Space) MODELS
# ============================================================

class PSVSCoordinates(BaseModel):
    """Represents a position in the PSVS space at a specific time"""
    quadrant: PSVSQuadrant
    energy_state: PSVSEnergyState
    rational_emotional: float = Field(ge=-1.0, le=1.0, description="-1=emotional, +1=rational")
    intro_extro: float = Field(ge=-1.0, le=1.0, description="-1=introvert, +1=extrovert")
    distance_from_center: float = Field(ge=0.0, le=1.0, description="0=homeostatic center, 1=neurotic edge")
    stress_level: float = Field(ge=0.0, le=10.0, description="Internal stress calculation")
    timestamp: datetime = Field(default_factory=datetime.now)

class PSVSProfile(BaseModel):
    """PSVS profile for a client's AI Mind - tracks position and movement over time"""
    id: str
    mind_id: str
    current_position: PSVSCoordinates
    trajectory_history: list[PSVSCoordinates] = Field(default_factory=list, description="Last 50 positions")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ConversationSession(BaseModel):
    """A conversation session between client and avatar"""
    id: str
    mind_id: str
    avatar_id: str
    user_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    message_count: int = 0
    is_active: bool = True

class ConversationMessage(BaseModel):
    """A single message in a conversation with PSVS snapshot"""
    id: str
    session_id: str
    mind_id: str
    role: str  # "user" or "assistant"
    content: str
    psvs_snapshot: Optional[PSVSCoordinates] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Response models for PSVS endpoints
class PSVSProfileResponse(BaseModel):
    """Response model for PSVS profile"""
    id: str
    mind_id: str
    current_position: PSVSCoordinates
    recent_trajectory: list[PSVSCoordinates] = Field(default_factory=list, description="Last 10 positions")
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    """Response when sending a message"""
    message_id: str
    response: str
    psvs_position: PSVSCoordinates
    session_id: str

class SessionStartResponse(BaseModel):
    """Response when starting a session"""
    session_id: str
    mind_id: str
    avatar_id: str
    initial_psvs_position: PSVSCoordinates

# ============================================================
# IN-MEMORY STORAGE (LEGACY - Commented out, now using DynamoDB)
# ============================================================

# users_db: dict[str, UserInDB] = {}
# avatars_db: dict[str, AvatarInDB] = {}
# client_profiles_db: dict[str, ClientProfileInDB] = {}
# invitations_db: dict[str, InvitationInDB] = {}
# client_avatar_connections_db: dict[str, ClientAvatarConnectionInDB] = {}  # connection_id -> connection
# ai_minds_db: dict[str, AIMindInDB] = {}  # mind_id -> AI Mind
mind_cache: dict[str, UserAIMind] = {}  # Legacy cache for mock data (still in-memory)
feedback_storage: list[dict] = []  # Still in-memory for now
supervision_feedback_db: dict[str, list[dict]] = {}  # Still in-memory (defined later)
# pro_refresh_tokens_db: dict[str, str] = {}  # refresh_token -> user_id
# client_refresh_tokens_db: dict[str, str] = {}  # refresh_token -> user_id

# PSVS storage - now using DynamoDB
# psvs_profiles_db: dict[str, PSVSProfile] = {}  # mind_id -> PSVS Profile
# conversation_sessions_db: dict[str, ConversationSession] = {}  # session_id -> Session
# conversation_messages_db: dict[str, ConversationMessage] = {}  # message_id -> Message

# ============================================================
# JWT UTILITIES
# ============================================================

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, role: UserRole) -> str:
    to_encode = {"sub": user_id, "type": "refresh", "role": role}
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    db.create_refresh_token(token, user_id, role.value)
    return token

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    user_data = db.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    user = UserInDB(**user_data)
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")
    return user

async def get_current_pro(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != UserRole.THERAPIST:
        raise HTTPException(status_code=403, detail="Pro (Therapist) access required")
    return current_user

async def get_current_client(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Client access required")
    return current_user

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_connected_avatars_for_client(client_user_id: str) -> list[ConnectedAvatarDetail]:
    """Get all connected avatars for a client user"""
    connected_avatars = []
    connections = db.get_connections_by_client(client_user_id)
    for conn_data in connections:
        if conn_data.get("is_active", False):
            avatar_data = db.get_avatar_by_id(conn_data["avatar_id"])
            if avatar_data:
                therapist_data = db.get_user_by_id(avatar_data["therapist_id"])
                # Handle both client_id (model) and client_user_id (database) field names
                last_chat = conn_data.get("last_chat_time")
                if isinstance(last_chat, str):
                    last_chat = datetime.fromisoformat(last_chat)
                connected_avatars.append(ConnectedAvatarDetail(
                    id=avatar_data["id"],
                    avatar_name=avatar_data["name"],
                    pro_name=therapist_data["full_name"] if therapist_data else "Therapist",
                    specialty=avatar_data["specialty"],
                    therapeutic_approaches=avatar_data["therapeutic_approaches"],
                    about=avatar_data["about"],
                    avatar_picture=None,
                    last_chat_time=last_chat
                ))
    return connected_avatars

def create_client_avatar_connection(client_user_id: str, avatar_id: str) -> ClientAvatarConnectionInDB:
    """Create a new client-avatar connection"""
    connection_id = str(uuid.uuid4())
    now = datetime.now()
    connection = ClientAvatarConnectionInDB(
        id=connection_id,
        client_id=client_user_id,
        avatar_id=avatar_id,
        connected_at=now,
        last_chat_time=now,
        is_active=True
    )
    # Map client_id to client_user_id for database storage
    connection_dict = connection.model_dump()
    connection_dict["client_user_id"] = connection_dict.pop("client_id")
    db.create_connection(connection_dict)
    return connection

def get_client_connected_at(client_profile: ClientProfileInDB) -> Optional[datetime]:
    """Get the connected_at time for a client profile by finding when a real user registered"""
    # Find the user linked to this client profile
    if not client_profile.user_id:
        return None  # No real user has registered yet

    # Find the connection for this user
    connections = db.get_connections_by_client(client_profile.user_id)
    for conn_data in connections:
        if conn_data.get("is_active", False):
            connected_at = conn_data["connected_at"]
            if isinstance(connected_at, str):
                return datetime.fromisoformat(connected_at)
            return connected_at
    return None

def find_invitation_by_mind_id(mind_id: str, pro_user_id: str) -> Optional[str]:
    """Find invitation code for a mind_id by scanning pro's invitations"""
    invitations = db.get_invitations_by_pro(pro_user_id)
    for inv_data in invitations:
        if inv_data.get("mind_id") == mind_id and not inv_data.get("is_used", False):
            return inv_data["code"]
    return None

# ============================================================
# MOCK DATA GENERATOR
# ============================================================

class MockDataGenerator:
    @staticmethod
    def generate_user_ai_mind(user_id: str, avatar_id: str) -> UserAIMind:
        personality = PersonalityCharacteristics(
            primary_traits=random.sample(list(PersonalityTrait), k=random.randint(2, 4)),
            openness=round(random.uniform(0.3, 0.9), 2),
            conscientiousness=round(random.uniform(0.3, 0.9), 2),
            extraversion=round(random.uniform(0.2, 0.8), 2),
            agreeableness=round(random.uniform(0.4, 0.9), 2),
            neuroticism=round(random.uniform(0.3, 0.7), 2),
            description="Client shows introverted tendencies with high conscientiousness."
        )
        emotion_pattern = EmotionPattern(
            dominant_emotions=random.sample([EmotionType.ANXIETY, EmotionType.SADNESS, EmotionType.NEUTRAL], k=2),
            triggers=["Work deadlines", "Social situations", "Conflict or criticism"],
            coping_mechanisms=["Withdrawal", "Over-preparation", "Seeking reassurance"],
            emotional_stability=round(random.uniform(0.4, 0.7), 2),
            description="Experiences heightened anxiety in performance situations."
        )
        cognition_beliefs = CognitionBeliefs(
            core_beliefs=["I must perform perfectly to be accepted", "Making mistakes means failure"],
            cognitive_distortions=["All-or-nothing thinking", "Catastrophizing", "Mind reading"],
            thinking_patterns=["Rumination", "Anticipatory worry", "Self-critical dialogue"],
            self_perception="Views self as capable but fundamentally flawed",
            world_perception="World is demanding and judgmental",
            future_perception="Future success depends on perfect performance"
        )
        relationship_manipulations = RelationshipManipulations(
            attachment_style=random.choice([RelationshipStyle.ANXIOUS, RelationshipStyle.AVOIDANT]),
            relationship_patterns=["Difficulty expressing needs", "Fear of abandonment"],
            communication_style="Indirect, tends to hint rather than state needs",
            conflict_resolution="Avoidant - prefers to minimize conflicts",
            trust_level=round(random.uniform(0.4, 0.7), 2),
            intimacy_comfort=round(random.uniform(0.3, 0.6), 2)
        )
        return UserAIMind(
            user_id=user_id, avatar_id=avatar_id,
            personality=personality, emotion_pattern=emotion_pattern,
            cognition_beliefs=cognition_beliefs, relationship_manipulations=relationship_manipulations,
            last_updated=datetime.now(), confidence_score=round(random.uniform(0.7, 0.95), 2)
        )

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Hamo-UME API",
    description="Hamo Unified Mind Engine - Backend API v1.4.5",
    version="1.4.5"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # 本地开发
        "http://localhost:3000",           # 本地开发备用端口
        "https://hamo-pro.vercel.app",     # Vercel 生产环境 - Pro
        "https://hamo-client.vercel.app",  # Vercel 生产环境 - Client
        "https://hamo-portal.vercel.app",  # Vercel 生产环境 - Portal
        "https://*.vercel.app",            # 所有 Vercel 部署
        "https://hamo.ai",                 # 主域名
        "https://*.hamo.ai",               # 子域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/", tags=["Health"])
async def root():
    return {"service": "Hamo-UME", "version": "1.4.5", "status": "running"}

# ============================================================
# PRO (THERAPIST) AUTH ENDPOINTS
# ============================================================

@app.post("/api/auth/registerPro", response_model=ProTokenResponse, tags=["Auth - Pro"])
async def register_pro(user_data: ProRegister):
    """Register a new Pro (Therapist) account"""
    # Only check for duplicate email among Pro users (Pro and Client are independent systems)
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user and existing_user.get("role") == UserRole.THERAPIST:
        raise HTTPException(status_code=400, detail="Email already registered as Pro")

    user_id = str(uuid.uuid4())
    new_user = UserInDB(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        role=UserRole.THERAPIST,
        hashed_password=hash_password(user_data.password),
        profession=user_data.profession,
        license_number=user_data.license_number,
        specializations=user_data.specializations
    )
    db.create_user(new_user.model_dump())

    access_token = create_access_token({"sub": user_id, "email": user_data.email, "role": UserRole.THERAPIST})
    refresh_token = create_refresh_token(user_id, UserRole.THERAPIST)

    return ProTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ProResponse(**new_user.model_dump())
    )

@app.post("/api/auth/loginPro", response_model=ProTokenResponse, tags=["Auth - Pro"])
async def login_pro(credentials: ProLogin):
    """Login as Pro (Therapist)"""
    user_data = db.get_user_by_email(credentials.email)

    if not user_data or user_data.get("role") != UserRole.THERAPIST:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = UserInDB(**user_data)
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account inactive")

    access_token = create_access_token({"sub": user.id, "email": user.email, "role": UserRole.THERAPIST})
    refresh_token = create_refresh_token(user.id, UserRole.THERAPIST)

    return ProTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ProResponse(**user.model_dump())
    )

@app.post("/api/auth/refreshPro", response_model=ProTokenResponse, tags=["Auth - Pro"])
async def refresh_pro_token(request: ProRefreshRequest):
    """Refresh Pro access token"""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh" or payload.get("role") != UserRole.THERAPIST:
        raise HTTPException(status_code=401, detail="Invalid Pro refresh token")

    user_id = payload.get("sub")
    token_data = db.get_refresh_token(request.refresh_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    user_data = db.get_user_by_id(user_id)
    if not user_data or user_data.get("role") != UserRole.THERAPIST:
        raise HTTPException(status_code=401, detail="Pro user not found")

    user = UserInDB(**user_data)
    db.delete_refresh_token(request.refresh_token)
    access_token = create_access_token({"sub": user.id, "email": user.email, "role": UserRole.THERAPIST})
    new_refresh_token = create_refresh_token(user.id, UserRole.THERAPIST)

    return ProTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ProResponse(**user.model_dump())
    )

# ============================================================
# CLIENT AUTH ENDPOINTS
# ============================================================

@app.post("/api/auth/registerClient", response_model=ClientTokenResponse, tags=["Auth - Client"])
async def register_client(user_data: ClientRegister):
    """Register a new Client account (requires invitation code)"""
    # Only check for duplicate email among Client users (Pro and Client are independent systems)
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user and existing_user.get("role") == UserRole.CLIENT:
        raise HTTPException(status_code=400, detail="Email already registered as Client")

    # Validate invitation code
    invitation_data = db.get_invitation_by_code(user_data.invitation_code)
    if not invitation_data:
        raise HTTPException(status_code=400, detail="Invalid invitation code")
    if invitation_data.get("is_used", False):
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if datetime.fromisoformat(invitation_data["expires_at"]) < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")

    user_id = str(uuid.uuid4())
    now = datetime.now()

    # Bind to AI Mind if mind_id exists in invitation
    if invitation_data.get("mind_id"):
        mind_data = db.get_ai_mind_by_id(invitation_data["mind_id"])
        if mind_data:
            mind_data["user_id"] = user_id
            mind_data["connected_at"] = now.isoformat()
            db.create_ai_mind(mind_data)  # Update by re-creating

    # Legacy: Create or get client profile (still using in-memory for now)
    client_profile_id = invitation_data.get("client_id", "")
    if not client_profile_id or client_profile_id == "":
        # Auto-create client profile if not exists
        client_profile_id = str(uuid.uuid4())
        avatar_data = db.get_avatar_by_id(invitation_data["avatar_id"])
        # Note: client_profiles_db is legacy and not migrated to DB yet
        # For now we skip this logic since AI Minds replace client profiles

    new_user = UserInDB(
        id=user_id,
        email=user_data.email,
        full_name=user_data.nickname,  # Use nickname from client frontend
        role=UserRole.CLIENT,
        hashed_password=hash_password(user_data.password),
        therapist_id=invitation_data["therapist_id"],
        avatar_id=invitation_data["avatar_id"],
        client_profile_id=client_profile_id
    )
    db.create_user(new_user.model_dump())

    # Mark invitation as used
    invitation_data["is_used"] = True
    db.create_invitation(invitation_data)  # Update by re-creating

    # Create client-avatar connection (multi-avatar support)
    create_client_avatar_connection(user_id, invitation_data["avatar_id"])

    # Get all connected avatars for this client
    connected_avatars = get_connected_avatars_for_client(user_id)

    # Get legacy connected_avatar for backward compatibility
    avatar_data = db.get_avatar_by_id(invitation_data["avatar_id"])
    therapist_data = db.get_user_by_id(invitation_data["therapist_id"])
    connected_avatar = None
    if avatar_data:
        connected_avatar = ConnectedAvatar(
            id=avatar_data["id"],
            name=avatar_data["name"],
            therapist_name=therapist_data["full_name"] if therapist_data else None
        )

    access_token = create_access_token({"sub": user_id, "email": user_data.email, "role": UserRole.CLIENT})
    refresh_token = create_refresh_token(user_id, UserRole.CLIENT)

    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ClientResponse(**new_user.model_dump()),
        connected_avatars=connected_avatars,
        connected_avatar=connected_avatar
    )

@app.post("/api/auth/loginClient", response_model=ClientTokenResponse, tags=["Auth - Client"])
async def login_client(credentials: ClientLogin):
    """Login as Client"""
    user_data = db.get_user_by_email(credentials.email)

    if not user_data or user_data.get("role") != UserRole.CLIENT:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = UserInDB(**user_data)
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account inactive")

    # Get all connected avatars for this client
    connected_avatars = get_connected_avatars_for_client(user.id)

    # Get legacy connected_avatar for backward compatibility (first/primary avatar)
    connected_avatar = None
    if user.avatar_id:
        avatar_data = db.get_avatar_by_id(user.avatar_id)
        therapist_data = db.get_user_by_id(user.therapist_id) if user.therapist_id else None
        if avatar_data:
            connected_avatar = ConnectedAvatar(
                id=avatar_data["id"],
                name=avatar_data["name"],
                therapist_name=therapist_data["full_name"] if therapist_data else None
            )

    access_token = create_access_token({"sub": user.id, "email": user.email, "role": UserRole.CLIENT})
    refresh_token = create_refresh_token(user.id, UserRole.CLIENT)

    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ClientResponse(**user.model_dump()),
        connected_avatars=connected_avatars,
        connected_avatar=connected_avatar
    )

@app.post("/api/auth/refreshClient", response_model=ClientTokenResponse, tags=["Auth - Client"])
async def refresh_client_token(request: ClientRefreshRequest):
    """Refresh Client access token"""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh" or payload.get("role") != UserRole.CLIENT:
        raise HTTPException(status_code=401, detail="Invalid Client refresh token")

    user_id = payload.get("sub")
    token_data = db.get_refresh_token(request.refresh_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    user_data = db.get_user_by_id(user_id)
    if not user_data or user_data.get("role") != UserRole.CLIENT:
        raise HTTPException(status_code=401, detail="Client user not found")

    user = UserInDB(**user_data)

    # Get all connected avatars for this client
    connected_avatars = get_connected_avatars_for_client(user.id)

    # Get legacy connected_avatar for backward compatibility (first/primary avatar)
    connected_avatar = None
    if user.avatar_id:
        avatar_data = db.get_avatar_by_id(user.avatar_id)
        therapist_data = db.get_user_by_id(user.therapist_id) if user.therapist_id else None
        if avatar_data:
            connected_avatar = ConnectedAvatar(
                id=avatar_data["id"],
                name=avatar_data["name"],
                therapist_name=therapist_data["full_name"] if therapist_data else None
            )

    db.delete_refresh_token(request.refresh_token)
    access_token = create_access_token({"sub": user.id, "email": user.email, "role": UserRole.CLIENT})
    new_refresh_token = create_refresh_token(user.id, UserRole.CLIENT)

    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ClientResponse(**user.model_dump()),
        connected_avatars=connected_avatars,
        connected_avatar=connected_avatar
    )

# ============================================================
# USER ENDPOINTS
# ============================================================

@app.get("/api/users/me/pro", response_model=ProResponse, tags=["Users"])
async def get_pro_me(current_user: UserInDB = Depends(get_current_pro)):
    """Get current Pro (Therapist) user info"""
    return ProResponse(**current_user.model_dump())

@app.get("/api/users/me/client", response_model=ClientResponse, tags=["Users"])
async def get_client_me(current_user: UserInDB = Depends(get_current_client)):
    """Get current Client user info"""
    return ClientResponse(**current_user.model_dump())

# ============================================================
# AVATAR ENDPOINTS (Pro only)
# ============================================================

@app.get("/api/avatars", response_model=list[AvatarResponse], tags=["Avatars"])
async def get_avatars(current_user: UserInDB = Depends(get_current_pro)):
    """Get all avatars for current Pro"""
    avatars = db.get_avatars_by_pro(current_user.id)
    return [AvatarResponse(**a) for a in avatars]

@app.post("/api/avatars", response_model=AvatarResponse, tags=["Avatars"])
async def create_avatar(avatar_data: AvatarCreate, current_user: UserInDB = Depends(get_current_pro)):
    """Create a new avatar"""
    # Validation is handled by Pydantic model, but add extra checks
    if len(avatar_data.therapeutic_approaches) < 1 or len(avatar_data.therapeutic_approaches) > 3:
        raise HTTPException(status_code=400, detail="therapeutic_approaches must have 1-3 items")
    if len(avatar_data.about) > 280:
        raise HTTPException(status_code=400, detail="about must be max 280 characters")

    avatar_id = str(uuid.uuid4())
    new_avatar = AvatarInDB(
        id=avatar_id,
        therapist_id=current_user.id,
        name=avatar_data.name,
        specialty=avatar_data.specialty,
        therapeutic_approaches=avatar_data.therapeutic_approaches,
        about=avatar_data.about,
        experience_years=avatar_data.experience_years,
        experience_months=avatar_data.experience_months
    )
    db.create_avatar(new_avatar.model_dump())
    return AvatarResponse(**new_avatar.model_dump())

@app.get("/api/avatars/{avatar_id}", response_model=AvatarResponse, tags=["Avatars"])
async def get_avatar(avatar_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get avatar by ID"""
    avatar_data = db.get_avatar_by_id(avatar_id)
    if not avatar_data:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return AvatarResponse(**avatar_data)

@app.put("/api/avatars/{avatar_id}", response_model=AvatarUpdateResponse, tags=["Avatars"])
async def update_avatar(avatar_id: str, avatar_data: AvatarUpdate, current_user: UserInDB = Depends(get_current_pro)):
    """Update an existing avatar (Pro only, must be the owner)"""
    # Check if avatar exists
    avatar_dict = db.get_avatar_by_id(avatar_id)
    if not avatar_dict:
        raise HTTPException(status_code=404, detail="Avatar not found")

    avatar = AvatarInDB(**avatar_dict)

    # Check ownership - only the Pro who created the avatar can update it
    if avatar.therapist_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own avatars")

    # Update only provided fields
    update_data = avatar_data.model_dump(exclude_unset=True)

    # Validate therapeutic_approaches if provided
    if "therapeutic_approaches" in update_data:
        if len(update_data["therapeutic_approaches"]) < 1 or len(update_data["therapeutic_approaches"]) > 3:
            raise HTTPException(status_code=400, detail="therapeutic_approaches must have 1-3 items")

    # Validate about if provided
    if "about" in update_data and len(update_data["about"]) > 280:
        raise HTTPException(status_code=400, detail="about must be max 280 characters")

    # Apply updates
    for field, value in update_data.items():
        setattr(avatar, field, value)

    # Set updated_at timestamp
    avatar.updated_at = datetime.now()

    # Save to database
    db.create_avatar(avatar.model_dump())

    return AvatarUpdateResponse(
        id=avatar.id,
        name=avatar.name,
        specialty=avatar.specialty,
        therapeutic_approaches=avatar.therapeutic_approaches,
        about=avatar.about,
        experience_years=avatar.experience_years,
        experience_months=avatar.experience_months,
        pro_id=avatar.therapist_id,
        created_at=avatar.created_at,
        updated_at=avatar.updated_at
    )

# ============================================================
# DISCOVER ENDPOINTS (Public for Client Discovery)
# ============================================================

class DiscoverAvatarResponse(BaseModel):
    """Avatar response for Discover page with Pro info"""
    id: str
    name: str
    specialty: str
    therapeutic_approaches: list[str] = Field(default_factory=list)
    about: str = ""
    experience_years: int = 0
    experience_months: int = 0
    pro_name: str
    avatar_picture: Optional[str] = None

@app.get("/api/discover/avatars", response_model=list[DiscoverAvatarResponse], tags=["Discover"])
async def discover_avatars():
    """Get all public avatars for Client discovery page (no authentication required)"""
    result = []
    avatars = db.get_all_avatars()
    for avatar_data in avatars:
        if avatar_data.get("is_active", True):
            therapist_data = db.get_user_by_id(avatar_data["therapist_id"])
            result.append(DiscoverAvatarResponse(
                id=avatar_data["id"],
                name=avatar_data["name"],
                specialty=avatar_data["specialty"],
                therapeutic_approaches=avatar_data["therapeutic_approaches"],
                about=avatar_data["about"],
                experience_years=avatar_data["experience_years"],
                experience_months=avatar_data["experience_months"],
                pro_name=therapist_data["full_name"] if therapist_data else "Therapist",
                avatar_picture=None
            ))
    return result

# ============================================================
# AI MIND ENDPOINTS (Pro creates client AI Mind)
# ============================================================

@app.post("/api/mind", response_model=AIMindResponse, tags=["AI Mind"])
async def create_ai_mind(mind_data: AIMindCreate, current_user: UserInDB = Depends(get_current_pro)):
    """Create a new AI Mind for a client (Pro only)"""
    # Verify avatar exists and belongs to current pro
    avatar_dict = db.get_avatar_by_id(mind_data.avatar_id)
    if not avatar_dict:
        raise HTTPException(status_code=404, detail="Avatar not found")
    if avatar_dict["therapist_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Avatar does not belong to you")

    avatar = AvatarInDB(**avatar_dict)
    mind_id = str(uuid.uuid4())
    new_mind = AIMindInDB(
        id=mind_id,
        user_id=None,  # Will be set when client registers
        avatar_id=mind_data.avatar_id,
        therapist_id=current_user.id,
        name=mind_data.name,
        sex=mind_data.sex,
        age=mind_data.age,
        personality=mind_data.personality,
        emotion_pattern=mind_data.emotion_pattern,
        cognition_beliefs=mind_data.cognition_beliefs,
        relationship_manipulations=mind_data.relationship_manipulations,
        goals=mind_data.goals,
        therapy_principles=mind_data.therapy_principles,
        connected_at=None,
        created_at=datetime.now()
    )
    db.create_ai_mind(new_mind.model_dump())

    # Update avatar client count
    avatar.client_count += 1
    db.create_avatar(avatar.model_dump())

    # Auto-initialize PSVS profile
    try:
        from psvs.calculator import calculate_initial_psvs_position

        ai_mind_dict = {
            "personality": mind_data.personality.model_dump() if mind_data.personality else {},
            "emotion_pattern": mind_data.emotion_pattern.model_dump() if mind_data.emotion_pattern else {},
            "cognition_beliefs": mind_data.cognition_beliefs.model_dump() if mind_data.cognition_beliefs else {},
            "relationship_manipulations": mind_data.relationship_manipulations.model_dump() if mind_data.relationship_manipulations else {},
        }

        initial_coords = calculate_initial_psvs_position(ai_mind_dict)

        psvs_id = str(uuid.uuid4())
        psvs_profile = PSVSProfile(
            id=psvs_id,
            mind_id=mind_id,
            current_position=PSVSCoordinates(**initial_coords),
            trajectory_history=[PSVSCoordinates(**initial_coords)],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.create_psvs_profile(psvs_profile.model_dump())
    except Exception as e:
        # Don't fail AI Mind creation if PSVS initialization fails
        print(f"Warning: PSVS profile initialization failed: {e}")

    return AIMindResponse(
        **new_mind.model_dump(),
        avatar_name=avatar.name
    )

@app.get("/api/mind/{mind_id}", response_model=AIMindResponse, tags=["AI Mind"])
async def get_ai_mind(mind_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get AI Mind by ID"""
    mind_data = db.get_ai_mind_by_id(mind_id)
    if not mind_data:
        raise HTTPException(status_code=404, detail="AI Mind not found")

    avatar_data = db.get_avatar_by_id(mind_data["avatar_id"])

    # Find invitation code if not connected
    invitation_code = None
    if mind_data.get("connected_at") is None:
        invitation_code = find_invitation_by_mind_id(mind_id, mind_data["therapist_id"])

    return AIMindResponse(
        **mind_data,
        avatar_name=avatar_data["name"] if avatar_data else None,
        invitation_code=invitation_code
    )

# ============================================================
# CLIENT PROFILE ENDPOINTS (Pro only) - Now returns AI Minds
# ============================================================

@app.get("/api/clients", response_model=list[AIMindResponse], tags=["Clients"])
async def get_clients(current_user: UserInDB = Depends(get_current_pro)):
    """Get all AI Minds (clients) for current Pro, including unconnected ones"""
    result = []
    minds = db.get_ai_minds_by_therapist(current_user.id)

    for mind_data in minds:
        avatar_data = db.get_avatar_by_id(mind_data["avatar_id"])

        # Find invitation code if not connected
        invitation_code = None
        if mind_data.get("connected_at") is None:
            invitation_code = find_invitation_by_mind_id(mind_data["id"], current_user.id)

        result.append(AIMindResponse(
            **mind_data,
            avatar_name=avatar_data["name"] if avatar_data else None,
            invitation_code=invitation_code
        ))
    return result

@app.post("/api/clients", response_model=ClientProfileResponse, tags=["Clients"])
async def create_client(client_data: ClientProfileCreate, current_user: UserInDB = Depends(get_current_pro)):
    """Create a new client profile (Legacy endpoint)"""
    avatar = avatars_db.get(client_data.avatar_id)
    if not avatar or avatar.therapist_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid avatar ID")

    client_id = str(uuid.uuid4())
    new_client = ClientProfileInDB(
        id=client_id,
        therapist_id=current_user.id,
        avatar_id=client_data.avatar_id,
        name=client_data.name,
        sex=client_data.sex,
        age=client_data.age,
        emotion_pattern=client_data.emotion_pattern,
        personality=client_data.personality,
        cognition=client_data.cognition,
        goals=client_data.goals,
        therapy_principles=client_data.therapy_principles
    )
    client_profiles_db[client_id] = new_client
    avatar.client_count += 1

    return ClientProfileResponse(**new_client.model_dump(), avatar_name=avatar.name)

@app.get("/api/clients/{client_id}", response_model=AIMindResponse, tags=["Clients"])
async def get_client(client_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get client (AI Mind) by ID"""
    # First try AI Mind
    mind = ai_minds_db.get(client_id)
    if mind:
        avatar = avatars_db.get(mind.avatar_id)
        invitation_code = None
        if mind.connected_at is None:
            for inv in invitations_db.values():
                if inv.mind_id == mind.id and not inv.is_used:
                    invitation_code = inv.code
                    break
        return AIMindResponse(
            **mind.model_dump(),
            avatar_name=avatar.name if avatar else None,
            invitation_code=invitation_code
        )

    # Fallback to legacy client profile
    client = client_profiles_db.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    avatar = avatars_db.get(client.avatar_id)
    connected_at = get_client_connected_at(client)
    # Convert to AIMindResponse format
    return AIMindResponse(
        id=client.id,
        user_id=client.user_id,
        avatar_id=client.avatar_id,
        therapist_id=client.therapist_id,
        name=client.name,
        sex=client.sex,
        age=client.age,
        connected_at=connected_at,
        created_at=datetime.now(),
        avatar_name=avatar.name if avatar else None
    )

# ============================================================
# INVITATION ENDPOINTS (Pro only)
# ============================================================

class ProInvitationGenerateRequest(BaseModel):
    avatar_id: Optional[str] = None  # Legacy field
    mind_id: Optional[str] = None  # New: use mind_id

class ProInvitationGenerateResponse(BaseModel):
    invitation_code: str
    expires_at: datetime
    mind_id: Optional[str] = None

@app.post("/api/pro/invitation/generate", response_model=ProInvitationGenerateResponse, tags=["Invitations"])
async def generate_pro_invitation(invite_data: ProInvitationGenerateRequest, current_user: UserInDB = Depends(get_current_pro)):
    """Generate an invitation code for a client (Pro endpoint for hamo-pro frontend)"""
    avatar_id = None
    mind_id = invite_data.mind_id

    # If mind_id is provided, use it to get avatar_id
    if mind_id:
        mind_data = db.get_ai_mind_by_id(mind_id)
        if not mind_data:
            raise HTTPException(status_code=404, detail="AI Mind not found")
        if mind_data["therapist_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="AI Mind does not belong to you")
        avatar_id = mind_data["avatar_id"]
    elif invite_data.avatar_id:
        # Legacy: use avatar_id directly
        avatar_id = invite_data.avatar_id
    else:
        raise HTTPException(status_code=400, detail="Either mind_id or avatar_id is required")

    avatar_data = db.get_avatar_by_id(avatar_id)
    if not avatar_data or avatar_data["therapist_id"] != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid avatar ID")

    code = f"HAMO-{str(uuid.uuid4())[:6].upper()}"
    expires_at = datetime.now() + timedelta(days=7)

    invitation = InvitationInDB(
        code=code,
        therapist_id=current_user.id,
        client_id="",  # Legacy field
        avatar_id=avatar_id,
        mind_id=mind_id,
        expires_at=expires_at
    )
    db.create_invitation(invitation.model_dump())

    return ProInvitationGenerateResponse(
        invitation_code=code,
        expires_at=expires_at,
        mind_id=mind_id
    )

@app.post("/api/invitations", response_model=InvitationResponse, tags=["Invitations"])
async def create_invitation(invite_data: InvitationCreate, current_user: UserInDB = Depends(get_current_pro)):
    """Generate an invitation code for a client"""
    client = client_profiles_db.get(invite_data.client_id)
    if not client or client.therapist_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid client ID")
    
    avatar = avatars_db.get(invite_data.avatar_id)
    if not avatar or avatar.therapist_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid avatar ID")
    
    code = str(uuid.uuid4())[:8].upper()
    expires_at = datetime.now() + timedelta(days=7)
    
    invitation = InvitationInDB(
        code=code,
        therapist_id=current_user.id,
        client_id=invite_data.client_id,
        avatar_id=invite_data.avatar_id,
        expires_at=expires_at
    )
    invitations_db[code] = invitation
    
    return InvitationResponse(
        code=code,
        client_id=invite_data.client_id,
        avatar_id=invite_data.avatar_id,
        expires_at=expires_at,
        qr_data=f"hamo://invite/{code}"
    )

@app.get("/api/invitations/{code}", tags=["Invitations"])
async def validate_invitation(code: str):
    """Validate an invitation code (public endpoint)"""
    invitation_data = db.get_invitation_by_code(code)
    if not invitation_data:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    if invitation_data.get("is_used", False):
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if datetime.fromisoformat(invitation_data["expires_at"]) < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")

    avatar_data = db.get_avatar_by_id(invitation_data["avatar_id"])
    therapist_data = db.get_user_by_id(invitation_data["therapist_id"])

    return {
        "valid": True,
        "avatar_name": avatar_data["name"] if avatar_data else None,
        "therapist_name": therapist_data["full_name"] if therapist_data else None,
        "expires_at": invitation_data["expires_at"]
    }

# ============================================================
# CLIENT INVITATION ENDPOINTS
# ============================================================

class ClientInvitationValidateRequest(BaseModel):
    invitation_code: str

@app.post("/api/client/invitation/validate", tags=["Invitations"])
async def validate_client_invitation(request: ClientInvitationValidateRequest):
    """Validate an invitation code (for hamo-client frontend)"""
    invitation_data = db.get_invitation_by_code(request.invitation_code)
    if not invitation_data:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    if invitation_data.get("is_used", False):
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if datetime.fromisoformat(invitation_data["expires_at"]) < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")

    avatar_data = db.get_avatar_by_id(invitation_data["avatar_id"])
    therapist_data = db.get_user_by_id(invitation_data["therapist_id"])

    return {
        "valid": True,
        "pro_avatar": {
            "id": avatar_data["id"] if avatar_data else None,
            "name": avatar_data["name"] if avatar_data else None,
            "therapist_name": therapist_data["full_name"] if therapist_data else None
        }
    }

# ============================================================
# CLIENT AVATAR ENDPOINTS (Multi-Avatar Support)
# ============================================================

class InvitationCodeRequest(BaseModel):
    invitation_code: str

class ConnectAvatarResponse(BaseModel):
    avatar: ConnectedAvatarDetail

@app.get("/api/client/avatars", response_model=list[ConnectedAvatarDetail], tags=["Client Avatars"])
async def get_client_avatars(current_user: UserInDB = Depends(get_current_client)):
    """Get all avatars connected to the current client"""
    return get_connected_avatars_for_client(current_user.id)

@app.post("/api/client/avatar/connect", response_model=ConnectAvatarResponse, tags=["Client Avatars"])
async def connect_avatar(request: InvitationCodeRequest, current_user: UserInDB = Depends(get_current_client)):
    """Connect to a new avatar using an invitation code"""
    # Validate invitation code
    invitation_data = db.get_invitation_by_code(request.invitation_code)
    if not invitation_data:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    if invitation_data.get("is_used", False):
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if datetime.fromisoformat(invitation_data["expires_at"]) < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")

    # Check if already connected to this avatar
    connections = db.get_connections_by_client(current_user.id)
    for conn_data in connections:
        if conn_data["avatar_id"] == invitation_data["avatar_id"] and conn_data.get("is_active", False):
            raise HTTPException(status_code=400, detail="Already connected to this avatar")

    # Create new connection (without removing existing connections - multi-avatar support)
    connection = create_client_avatar_connection(current_user.id, invitation_data["avatar_id"])

    # Bind to AI Mind if mind_id exists in invitation
    now = datetime.now()
    if invitation_data.get("mind_id"):
        mind_data = db.get_ai_mind_by_id(invitation_data["mind_id"])
        if mind_data:
            mind_data["user_id"] = current_user.id
            mind_data["connected_at"] = now.isoformat()
            db.create_ai_mind(mind_data)  # Update by re-creating

    # Mark invitation as used
    invitation_data["is_used"] = True
    db.create_invitation(invitation_data)  # Update by re-creating

    # Get avatar details for response
    avatar_data = db.get_avatar_by_id(invitation_data["avatar_id"])
    therapist_data = db.get_user_by_id(invitation_data["therapist_id"])

    if not avatar_data:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Build response with connection details
    connected_avatar = ConnectedAvatarDetail(
        id=avatar_data["id"],
        avatar_name=avatar_data["name"],
        pro_name=therapist_data["full_name"] if therapist_data else "Therapist",
        specialty=avatar_data["specialty"],
        therapeutic_approaches=avatar_data["therapeutic_approaches"],
        about=avatar_data["about"],
        avatar_picture=None,
        last_chat_time=connection.last_chat_time
    )

    return ConnectAvatarResponse(avatar=connected_avatar)

class AvatarIdRequest(BaseModel):
    avatar_id: str

@app.post("/api/client/avatar/connect-by-id", response_model=ConnectAvatarResponse, tags=["Client Avatars"])
async def connect_avatar_by_id(request: AvatarIdRequest, current_user: UserInDB = Depends(get_current_client)):
    """Connect to an avatar directly by avatar_id (from Discover page).
    This also creates an AI Mind for this Avatar + Client pair.
    """
    # Check if avatar exists
    avatar_dict = db.get_avatar_by_id(request.avatar_id)
    if not avatar_dict:
        raise HTTPException(status_code=404, detail="Avatar not found")
    if not avatar_dict.get("is_active", True):
        raise HTTPException(status_code=400, detail="Avatar is not active")

    avatar = AvatarInDB(**avatar_dict)

    # Check if already connected to this avatar
    connections = db.get_connections_by_client(current_user.id)
    for conn_data in connections:
        if conn_data["avatar_id"] == request.avatar_id and conn_data.get("is_active", False):
            raise HTTPException(status_code=400, detail="Already connected to this avatar")

    # Create new connection (multi-avatar support)
    now = datetime.now()
    connection = create_client_avatar_connection(current_user.id, request.avatar_id)

    # Create AI Mind for this Avatar + Client pair
    mind_id = str(uuid.uuid4())
    new_mind = AIMindInDB(
        id=mind_id,
        user_id=current_user.id,  # Already connected
        avatar_id=request.avatar_id,
        therapist_id=avatar.therapist_id,
        name=current_user.full_name,  # Use client's name
        sex=None,
        age=None,
        personality=None,
        emotion_pattern=None,
        cognition_beliefs=None,
        relationship_manipulations=None,
        goals=None,
        therapy_principles=None,
        connected_at=now,  # Already connected
        created_at=now
    )
    db.create_ai_mind(new_mind.model_dump())

    # Update avatar client count
    avatar.client_count += 1
    db.create_avatar(avatar.model_dump())

    # Get therapist info
    therapist_data = db.get_user_by_id(avatar.therapist_id)

    # Build response
    connected_avatar = ConnectedAvatarDetail(
        id=avatar.id,
        avatar_name=avatar.name,
        pro_name=therapist_data["full_name"] if therapist_data else "Therapist",
        specialty=avatar.specialty,
        therapeutic_approaches=avatar.therapeutic_approaches,
        about=avatar.about,
        avatar_picture=None,
        last_chat_time=connection.last_chat_time
    )

    return ConnectAvatarResponse(avatar=connected_avatar)

# ============================================================
# AI MIND ENDPOINTS
# ============================================================

class MindSection(str, Enum):
    PERSONALITY = "personality"
    EMOTION_PATTERN = "emotion_pattern"
    COGNITION_BELIEFS = "cognition_beliefs"
    RELATIONSHIP = "relationship"

class SupervisionFeedbackRequest(BaseModel):
    section: MindSection
    feedback: str

class SupervisionFeedbackResponse(BaseModel):
    success: bool
    message: str

# In-memory storage for supervision feedback
supervision_feedback_db: dict[str, list[dict]] = {}  # key: mind_id -> list of feedbacks

class AIMindByUserAvatarResponse(BaseModel):
    """Response for GET /api/mind/{user_id}/{avatar_id}"""
    id: str
    name: str
    sex: Optional[str] = None
    age: Optional[int] = None
    avatar_id: str
    avatar_name: Optional[str] = None
    personality: Optional[PersonalityInput] = None
    emotion_pattern: Optional[EmotionPatternInput] = None
    cognition_beliefs: Optional[CognitionBeliefsInput] = None
    relationship_manipulations: Optional[RelationshipInput] = None
    goals: Optional[str] = None
    therapy_principles: Optional[str] = None
    sessions: int = 0
    avg_time: int = 0

@app.get("/api/mind/{user_id}/{avatar_id}", response_model=AIMindByUserAvatarResponse, tags=["AI Mind"])
async def get_user_ai_mind(user_id: str, avatar_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get AI Mind by user_id and avatar_id pair"""
    # Find AI Mind by user_id and avatar_id
    mind_data = db.get_ai_mind_by_user_avatar(user_id, avatar_id)

    if not mind_data:
        raise HTTPException(status_code=404, detail="AI Mind not found for this user and avatar pair")

    # Get avatar name
    avatar_data = db.get_avatar_by_id(avatar_id)

    return AIMindByUserAvatarResponse(
        id=mind_data["id"],
        name=mind_data["name"],
        sex=mind_data.get("sex"),
        age=mind_data.get("age"),
        avatar_id=mind_data["avatar_id"],
        avatar_name=avatar_data["name"] if avatar_data else None,
        personality=mind_data.get("personality"),
        emotion_pattern=mind_data.get("emotion_pattern"),
        cognition_beliefs=mind_data.get("cognition_beliefs"),
        relationship_manipulations=mind_data.get("relationship_manipulations"),
        goals=mind_data.get("goals"),
        therapy_principles=mind_data.get("therapy_principles"),
        sessions=mind_data.get("sessions", 0),
        avg_time=mind_data.get("avg_time", 0)
    )

@app.post("/api/mind/{mind_id}/supervise", response_model=SupervisionFeedbackResponse, tags=["AI Mind"])
async def submit_supervision_feedback(
    mind_id: str,
    request: SupervisionFeedbackRequest,
    current_user: UserInDB = Depends(get_current_pro)
):
    """Submit supervision feedback for a client's AI Mind profile (Pro only)"""
    # Find the AI Mind by mind_id
    mind_data = db.get_ai_mind_by_id(mind_id)
    if not mind_data:
        raise HTTPException(status_code=404, detail="AI Mind not found")

    # Verify the avatar belongs to current pro
    avatar_data = db.get_avatar_by_id(mind_data["avatar_id"])
    if not avatar_data:
        raise HTTPException(status_code=404, detail="Avatar not found")
    if avatar_data["therapist_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to supervise this avatar")

    # Store the feedback using mind_id as key (still in-memory for now)
    cache_key = mind_id
    if cache_key not in supervision_feedback_db:
        supervision_feedback_db[cache_key] = []

    supervision_feedback_db[cache_key].append({
        "id": str(uuid.uuid4()),
        "section": request.section.value,
        "feedback": request.feedback,
        "pro_id": current_user.id,
        "pro_name": current_user.full_name,
        "created_at": datetime.now().isoformat()
    })

    return SupervisionFeedbackResponse(
        success=True,
        message="Supervision feedback received"
    )

# ============================================================
# FEEDBACK ENDPOINTS (Client only)
# ============================================================

@app.post("/api/feedback/session", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_session_feedback(feedback: SessionFeedback, current_user: UserInDB = Depends(get_current_client)):
    """Submit session feedback (client only)"""
    feedback_id = str(uuid.uuid4())
    feedback_storage.append({
        "id": feedback_id,
        "user_id": current_user.id,
        **feedback.model_dump(),
        "timestamp": datetime.now()
    })
    return FeedbackResponse(success=True, message="Feedback recorded", feedback_id=feedback_id)

@app.get("/api/feedback/{user_id}", tags=["Feedback"])
async def get_user_feedback(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get feedback history for a user"""
    return [f for f in feedback_storage if f.get("user_id") == user_id]

# ============================================================
# PORTAL ENDPOINTS (Admin/Analytics)
# ============================================================

class PortalStatsResponse(BaseModel):
    total_pros: int
    total_clients: int
    total_avatars: int
    total_sessions: int
    active_invitations: int

class ProUserStats(BaseModel):
    id: str
    email: str
    full_name: str
    profession: Optional[str] = None
    created_at: datetime
    avatar_count: int
    client_count: int
    total_sessions: int
    is_active: bool

class ProUserDetail(BaseModel):
    id: str
    email: str
    full_name: str
    profession: Optional[str] = None
    license_number: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)
    created_at: datetime
    is_active: bool
    avatars: list[AvatarResponse] = Field(default_factory=list)
    clients: list[AIMindResponse] = Field(default_factory=list)  # Changed to AIMindResponse

@app.get("/api/portal/stats", response_model=PortalStatsResponse, tags=["Portal"])
async def get_portal_stats():
    """Get overall platform statistics"""
    all_users = db.get_all_users()
    total_pros = sum(1 for u in all_users if u.get("role") == UserRole.THERAPIST)
    total_clients = sum(1 for u in all_users if u.get("role") == UserRole.CLIENT)

    all_avatars = db.get_all_avatars()
    total_avatars = len(all_avatars)

    # For sessions, we'd need to scan all AI minds or sessions (expensive)
    # For now, return 0 or implement later
    total_sessions = 0

    all_invitations = db.get_all_invitations()
    active_invitations = sum(1 for inv in all_invitations
                           if not inv.get("is_used", False)
                           and datetime.fromisoformat(inv["expires_at"]) > datetime.now())

    return PortalStatsResponse(
        total_pros=total_pros,
        total_clients=total_clients,
        total_avatars=total_avatars,
        total_sessions=total_sessions,
        active_invitations=active_invitations
    )

@app.get("/api/portal/pro-users", response_model=list[ProUserStats], tags=["Portal"])
async def get_portal_pro_users():
    """Get all Pro users with their statistics"""
    result = []
    all_users = db.get_all_users()

    for user_data in all_users:
        if user_data.get("role") == UserRole.THERAPIST:
            avatars = db.get_avatars_by_pro(user_data["id"])
            avatar_count = len(avatars)

            minds = db.get_ai_minds_by_therapist(user_data["id"])
            client_count = len(minds)

            # For sessions, would need to scan - set to 0 for now
            total_sessions = 0

            result.append(ProUserStats(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                profession=user_data.get("profession"),
                created_at=datetime.fromisoformat(user_data["created_at"]),
                avatar_count=avatar_count,
                client_count=client_count,
                total_sessions=total_sessions,
                is_active=user_data.get("is_active", True)
            ))
    return result

@app.get("/api/portal/pro-users/{pro_id}/details", response_model=ProUserDetail, tags=["Portal"])
async def get_portal_pro_user_details(pro_id: str):
    """Get Pro user details with avatars and clients (AI Minds)"""
    user_data = db.get_user_by_id(pro_id)
    if not user_data or user_data.get("role") != UserRole.THERAPIST:
        raise HTTPException(status_code=404, detail="Pro user not found")

    # Get all avatars for this pro
    avatars = db.get_avatars_by_pro(pro_id)
    user_avatars = [AvatarResponse(**a) for a in avatars]

    # Get all AI Minds (clients) for this pro - same logic as /api/clients
    user_clients = []
    minds = db.get_ai_minds_by_therapist(pro_id)

    for mind_data in minds:
        avatar_data = db.get_avatar_by_id(mind_data["avatar_id"])

        # Find invitation code if not connected
        invitation_code = None
        if mind_data.get("connected_at") is None:
            invitation_code = find_invitation_by_mind_id(mind_data["id"], pro_id)

        user_clients.append(AIMindResponse(
            **mind_data,
            avatar_name=avatar_data["name"] if avatar_data else None,
            invitation_code=invitation_code
        ))

    return ProUserDetail(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        profession=user_data.get("profession"),
        license_number=user_data.get("license_number"),
        specializations=user_data.get("specializations", []),
        created_at=datetime.fromisoformat(user_data["created_at"]),
        is_active=user_data.get("is_active", True),
        avatars=user_avatars,
        clients=user_clients
    )

# ============================================================
# PSVS ENDPOINTS
# ============================================================

# Import PSVS modules
from psvs.calculator import (
    calculate_initial_psvs_position,
    calculate_psvs_update,
)
from psvs.prompt_generator import generate_system_prompt
from psvs.gemini_service import (
    generate_response,
    analyze_message_for_stress,
    should_skip_psvs_update,
)

@app.post("/api/mind/{mind_id}/psvs/initialize", response_model=PSVSProfileResponse, tags=["PSVS"])
async def initialize_psvs_profile(mind_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Initialize PSVS profile for an AI Mind.

    This is automatically called when creating an AI Mind, but can be called manually if needed.
    """
    # Get AI Mind
    mind_data = db.get_ai_mind_by_id(mind_id)
    if not mind_data:
        raise HTTPException(status_code=404, detail="AI Mind not found")

    # Check if PSVS profile already exists
    existing_profile_data = db.get_psvs_profile(mind_id)
    if existing_profile_data:
        return PSVSProfileResponse(
            id=existing_profile_data["id"],
            mind_id=existing_profile_data["mind_id"],
            current_position=PSVSCoordinates(**existing_profile_data["current_position"]),
            recent_trajectory=[PSVSCoordinates(**c) for c in existing_profile_data["trajectory_history"][-10:]],
            created_at=datetime.fromisoformat(existing_profile_data["created_at"]),
            updated_at=datetime.fromisoformat(existing_profile_data["updated_at"])
        )

    # Calculate initial PSVS position from AI Mind data
    ai_mind_dict = {
        "personality": mind_data.get("personality", {}),
        "emotion_pattern": mind_data.get("emotion_pattern", {}),
        "cognition_beliefs": mind_data.get("cognition_beliefs", {}),
        "relationship_manipulations": mind_data.get("relationship_manipulations", {}),
    }

    initial_coords = calculate_initial_psvs_position(ai_mind_dict)

    # Create PSVS profile
    psvs_id = str(uuid.uuid4())
    psvs_profile = PSVSProfile(
        id=psvs_id,
        mind_id=mind_id,
        current_position=PSVSCoordinates(**initial_coords),
        trajectory_history=[PSVSCoordinates(**initial_coords)],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.create_psvs_profile(psvs_profile.model_dump())

    return PSVSProfileResponse(
        id=psvs_profile.id,
        mind_id=psvs_profile.mind_id,
        current_position=psvs_profile.current_position,
        recent_trajectory=psvs_profile.trajectory_history[-10:],
        created_at=psvs_profile.created_at,
        updated_at=psvs_profile.updated_at
    )


@app.get("/api/mind/{mind_id}/psvs", response_model=PSVSProfileResponse, tags=["PSVS"])
async def get_psvs_profile(mind_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get current PSVS profile for an AI Mind."""
    psvs_profile_data = db.get_psvs_profile(mind_id)
    if not psvs_profile_data:
        raise HTTPException(status_code=404, detail="PSVS profile not found. Initialize it first.")

    return PSVSProfileResponse(
        id=psvs_profile_data["id"],
        mind_id=psvs_profile_data["mind_id"],
        current_position=PSVSCoordinates(**psvs_profile_data["current_position"]),
        recent_trajectory=[PSVSCoordinates(**c) for c in psvs_profile_data["trajectory_history"][-10:]],
        created_at=datetime.fromisoformat(psvs_profile_data["created_at"]),
        updated_at=datetime.fromisoformat(psvs_profile_data["updated_at"])
    )


@app.get("/api/mind/{mind_id}/psvs/trajectory", response_model=list[PSVSCoordinates], tags=["PSVS"])
async def get_psvs_trajectory(mind_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get full PSVS trajectory history for an AI Mind."""
    psvs_profile_data = db.get_psvs_profile(mind_id)
    if not psvs_profile_data:
        raise HTTPException(status_code=404, detail="PSVS profile not found")

    return [PSVSCoordinates(**c) for c in psvs_profile_data["trajectory_history"]]


@app.post("/api/session/start", response_model=SessionStartResponse, tags=["PSVS"])
async def start_conversation_session(
    mind_id: str,
    avatar_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Start a new conversation session."""
    # Verify AI Mind exists
    mind_data = db.get_ai_mind_by_id(mind_id)
    if not mind_data:
        raise HTTPException(status_code=404, detail="AI Mind not found")

    # Verify avatar exists
    avatar_data = db.get_avatar_by_id(avatar_id)
    if not avatar_data:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Get or create PSVS profile
    psvs_profile_data = db.get_psvs_profile(mind_id)
    if not psvs_profile_data:
        # Auto-initialize PSVS profile
        ai_mind_dict = {
            "personality": mind_data.get("personality", {}),
            "emotion_pattern": mind_data.get("emotion_pattern", {}),
            "cognition_beliefs": mind_data.get("cognition_beliefs", {}),
            "relationship_manipulations": mind_data.get("relationship_manipulations", {}),
        }
        initial_coords = calculate_initial_psvs_position(ai_mind_dict)
        psvs_id = str(uuid.uuid4())
        psvs_profile = PSVSProfile(
            id=psvs_id,
            mind_id=mind_id,
            current_position=PSVSCoordinates(**initial_coords),
            trajectory_history=[PSVSCoordinates(**initial_coords)],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.create_psvs_profile(psvs_profile.model_dump())
        current_position = psvs_profile.current_position
    else:
        current_position = PSVSCoordinates(**psvs_profile_data["current_position"])

    # Create session
    session_id = str(uuid.uuid4())
    session = ConversationSession(
        id=session_id,
        mind_id=mind_id,
        avatar_id=avatar_id,
        user_id=current_user.id,
        started_at=datetime.now(),
        message_count=0,
        is_active=True
    )

    db.create_session(session.model_dump())

    return SessionStartResponse(
        session_id=session_id,
        mind_id=mind_id,
        avatar_id=avatar_id,
        initial_psvs_position=current_position
    )


@app.post("/api/session/{session_id}/message", response_model=MessageResponse, tags=["PSVS"])
async def send_message(
    session_id: str,
    message: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Send a message and get AI response (MAIN CONVERSATION ENDPOINT).

    Flow:
    1. Analyze user message for PSVS indicators
    2. Update PSVS position (if message is substantial)
    3. Generate dynamic prompts (policy/value/search)
    4. Call Gemini API
    5. Store message + response
    6. Update trajectory
    7. Return response + PSVS position
    """
    # Get session
    session_data = db.get_session_by_id(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session_data.get("is_active", False):
        raise HTTPException(status_code=400, detail="Session has ended")

    # Get AI Mind and Avatar
    mind_data = db.get_ai_mind_by_id(session_data["mind_id"])
    avatar_data = db.get_avatar_by_id(session_data["avatar_id"])

    if not mind_data or not avatar_data:
        raise HTTPException(status_code=404, detail="Mind or Avatar not found")

    # Get PSVS profile
    psvs_profile_data = db.get_psvs_profile(session_data["mind_id"])
    if not psvs_profile_data:
        raise HTTPException(status_code=404, detail="PSVS profile not found")

    # Reconstruct PSVS profile object for manipulation
    psvs_profile = PSVSProfile(**psvs_profile_data)

    # Check if we should skip PSVS update for very short messages
    skip_update = should_skip_psvs_update(message)

    # Analyze message for stress indicators (if not skipping)
    if not skip_update:
        stress_indicators = analyze_message_for_stress(message)

        # Update PSVS position
        current_position_dict = psvs_profile.current_position.model_dump()
        updated_coords = calculate_psvs_update(
            current_position_dict,
            stress_indicators,
            message
        )

        # Update profile
        new_position = PSVSCoordinates(**updated_coords)
        psvs_profile.current_position = new_position

        # Add to trajectory (keep last 50)
        psvs_profile.trajectory_history.append(new_position)
        if len(psvs_profile.trajectory_history) > 50:
            psvs_profile.trajectory_history = psvs_profile.trajectory_history[-50:]

        psvs_profile.updated_at = datetime.now()

        # Save updated PSVS profile
        db.update_psvs_profile(session_data["mind_id"], psvs_profile.model_dump())

    # Generate system prompt with current PSVS position
    avatar_dict = {
        "name": avatar_data["name"],
        "specialty": avatar_data["specialty"],
        "therapeutic_approaches": avatar_data["therapeutic_approaches"],
        "about": avatar_data["about"],
    }

    ai_mind_dict = {
        "name": mind_data["name"],
        "goals": mind_data.get("goals"),
        "therapy_principles": mind_data.get("therapy_principles"),
    }

    psvs_position_dict = psvs_profile.current_position.model_dump()

    system_prompt = generate_system_prompt(avatar_dict, ai_mind_dict, psvs_position_dict)

    # Get conversation history
    messages = db.get_messages_by_session(session_id)
    conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    # Generate response using Gemini
    response_text = generate_response(system_prompt, message, conversation_history)

    # Store user message
    user_msg_id = str(uuid.uuid4())
    user_message = ConversationMessage(
        id=user_msg_id,
        session_id=session_id,
        mind_id=session_data["mind_id"],
        role="user",
        content=message,
        psvs_snapshot=psvs_profile.current_position,
        timestamp=datetime.now()
    )
    db.create_message(user_message.model_dump())

    # Store assistant response
    assistant_msg_id = str(uuid.uuid4())
    assistant_message = ConversationMessage(
        id=assistant_msg_id,
        session_id=session_id,
        mind_id=session_data["mind_id"],
        role="assistant",
        content=response_text,
        psvs_snapshot=psvs_profile.current_position,
        timestamp=datetime.now()
    )
    db.create_message(assistant_message.model_dump())

    # Update session
    session_data["message_count"] = session_data.get("message_count", 0) + 2
    db.update_session(session_id, session_data)

    return MessageResponse(
        message_id=assistant_msg_id,
        response=response_text,
        psvs_position=psvs_profile.current_position,
        session_id=session_id
    )


@app.get("/api/session/{session_id}/messages", response_model=list[ConversationMessage], tags=["PSVS"])
async def get_session_messages(session_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get all messages in a conversation session."""
    session_data = db.get_session_by_id(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all messages for this session (already sorted by timestamp in db method)
    messages_data = db.get_messages_by_session(session_id)

    # Convert to Pydantic models
    messages = [ConversationMessage(**msg_data) for msg_data in messages_data]

    return messages


@app.post("/api/session/{session_id}/end", tags=["PSVS"])
async def end_conversation_session(session_id: str, current_user: UserInDB = Depends(get_current_user)):
    """End a conversation session."""
    session_data = db.get_session_by_id(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data["is_active"] = False
    session_data["ended_at"] = datetime.now().isoformat()

    db.update_session(session_id, session_data)

    return {"success": True, "message": "Session ended", "session_id": session_id}

# For Vercel deployment
app = app