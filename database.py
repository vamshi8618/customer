from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB URI (replace with your MongoDB connection string)
MONGO_URI = "mongodb://localhost:27017"  # Use your connection URI here
DATABASE_NAME = "vamshi"  # Replace with your desired DB name

# Create a MongoDB client and connect to the database
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
