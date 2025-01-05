from fastapi import APIRouter, HTTPException, Depends, Body
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from router import get_current_user
import os

# MongoDB connection (adjust as needed)


MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hotel_db")
COLLECTION_NAME = "tabs"
client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
orders_collection = db[COLLECTION_NAME]




tab_router = APIRouter()

# Models
class TabBase(BaseModel):
    id: Optional[str]
    name: str
    user: Optional[str] = None
    table: Optional[int] = None
    waiter_request: Optional[bool] = False
    waiter_text: Optional[str] = ""
    support_request: Optional[bool] = False
    support_text: Optional[str] = ""
    user_type: Optional[str] = None  # Manager/Customer/Waiter/Billing/Table


# Admin endpoints
@tab_router.post("/add_tab", status_code=201)
def add_tab(tab: TabBase, user: dict = Depends(get_current_user)):
    """
    Add a new tab. Only Admin users are allowed.
    """
    if user["user_type"] != "Manager":
        raise HTTPException(status_code=403, detail="Only admins can add tabs.")
    
    if tabs_collection.find_one({"name": tab.name}):
        raise HTTPException(status_code=400, detail="Tab name already exists.")
    
    tabs_collection.insert_one(tab.dict())
    return {"message": "Tab added successfully", "tab": tab}


@tab_router.delete("/delete_tab/{tab_name}", status_code=200)
def delete_tab(tab_name: str, user: dict = Depends(get_current_user)):
    """
    Delete a tab by name. Only Admin users are allowed.
    """
    if user["user_type"] != "Manager":
        raise HTTPException(status_code=403, detail="Only admins can delete tabs.")
    
    result = tabs_collection.delete_one({"name": tab_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    return {"message": "Tab deleted successfully"}


@tab_router.put("/update_tab_name/{old_name}", status_code=200)
def update_tab_name(old_name: str, new_name: str, user: dict = Depends(get_current_user)):
    """
    Update the name of a tab. Only Admin users are allowed.
    """
    if user["user_type"] != "Manager":
        raise HTTPException(status_code=403, detail="Only admins can update tabs.")
    
    if tabs_collection.find_one({"name": new_name}):
        raise HTTPException(status_code=400, detail="New tab name already exists.")
    
    result = tabs_collection.update_one({"name": old_name}, {"$set": {"name": new_name}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    return {"message": "Tab name updated successfully"}


# Update table number
@tab_router.put("/update_table/{tab_name}", status_code=200)
def update_table(tab_name: str, table: int, user: dict = Depends(get_current_user)):
    """
    Update the table number for a tab.
    """
    tab = tabs_collection.find_one({"name": tab_name})
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    tabs_collection.update_one(
        {"name": tab_name},
        {"$set": {"table": table, "user": user["username"], "user_type": user["user_type"]}}
    )
    return {"message": "Table number updated successfully"}


# Query all tabs
@tab_router.get("/list_tabs", response_model=List[TabBase])
def list_tabs(user: dict = Depends(get_current_user)):
    """
    List all tabs.
    """
    tabs = list(tabs_collection.find())
    return tabs


# Call waiter with text
@tab_router.put("/call_waiter/{tab_name}", status_code=200)
def call_waiter(tab_name: str, waiter_text: str, user: dict = Depends(get_current_user)):
    """
    Call a waiter with a text message.
    """
    tab = tabs_collection.find_one({"name": tab_name})
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    tabs_collection.update_one(
        {"name": tab_name},
        {"$set": {"waiter_request": True, "waiter_text": waiter_text}}
    )
    return {"message": "Waiter called successfully"}


# Clear waiter request
@tab_router.put("/clear_waiter/{tab_name}", status_code=200)
def clear_waiter(tab_name: str, user: dict = Depends(get_current_user)):
    """
    Clear waiter request and text.
    """
    tab = tabs_collection.find_one({"name": tab_name})
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    tabs_collection.update_one(
        {"name": tab_name},
        {"$set": {"waiter_request": False, "waiter_text": ""}}
    )
    return {"message": "Waiter request cleared successfully"}


# Call support with text
@tab_router.put("/call_support/{tab_name}", status_code=200)
def call_support(tab_name: str, support_text: str, user: dict = Depends(get_current_user)):
    """
    Call support with a text message.
    """
    tab = tabs_collection.find_one({"name": tab_name})
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    tabs_collection.update_one(
        {"name": tab_name},
        {"$set": {"support_request": True, "support_text": support_text}}
    )
    return {"message": "Support called successfully"}


# Clear support request
@tab_router.put("/clear_support/{tab_name}", status_code=200)
def clear_support(tab_name: str, user: dict = Depends(get_current_user)):
    """
    Clear support request and text.
    """
    tab = tabs_collection.find_one({"name": tab_name})
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found.")
    
    tabs_collection.update_one(
        {"name": tab_name},
        {"$set": {"support_request": False, "support_text": ""}}
    )
    return {"message": "Support request cleared successfully"}
