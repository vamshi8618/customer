# main.py
from fastapi import FastAPI
from router import user_router
from routers.order_router import order_router
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FastAPI instance
app = FastAPI()

# Include user routes
app.include_router(user_router, prefix="/user", tags=["User Management"])
app.include_router(order_router, prefix="/order", tags=["Order Management"])

@app.get("/")
def root():
    return {"message": "Welcome to the Hotel Order Management System!"}
