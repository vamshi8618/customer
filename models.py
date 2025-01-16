# models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    username: str
    privilege: str
    table: Optional[str] = None

class UserCreate(UserBase):
    password: str
class UserLogin(BaseModel):
    username: str
    password: str
class UserInDB(UserBase):
    hashed_password: str
    date_created: datetime
    date_last_login: datetime = None
    enable: bool
    token_expiry: datetime = None

class Token(BaseModel):
    access_token: str
    token_type: str
    
