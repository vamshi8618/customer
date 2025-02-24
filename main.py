from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import jwt
import datetime
import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from router import user_router
from routers.order import order_router
from routers.tab_router import tab_router
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# FastAPI instance
app = FastAPI()

# MongoDB Connection
MONGO_URL = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client["kitchen_db"]
chef_collection = db["chefs"]

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Secret & Algorithm
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Token Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS Configuration
origins = [
    "http://localhost:8081",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from specified origins
    allow_credentials=True,  # Allows cookies to be sent along with requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Pydantic Models
class Chef(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Hash Password
def hash_password(password: str) -> str:
    logger.debug("Hashing password...")
    return pwd_context.hash(password)

# Verify Password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password...")
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT Token
def create_access_token(username: str):
    logger.debug(f"Creating access token for user: {username}")
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Root Route
@app.get("/")
async def root():
    logger.debug("Root endpoint accessed.")
    return {"message": "Welcome to Uniqtx!"}

# Signup Route (Register Chefs)
@app.post("/signup")
async def signup(chef: Chef):
    logger.debug(f"Signup request received for username: {chef.username}")
    existing_chef = await chef_collection.find_one({"username": chef.username})
    if existing_chef:
        logger.warning(f"Username {chef.username} already exists.")
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = hash_password(chef.password)
    chef_data = {"username": chef.username, "password": hashed_password}
    await chef_collection.insert_one(chef_data)
    
    logger.info(f"Chef {chef.username} registered successfully.")
    return {"message": "Chef registered successfully"}

# Login Route (Returns Token)
@app.post("/login")
async def login(chef: Chef):
    logger.debug(f"Login request received for username: {chef.username}")
    chef_data = await chef_collection.find_one({"username": chef.username})
    if not chef_data or not verify_password(chef.password, chef_data["password"]):
        logger.warning(f"Invalid credentials for username: {chef.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(chef.username)
    logger.info(f"Login successful for username: {chef.username}")
    return {"access_token": token, "token_type": "bearer"}

# Protected Route (Example)
@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    logger.debug("Protected route accessed.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            logger.warning("Invalid token: No username found in payload.")
            raise HTTPException(status_code=401, detail="Invalid token")
        logger.info(f"Access granted to user: {username}")
        return {"message": f"Welcome, {username}"}
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired.")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.warning("Invalid token.")
        raise HTTPException(status_code=401, detail="Invalid token")

# Include user routes
app.include_router(user_router, prefix="/user", tags=["User Management"])
app.include_router(order_router, prefix="/order", tags=["Order Management"])
app.include_router(tab_router, prefix="/tabs", tags=["Tabs"])

# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    logger.debug("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.debug("Application shutdown complete.")