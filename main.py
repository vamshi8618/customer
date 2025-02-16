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
    return {"message": "Welcome to Tab based  Management System!"}
