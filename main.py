<<<<<<< HEAD
# main.py
from fastapi import FastAPI
from router import user_router
from routers.order import order_router
from routers.tab_router import tab_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# FastAPI instance
app = FastAPI()
# List of origins allowed to access your API
origins = [
    "http://localhost:8081",  # Example: React app running on localhost
    "http://localhost:8080",  # Example: React app running on localhost
    "http://localhost:3000",  # Example: React app running on localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from specified origins
    allow_credentials=True,  # Allows cookies to be sent along with requests
    allow_methods=["*"],     # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],     # Allows all headers
)
# Include user routes
app.include_router(user_router, prefix="/user", tags=["User Management"])
app.include_router(order_router, prefix="/order", tags=["Order Management"])
app.include_router(tab_router, prefix="/tabs", tags=["Tabs"])

@app.get("/")
def root():
    return {"message": "Welcome Uniqtx!"}
=======
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import jwt
import datetime
import motor.motor_asyncio

# FastAPI App
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

# Pydantic Models
class Chef(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Hash Password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify Password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT Token
def create_access_token(username: str):
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Root Route
@app.get("/")
async def root():
    return {"message": "FastAPI Backend is Running!"}

# Signup Route (Register Chefs)
@app.post("/signup")
async def signup(chef: Chef):
    existing_chef = await chef_collection.find_one({"username": chef.username})
    if existing_chef:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = hash_password(chef.password)
    chef_data = {"username": chef.username, "password": hashed_password}
    await chef_collection.insert_one(chef_data)
    
    return {"message": "Chef registered successfully"}

# Login Route (Returns Token)
@app.post("/login")
async def login(chef: Chef):
    chef_data = await chef_collection.find_one({"username": chef.username})
    if not chef_data or not verify_password(chef.password, chef_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(chef.username)
    return {"access_token": token, "token_type": "bearer"}

# Protected Route (Example)
@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"message": f"Welcome, {username}"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
>>>>>>> 5645699 (first commit)
