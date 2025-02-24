import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import UserCreate, UserLogin, Token, UserBase
from utilities import create_access_token, get_password_hash, verify_password
from datetime import datetime, timedelta
from pymongo import MongoClient
from typing import List
from jose import jwt, JWTError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "tabserv")
COLLECTION_NAME = "user"

client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
users_collection = db[COLLECTION_NAME]

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

user_router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

def admin_required(current_user=Depends(get_current_user)):
    if current_user["privilege"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin privileges required"
        )
    return current_user

@user_router.post("/register")
def register_user(user: UserCreate, admin_user: dict = Depends(admin_required)):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already exists"
        )
    user_data = {
        "name": user.name,
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "privilege": user.privilege,
        "table": user.table,
        "date_created": datetime.utcnow(),
        "date_last_login": None,
        "enable": True,
        "token_expiry": None
    }
    users_collection.insert_one(user_data)
    return {"message": f"User {user.username} created successfully"}

@user_router.post("/login", response_model=Token)
def login_user(user_data: UserLogin):
    user = users_collection.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user["enable"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"date_last_login": datetime.utcnow(), "token_expiry": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@user_router.get("/me", response_model=UserBase)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return UserBase(
        name=current_user["name"],
        username=current_user["username"],
        privilege=current_user["privilege"],
        table=current_user.get("table")
    )

@user_router.get("/list", response_model=List[UserBase])
def list_users(admin_user: dict = Depends(admin_required)):
    return [
        UserBase(
            name=user["name"],
            username=user["username"],
            privilege=user["privilege"],
            table=user.get("table")
        ) for user in users_collection.find()
    ]

@user_router.delete("/delete/{username}")
def delete_user(username: str, admin_user: dict = Depends(admin_required)):
    if users_collection.delete_one({"username": username}).deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    return {"message": "User deleted successfully"}

@user_router.put("/update/{username}")
def update_user(username: str, user_data: dict, current_user: dict = Depends(get_current_user)):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user["privilege"] != "admin" and current_user["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    users_collection.update_one({"username": username}, {"$set": user_data})
    return {"message": "User updated successfully"}
