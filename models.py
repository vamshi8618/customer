from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# User Models
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
    date_last_login: Optional[datetime] = None
    enable: bool
    token_expiry: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# Item Model
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int
