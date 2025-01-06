# main.py
from fastapi import FastAPI
from router import user_router
from routers.order import order_router
from routers.tab_router import tab_router
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FastAPI instance
app = FastAPI()

# Include user routes
app.include_router(user_router, prefix="/user", tags=["User Management"])
app.include_router(order_router, prefix="/order", tags=["Order Management"])
app.include_router(tab_router, prefix="/tabs", tags=["Tabs"])

@app.get("/")
def root():
    return {"message": "Welcome to Tab based Order Management System!"}
