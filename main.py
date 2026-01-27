"""
Hamo-UME: Hamo Unified Mind Engine
Backend API Server with JWT Authentication

Tech Stack: Python + FastAPI + JWT
Version: 1.2.6
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
    id: str
    name: str
    therapist_name: Optional[str] = None

class ClientTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: ClientResponse
    connected_avatar: Optional[ConnectedAvatar] = None

# ============================================================
# AVATAR MODELS
# ============================================================

class AvatarCreate(BaseModel):
    name: str
    theory: str
    methodology: Optional[str] = None
    principles: Optional[str] = None
    description: Optional[str] = None

class AvatarInDB(BaseModel):
    id: str
    therapist_id: str
    name: str
    theory: str
    methodology: Optional[str] = None
    principles: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    client_count: int = 0

class AvatarResponse(AvatarInDB):
    pass

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

# ============================================================
# INVITATION MODELS
# ============================================================

class InvitationCreate(BaseModel):
    client_id: str
    avatar_id: str

class InvitationInDB(BaseModel):
    code: str
    therapist_id: str
    client_id: str
    avatar_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    is_used: bool = False

class InvitationResponse(BaseModel):
    code: str
    client_id: str
    avatar_id: str
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
    user_id: str
    avatar_id: str
    personality: PersonalityCharacteristics
    emotion_pattern: EmotionPattern
    cognition_beliefs: CognitionBeliefs
    relationship_manipulations: RelationshipManipulations
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(ge=0, le=1)

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
# IN-MEMORY STORAGE
# ============================================================

users_db: dict[str, UserInDB] = {}
avatars_db: dict[str, AvatarInDB] = {}
client_profiles_db: dict[str, ClientProfileInDB] = {}
invitations_db: dict[str, InvitationInDB] = {}
mind_cache: dict[str, UserAIMind] = {}
feedback_storage: list[dict] = []
pro_refresh_tokens_db: dict[str, str] = {}  # refresh_token -> user_id
client_refresh_tokens_db: dict[str, str] = {}  # refresh_token -> user_id

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
    if role == UserRole.THERAPIST:
        pro_refresh_tokens_db[token] = user_id
    else:
        client_refresh_tokens_db[token] = user_id
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
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
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
    description="Hamo Unified Mind Engine - Backend API v1.2.6",
    version="1.2.6"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # 本地开发
        "http://localhost:3000",           # 本地开发备用端口
        "https://hamo-pro.vercel.app",     # Vercel 生产环境 - Pro
        "https://hamo-client.vercel.app",  # Vercel 生产环境 - Client
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
    return {"service": "Hamo-UME", "version": "1.2.6", "status": "running"}

# ============================================================
# PRO (THERAPIST) AUTH ENDPOINTS
# ============================================================

@app.post("/api/auth/registerPro", response_model=ProTokenResponse, tags=["Auth - Pro"])
async def register_pro(user_data: ProRegister):
    """Register a new Pro (Therapist) account"""
    for u in users_db.values():
        if u.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
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
    users_db[user_id] = new_user
    
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
    user = None
    for u in users_db.values():
        if u.email == credentials.email and u.role == UserRole.THERAPIST:
            user = u
            break
    
    if not user or not verify_password(credentials.password, user.hashed_password):
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
    if request.refresh_token not in pro_refresh_tokens_db:
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    
    user = users_db.get(user_id)
    if not user or user.role != UserRole.THERAPIST:
        raise HTTPException(status_code=401, detail="Pro user not found")
    
    del pro_refresh_tokens_db[request.refresh_token]
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
    for u in users_db.values():
        if u.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate invitation code
    invitation = invitations_db.get(user_data.invitation_code)
    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid invitation code")
    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if invitation.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")
    
    user_id = str(uuid.uuid4())
    new_user = UserInDB(
        id=user_id,
        email=user_data.email,
        full_name=user_data.nickname,  # Use nickname from client frontend
        role=UserRole.CLIENT,
        hashed_password=hash_password(user_data.password),
        therapist_id=invitation.therapist_id,
        avatar_id=invitation.avatar_id,
        client_profile_id=invitation.client_id
    )
    users_db[user_id] = new_user
    
    # Mark invitation as used & link user to client profile
    invitation.is_used = True
    client_profile = client_profiles_db.get(invitation.client_id)
    if client_profile:
        client_profile.user_id = user_id

    # Get connected avatar info
    avatar = avatars_db.get(invitation.avatar_id)
    therapist = users_db.get(invitation.therapist_id)
    connected_avatar = None
    if avatar:
        connected_avatar = ConnectedAvatar(
            id=avatar.id,
            name=avatar.name,
            therapist_name=therapist.full_name if therapist else None
        )

    access_token = create_access_token({"sub": user_id, "email": user_data.email, "role": UserRole.CLIENT})
    refresh_token = create_refresh_token(user_id, UserRole.CLIENT)

    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ClientResponse(**new_user.model_dump()),
        connected_avatar=connected_avatar
    )

@app.post("/api/auth/loginClient", response_model=ClientTokenResponse, tags=["Auth - Client"])
async def login_client(credentials: ClientLogin):
    """Login as Client"""
    user = None
    for u in users_db.values():
        if u.email == credentials.email and u.role == UserRole.CLIENT:
            user = u
            break
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account inactive")
    
    access_token = create_access_token({"sub": user.id, "email": user.email, "role": UserRole.CLIENT})
    refresh_token = create_refresh_token(user.id, UserRole.CLIENT)
    
    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ClientResponse(**user.model_dump())
    )

@app.post("/api/auth/refreshClient", response_model=ClientTokenResponse, tags=["Auth - Client"])
async def refresh_client_token(request: ClientRefreshRequest):
    """Refresh Client access token"""
    payload = decode_token(request.refresh_token)
    
    if payload.get("type") != "refresh" or payload.get("role") != UserRole.CLIENT:
        raise HTTPException(status_code=401, detail="Invalid Client refresh token")
    
    user_id = payload.get("sub")
    if request.refresh_token not in client_refresh_tokens_db:
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    
    user = users_db.get(user_id)
    if not user or user.role != UserRole.CLIENT:
        raise HTTPException(status_code=401, detail="Client user not found")
    
    del client_refresh_tokens_db[request.refresh_token]
    access_token = create_access_token({"sub": user.id, "email": user.email, "role": UserRole.CLIENT})
    new_refresh_token = create_refresh_token(user.id, UserRole.CLIENT)
    
    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=ClientResponse(**user.model_dump())
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
    return [AvatarResponse(**a.model_dump()) for a in avatars_db.values() if a.therapist_id == current_user.id]

@app.post("/api/avatars", response_model=AvatarResponse, tags=["Avatars"])
async def create_avatar(avatar_data: AvatarCreate, current_user: UserInDB = Depends(get_current_pro)):
    """Create a new avatar"""
    avatar_id = str(uuid.uuid4())
    new_avatar = AvatarInDB(
        id=avatar_id,
        therapist_id=current_user.id,
        name=avatar_data.name,
        theory=avatar_data.theory,
        methodology=avatar_data.methodology,
        principles=avatar_data.principles,
        description=avatar_data.description
    )
    avatars_db[avatar_id] = new_avatar
    return AvatarResponse(**new_avatar.model_dump())

@app.get("/api/avatars/{avatar_id}", response_model=AvatarResponse, tags=["Avatars"])
async def get_avatar(avatar_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get avatar by ID"""
    avatar = avatars_db.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return AvatarResponse(**avatar.model_dump())

# ============================================================
# CLIENT PROFILE ENDPOINTS (Pro only)
# ============================================================

@app.get("/api/clients", response_model=list[ClientProfileResponse], tags=["Clients"])
async def get_clients(current_user: UserInDB = Depends(get_current_pro)):
    """Get all client profiles for current Pro"""
    result = []
    for c in client_profiles_db.values():
        if c.therapist_id == current_user.id:
            avatar = avatars_db.get(c.avatar_id)
            result.append(ClientProfileResponse(**c.model_dump(), avatar_name=avatar.name if avatar else None))
    return result

@app.post("/api/clients", response_model=ClientProfileResponse, tags=["Clients"])
async def create_client(client_data: ClientProfileCreate, current_user: UserInDB = Depends(get_current_pro)):
    """Create a new client profile"""
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

@app.get("/api/clients/{client_id}", response_model=ClientProfileResponse, tags=["Clients"])
async def get_client(client_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get client profile by ID"""
    client = client_profiles_db.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    avatar = avatars_db.get(client.avatar_id)
    return ClientProfileResponse(**client.model_dump(), avatar_name=avatar.name if avatar else None)

# ============================================================
# INVITATION ENDPOINTS (Pro only)
# ============================================================

class ProInvitationGenerateRequest(BaseModel):
    avatar_id: str

class ProInvitationGenerateResponse(BaseModel):
    invitation_code: str
    expires_at: datetime

@app.post("/api/pro/invitation/generate", response_model=ProInvitationGenerateResponse, tags=["Invitations"])
async def generate_pro_invitation(invite_data: ProInvitationGenerateRequest, current_user: UserInDB = Depends(get_current_pro)):
    """Generate an invitation code for a client (Pro endpoint for hamo-pro frontend)"""
    avatar = avatars_db.get(invite_data.avatar_id)
    if not avatar or avatar.therapist_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid avatar ID")

    code = f"HAMO-{str(uuid.uuid4())[:6].upper()}"
    expires_at = datetime.now() + timedelta(days=7)

    invitation = InvitationInDB(
        code=code,
        therapist_id=current_user.id,
        client_id="",  # Client ID will be assigned when client registers
        avatar_id=invite_data.avatar_id,
        expires_at=expires_at
    )
    invitations_db[code] = invitation

    return ProInvitationGenerateResponse(
        invitation_code=code,
        expires_at=expires_at
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
    invitation = invitations_db.get(code)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if invitation.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")

    avatar = avatars_db.get(invitation.avatar_id)
    therapist = users_db.get(invitation.therapist_id)

    return {
        "valid": True,
        "avatar_name": avatar.name if avatar else None,
        "therapist_name": therapist.full_name if therapist else None,
        "expires_at": invitation.expires_at
    }

# ============================================================
# CLIENT INVITATION ENDPOINTS
# ============================================================

class ClientInvitationValidateRequest(BaseModel):
    invitation_code: str

@app.post("/api/client/invitation/validate", tags=["Invitations"])
async def validate_client_invitation(request: ClientInvitationValidateRequest):
    """Validate an invitation code (for hamo-client frontend)"""
    invitation = invitations_db.get(request.invitation_code)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation code")
    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation code already used")
    if invitation.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="Invitation code expired")

    avatar = avatars_db.get(invitation.avatar_id)
    therapist = users_db.get(invitation.therapist_id)

    return {
        "valid": True,
        "pro_avatar": {
            "id": avatar.id if avatar else None,
            "name": avatar.name if avatar else None,
            "therapist_name": therapist.full_name if therapist else None
        }
    }

# ============================================================
# AI MIND ENDPOINTS
# ============================================================

@app.get("/api/mind/{user_id}/{avatar_id}", response_model=UserAIMind, tags=["AI Mind"])
async def get_user_ai_mind(user_id: str, avatar_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Get User's AI Mind Profile"""
    cache_key = f"{user_id}_{avatar_id}"
    if cache_key in mind_cache:
        return mind_cache[cache_key]
    user_mind = MockDataGenerator.generate_user_ai_mind(user_id, avatar_id)
    mind_cache[cache_key] = user_mind
    return user_mind

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

# For Vercel deployment
app = app