from fastapi import APIRouter, Depends, HTTPException, status, Body
from router import get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
import os

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hotel_db")
COLLECTION_NAME = "orders"
client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
orders_collection = db[COLLECTION_NAME]

order_router = APIRouter()

# Pydantic models
class OrderItem(BaseModel):
    item_id: str
    type: str  # Starter/Main Course/Dessert/Drinks
    item: str
    quantity: int
    cost: float
    instructions: Optional[str] = None
    status: str
    cook: Optional[str] = None
    addedby: str
    date: datetime
    takeaway: bool

class Order(BaseModel):
    order_id: str
    table: Optional[str]
    customer_name: Optional[str]
    phone_number: Optional[str]
    orders: List[OrderItem]
    order_date_time: datetime
    order_status: str  # ordered/processing/completed/cancelled
    dine_in_takeaway: str  # dine-in/takeaway
    bill_amount: float
    payment_status: str  # paid/unpaid
    payment_mode: Optional[str] = None
    order_by: Optional[dict] = None  # Added automatically based on user
    user_name: Optional[str] = None  # Added automatically based on user

# CRUD Endpoints
@order_router.post("/create", response_model=Order)
def create_order(order: Order, user: dict = Depends(get_current_user)):
    """
    Create a new order. Automatically assigns the logged-in user's username and role to 'order_by'.
    """
    if orders_collection.find_one({"order_id": order.order_id}):
        raise HTTPException(status_code=400, detail="Order ID already exists.")
    
    order_dict = order.dict()
    order_dict["order_by"] = {"username": user["username"], "role": user["role"]}
    orders_collection.insert_one(order_dict)
    return order_dict


@order_router.get("/status/{order_id}")
def get_order_status(order_id: str, user: dict = Depends(get_current_user)):
    """
    Get the status of a specific order.
    """
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return {"order_id": order_id, "order_status": order["order_status"]}


@order_router.put("/update/{order_id}")
def update_order(order_id: str, updated_items: List[OrderItem], user: dict = Depends(get_current_user)):
    """
    Update items in an existing order.
    """
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"orders": [item.dict() for item in updated_items]}}
    )
    return {"message": "Order updated successfully."}


@order_router.delete("/cancel/{order_id}")
def cancel_order(order_id: str, user: dict = Depends(get_current_user)):
    """
    Cancel an order. Cancellation is allowed only if the status is 'ordered'.
    """
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    if order["order_status"] != "ordered":
        raise HTTPException(
            status_code=400,
            detail="Order cannot be cancelled as it is not in 'ordered' status."
        )
    
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"order_status": "cancelled"}}
    )
    return {"message": "Order cancelled successfully."}


@order_router.put("/make_takeaway/{order_id}")
def make_order_takeaway(order_id: str, user: dict = Depends(get_current_user)):
    """
    Convert a dine-in order to takeaway.
    """
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    if order["dine_in_takeaway"] != "dine-in":
        raise HTTPException(
            status_code=400,
            detail="Only dine-in orders can be converted to takeaway."
        )
    
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"dine_in_takeaway": "takeaway"}}
    )
    return {"message": "Order converted to takeaway successfully."}


@order_router.get("/all")
def get_all_orders(user: dict = Depends(get_current_user)):
    """
    Get all orders for the logged-in user.
    """
    orders = list(orders_collection.find({"order_by.username": user["username"]}))
    return {"orders": orders}

#################################################

@order_router.put("/modify_order_items/{order_id}")
def modify_order_items(
    order_id: str,
    modifications: dict = Body(...),  # Includes instructions for takeaway, cancel, and adding new items
    user: dict = Depends(get_current_user)
):
    """
    Modify items within the 'orders' field of an existing order.
    """
    # Fetch the existing order
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Extract modifications
    takeaway_items = modifications.get("takeaway_items", [])  # List of item IDs to mark as takeaway
    cancel_items = modifications.get("cancel_items", [])      # List of item IDs to cancel
    new_items = modifications.get("new_items", [])            # List of new items to add
    
    updated_orders = []

    # Step 1: Modify existing items
    for item in order["orders"]:
        if item["item_id"] in takeaway_items:
            item["takeaway"] = True  # Mark as takeaway
        if item["item_id"] in cancel_items:
            if item["status"] != "ordered":
                raise HTTPException(
                    status_code=400,
                    detail=f"Item with ID {item['item_id']} cannot be cancelled as it is not in 'ordered' status.",
                )
            item["status"] = "cancelled"  # Cancel the item
        updated_orders.append(item)

    # Step 2: Add new items
    for new_item in new_items:
        updated_orders.append(new_item)

    # Update the order in the database
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"orders": updated_orders}}
    )

    return {
        "message": "Order items updated successfully.",
        "order_id": order_id,
        "updated_orders": updated_orders,
    }

@order_router.put("/mark_takeaway/{order_id}")
def mark_items_takeaway(
    order_id: str,
    item_ids: list = Body(...),  # List of item IDs to mark as takeaway
    user: dict = Depends(get_current_user)
):
    """
    Marks specific items in the 'orders' field of an order as takeaway.
    """
    # Fetch the existing order
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    updated_orders = []
    for item in order["orders"]:
        if item["item_id"] in item_ids:
            item["takeaway"] = True  # Mark as takeaway
        updated_orders.append(item)

    # Update the order in the database
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"orders": updated_orders}}
    )

    return {
        "message": "Items marked as takeaway successfully.",
        "order_id": order_id,
        "updated_orders": updated_orders,
    }

################################################################
# Endpoint for setting up the billing status of the order
################################################################

@order_router.put("/set_billing_status/{order_id}/{status}")
def set_billing_status(order_id: str, status: str, user: dict = Depends(get_current_user)):
    """
    Set the billing status of an order to the specified status.
    """
    # Fetch the existing order
    order = orders_collection.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Update the order in the database
    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"payment_status": status}}
    )

    return {
        "message": "Order billing status updated successfully.",
        "order_id": order_id,
        "payment_status": status,
    }
