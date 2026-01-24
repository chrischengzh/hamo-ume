"""
Hamo-UME: Hamo Unified Mind Engine
Backend API Server with JWT Authentication

Tech Stack: Python + FastAPI + JWT
Version: 0.2.0
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
import os

# JWT dependencies
from jose import JWTError, jwt
from passlib.context import CryptContext

# ============================================================
# CONFIGURATION
# ============================================================

# JWT Settings - In production, use environment variables!
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hamo-ume-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
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

# ============================================================
# USER MODELS
# ============================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class TherapistCreate(UserBase):
    password: str
    profession: str
    license_number: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)

class ClientCreate(UserBase):
    password: str
    therapist_id: Optional[str] = None  # Linked therapist
    invitation_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: str
    role: UserRole
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    # Therapist specific
    profession: Optional[str] = None
    license_number: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)
    # Client specific
    therapist_id: Optional[str] = None

class UserResponse(UserBase):
    id: str
    role: UserRole
    created_at: datetime
    is_active: bool
    profession: Optional[str] = None
    specializations: list[str] = Field(default_factory=list)
    therapist_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: str
    email: str
    role: UserRole

# ============================================================
# AI MIND MODELS (from previous version)
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
    user_id: str
    avatar_id: str
    personality: PersonalityCharacteristics
    emotion_pattern: EmotionPattern
    cognition_beliefs: CognitionBeliefs
    relationship_manipulations: RelationshipManipulations
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(ge=0, le=1)

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ConversationMessage(BaseModel):
    sender: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class TrainingRequest(BaseModel):
    user_id: str
    avatar_id: str
    session_id: str
    conversation: list[ConversationMessage]
    session_notes: Optional[str] = None

class TrainingResponse(BaseModel):
    success: bool
    message: str
    training_id: str
    estimated_completion: datetime

class SessionFeedback(BaseModel):
    user_id: str
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
    timestamp: datetime = Field(default_factory=datetime.now)

class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str

# ============================================================
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================================

users_db: dict[str, UserInDB] = {}
mind_cache: dict[str, UserAIMind] = {}
feedback_storage: list[SessionFeedback] = []
training_queue: list[TrainingRequest] = []
invitation_codes: dict[str, str] = {}  # code -> therapist_id

# ============================================================
# AUTH UTILITIES
# ============================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return TokenData(user_id=user_id, email=email, role=UserRole(role))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    token = credentials.credentials
    token_data = decode_token(token)
    user = users_db.get(token_data.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")
    return user

async def get_current_therapist(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != UserRole.THERAPIST:
        raise HTTPException(status_code=403, detail="Therapist access required")
    return current_user

async def get_current_client(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Client access required")
    return current_user

def generate_invitation_code(therapist_id: str) -> str:
    code = str(uuid.uuid4())[:8].upper()
    invitation_codes[code] = therapist_id
    return code

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
    description="Hamo Unified Mind Engine - Backend API with JWT Authentication",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/api/v1/auth/register/therapist", response_model=Token, tags=["Authentication"])
async def register_therapist(user_data: TherapistCreate):
    """Register a new therapist account"""
    # Check if email exists
    for u in users_db.values():
        if u.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    new_user = UserInDB(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        role=UserRole.THERAPIST,
        hashed_password=hashed_password,
        profession=user_data.profession,
        license_number=user_data.license_number,
        specializations=user_data.specializations
    )
    users_db[user_id] = new_user
    
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email, "role": UserRole.THERAPIST}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(**new_user.model_dump())
    )

@app.post("/api/v1/auth/register/client", response_model=Token, tags=["Authentication"])
async def register_client(user_data: ClientCreate):
    """Register a new client account (requires invitation code)"""
    # Check if email exists
    for u in users_db.values():
        if u.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate invitation code if provided
    therapist_id = None
    if user_data.invitation_code:
        therapist_id = invitation_codes.get(user_data.invitation_code)
        if not therapist_id:
            raise HTTPException(status_code=400, detail="Invalid invitation code")
    
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    new_user = UserInDB(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        role=UserRole.CLIENT,
        hashed_password=hashed_password,
        therapist_id=therapist_id or user_data.therapist_id
    )
    users_db[user_id] = new_user
    
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email, "role": UserRole.CLIENT}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(**new_user.model_dump())
    )

@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(credentials: UserLogin):
    """Login with email and password"""
    user = None
    for u in users_db.values():
        if u.email == credentials.email:
            user = u
            break
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(**user.model_dump())
    )

@app.get("/api/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """Get current authenticated user info"""
    return UserResponse(**current_user.model_dump())

@app.post("/api/v1/auth/invitation-code", tags=["Authentication"])
async def create_invitation_code(current_user: UserInDB = Depends(get_current_therapist)):
    """Generate an invitation code for clients (therapist only)"""
    code = generate_invitation_code(current_user.id)
    return {"invitation_code": code, "therapist_id": current_user.id}

# ============================================================
# PROTECTED API ENDPOINTS
# ============================================================

@app.get("/", tags=["Health"])
async def root():
    return {"service": "Hamo-UME", "version": "0.2.0", "status": "running", "auth": "JWT enabled"}

@app.get("/api/v1/mind/{user_id}/{avatar_id}", response_model=UserAIMind, tags=["AI Mind"])
async def get_user_ai_mind(user_id: str, avatar_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get User's AI Mind Profile (requires authentication)"""
    cache_key = f"{user_id}_{avatar_id}"
    if cache_key in mind_cache:
        return mind_cache[cache_key]
    user_mind = MockDataGenerator.generate_user_ai_mind(user_id, avatar_id)
    mind_cache[cache_key] = user_mind
    return user_mind

@app.post("/api/v1/mind/train", response_model=TrainingResponse, tags=["AI Mind"])
async def submit_training_request(request: TrainingRequest, current_user: UserInDB = Depends(get_current_therapist)):
    """Submit conversation for AI Mind training (therapist only)"""
    if not request.conversation:
        raise HTTPException(status_code=400, detail="Conversation cannot be empty")
    training_queue.append(request)
    training_id = str(uuid.uuid4())
    return TrainingResponse(
        success=True,
        message=f"Training request queued. Processing {len(request.conversation)} messages.",
        training_id=training_id,
        estimated_completion=datetime.now()
    )

@app.post("/api/v1/feedback/session", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_session_feedback(feedback: SessionFeedback, current_user: UserInDB = Depends(get_current_client)):
    """Submit session feedback (client only)"""
    feedback_storage.append(feedback)
    feedback_id = str(uuid.uuid4())
    return FeedbackResponse(success=True, message="Feedback recorded", feedback_id=feedback_id)

@app.get("/api/v1/feedback/{user_id}", response_model=list[SessionFeedback], tags=["Feedback"])
async def get_user_feedback_history(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get feedback history for a user"""
    return [f for f in feedback_storage if f.user_id == user_id]

@app.get("/api/v1/therapist/clients", tags=["Therapist"])
async def get_therapist_clients(current_user: UserInDB = Depends(get_current_therapist)):
    """Get all clients linked to current therapist"""
    clients = [UserResponse(**u.model_dump()) for u in users_db.values() 
               if u.role == UserRole.CLIENT and u.therapist_id == current_user.id]
    return {"clients": clients, "count": len(clients)}

# For Vercel deployment
app = app
