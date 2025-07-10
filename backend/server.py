from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import base64
from urllib.parse import urlparse
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="Live Streaming Platform", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    is_super_user: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_super_user: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Channel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    logo: Optional[str] = None  # Base64 encoded image
    urls: List[str] = []  # Multiple streaming URLs
    category: Optional[str] = None
    is_active: bool = True
    created_by: str  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChannelCreate(BaseModel):
    name: str
    description: str
    logo: Optional[str] = None
    urls: List[str] = []
    category: Optional[str] = None

class ChannelResponse(BaseModel):
    id: str
    name: str
    description: str
    logo: Optional[str]
    urls: List[str]
    category: Optional[str]
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(**user)

async def get_current_super_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_super_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def validate_m3u8_url(url: str) -> bool:
    return validate_url(url) and url.lower().endswith('.m3u8')

# Authentication Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        is_super_user=False
    )
    
    await db.users.insert_one(user.dict())
    return UserResponse(**user.dict())

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Channel Routes
@api_router.post("/channels", response_model=ChannelResponse)
async def create_channel(channel_data: ChannelCreate, current_user: User = Depends(get_current_user)):
    # Validate URLs
    for url in channel_data.urls:
        if not validate_url(url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL: {url}"
            )
    
    channel = Channel(
        name=channel_data.name,
        description=channel_data.description,
        logo=channel_data.logo,
        urls=channel_data.urls,
        category=channel_data.category,
        created_by=current_user.id
    )
    
    await db.channels.insert_one(channel.dict())
    return ChannelResponse(**channel.dict())

@api_router.get("/channels", response_model=List[ChannelResponse])
async def get_channels(category: Optional[str] = None, search: Optional[str] = None):
    query = {"is_active": True}
    
    if category:
        query["category"] = category
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    channels = await db.channels.find(query).sort("created_at", -1).to_list(1000)
    return [ChannelResponse(**channel) for channel in channels]

@api_router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str):
    channel = await db.channels.find_one({"id": channel_id, "is_active": True})
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    return ChannelResponse(**channel)

@api_router.put("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_user)
):
    # Find the channel
    channel = await db.channels.find_one({"id": channel_id, "is_active": True})
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Check if user owns the channel or is super user
    if channel["created_by"] != current_user.id and not current_user.is_super_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Validate URLs
    for url in channel_data.urls:
        if not validate_url(url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL: {url}"
            )
    
    # Update channel
    update_data = channel_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.channels.update_one(
        {"id": channel_id},
        {"$set": update_data}
    )
    
    updated_channel = await db.channels.find_one({"id": channel_id})
    return ChannelResponse(**updated_channel)

@api_router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    # Find the channel
    channel = await db.channels.find_one({"id": channel_id, "is_active": True})
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Check if user owns the channel or is super user
    if channel["created_by"] != current_user.id and not current_user.is_super_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Soft delete
    await db.channels.update_one(
        {"id": channel_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Channel deleted successfully"}

@api_router.get("/channels/{channel_id}/m3u8")
async def get_m3u8_download(
    channel_id: str,
    current_user: User = Depends(get_current_super_user)
):
    channel = await db.channels.find_one({"id": channel_id, "is_active": True})
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Filter M3U8 URLs
    m3u8_urls = [url for url in channel["urls"] if validate_m3u8_url(url)]
    
    if not m3u8_urls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No M3U8 URLs found for this channel"
        )
    
    return {"m3u8_urls": m3u8_urls}

@api_router.get("/my-channels", response_model=List[ChannelResponse])
async def get_my_channels(current_user: User = Depends(get_current_user)):
    channels = await db.channels.find({"created_by": current_user.id, "is_active": True}).sort("created_at", -1).to_list(1000)
    return [ChannelResponse(**channel) for channel in channels]

@api_router.get("/categories")
async def get_categories():
    categories = await db.channels.distinct("category", {"is_active": True, "category": {"$ne": None}})
    return {"categories": categories}

# Super User Routes
@api_router.post("/admin/users/{user_id}/make-super")
async def make_super_user(
    user_id: str,
    current_user: User = Depends(get_current_super_user)
):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_super_user": True, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "User promoted to super user"}

@api_router.get("/admin/channels", response_model=List[ChannelResponse])
async def get_all_channels_admin(current_user: User = Depends(get_current_super_user)):
    channels = await db.channels.find({"is_active": True}).sort("created_at", -1).to_list(1000)
    return [ChannelResponse(**channel) for channel in channels]

@api_router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users_admin(current_user: User = Depends(get_current_super_user)):
    users = await db.users.find({}).sort("created_at", -1).to_list(1000)
    return [UserResponse(**user) for user in users]

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Live Streaming Platform API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()