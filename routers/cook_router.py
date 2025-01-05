from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from router import get_current_user
import os

# MongoDB connection (adjust as needed)


MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hotel_db")
COLLECTION_NAME = "dish_master"
ORDER_COLLECTION_NAME = "orders"
client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
orders_collection = db[ORDER_COLLECTION_NAME]
dishes_collection = db[COLLECTION_NAME]


cook_router = APIRouter()

# Models
class DishBase(BaseModel):
    id: Optional[str]
    name: str
    available: bool
    type: str  # starter/Main Course/Desert/Drinks
    dish: str
    rate: float
    takeaway_rate: float
    image: Optional[str] = None
    date_add: datetime = datetime.utcnow()
    added_by: Optional[str] = None


class OrderUpdate(BaseModel):
    status: str
    cook: str
    updated_at: datetime = datetime.utcnow()


# Endpoints
@cook_router.get("/list_pending_dishes", status_code=200)
def list_pending_dishes(user: dict = Depends(get_current_user)):
    """
    List all pending dishes from the `orders` collection, grouped table-wise.
    Includes order_id, table, and order_status.
    Only accessible to Cook users.
    """
    if user["user_type"] != "Cook":
        raise HTTPException(status_code=403, detail="Only cooks can access this endpoint.")
    
    pending_orders = orders_collection.find({"orders.status": "pending"}, {"_id": 0, "order_id": 1, "table": 1, "orders": 1})
    
    result = []
    for order in pending_orders:
        table_orders = [
            {
                "table": order["table"],
                "order_id": order["order_id"],
                "dish": dish["item"],
                "status": dish["status"],
            }
            for dish in order["orders"]
            if dish["status"] == "pending"
        ]
        result.extend(table_orders)
    
    return result


@cook_router.put("/update_order_status/{order_id}", status_code=200)
def update_order_status(order_id: str, update_data: OrderUpdate, user: dict = Depends(get_current_user)):
    """
    Modify the parameters of an order's `orders` field.
    Updates: status, cook, and updated_at.
    Only accessible to Cook users.
    """
    if user["user_type"] != "Cook":
        raise HTTPException(status_code=403, detail="Only cooks can update orders.")
    
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    updated = orders_collection.update_one(
        {"order_id": order_id, "orders.status": "pending"},
        {"$set": {
            "orders.$.status": update_data.status,
            "orders.$.cook": update_data.cook,
            "orders.$.updated_at": update_data.updated_at,
        }}
    )
    if updated.matched_count == 0:
        raise HTTPException(status_code=400, detail="No matching pending orders to update.")
    
    return {"message": "Order updated successfully"}


@cook_router.post("/add_dish", status_code=201)
def add_dish(dish: DishBase, user: dict = Depends(get_current_user)):
    """
    Add a new dish to the `dish_master` collection.
    Only accessible to Cook users.
    """
    if user["user_type"] != "Cook":
        raise HTTPException(status_code=403, detail="Only cooks can add dishes.")
    
    if dishes_collection.find_one({"name": dish.name}):
        raise HTTPException(status_code=400, detail="Dish with this name already exists.")
    
    dish.added_by = user["username"]
    dish.date_add = datetime.utcnow()
    dishes_collection.insert_one(dish.dict())
    return {"message": "Dish added successfully", "dish": dish}


@cook_router.put("/modify_dish/{dish_id}", status_code=200)
def modify_dish(dish_id: str, dish: DishBase, user: dict = Depends(get_current_user)):
    """
    Modify an existing dish in the `dish_master` collection.
    Only accessible to Cook users.
    """
    if user["user_type"] != "Cook":
        raise HTTPException(status_code=403, detail="Only cooks can modify dishes.")
    
    updated = dishes_collection.update_one(
        {"id": dish_id},
        {"$set": dish.dict(exclude_unset=True)}
    )
    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dish not found.")
    
    return {"message": "Dish modified successfully"}


@cook_router.delete("/delete_dish/{dish_id}", status_code=200)
def delete_dish(dish_id: str, user: dict = Depends(get_current_user)):
    """
    Delete a dish from the `dish_master` collection.
    Only accessible to Cook users.
    """
    if user["user_type"] != "Cook":
        raise HTTPException(status_code=403, detail="Only cooks can delete dishes.")
    
    result = dishes_collection.delete_one({"id": dish_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dish not found.")
    
    return {"message": "Dish deleted successfully"}
