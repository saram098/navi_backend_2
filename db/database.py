import motor.motor_asyncio
from settings.config import settings
from pymongo.errors import ServerSelectionTimeoutError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database and client objects
client = None
db = None

async def connect_to_mongo():
    """Connect to MongoDB Atlas when the application starts."""
    global client, db
    try:
        logger.info("Connecting to MongoDB Atlas...")
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        
        # Verify the connection is successful
        await client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas successfully")
        
        # Create indexes for efficient querying
        await create_indexes()
        
    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB Atlas")
        raise

async def close_mongo_connection():
    """Close MongoDB connection when the application shuts down."""
    global client
    if client:
        logger.info("Closing MongoDB connection...")
        client.close()
        logger.info("MongoDB connection closed")

async def create_indexes():
    """Create necessary indexes for the collections."""
    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("phone_number", unique=True, sparse=True)
    
    # Physicians collection indexes
    await db.physicians.create_index("specialty")
    await db.physicians.create_index("consultation_price")
    
    # Appointments collection indexes
    await db.appointments.create_index("user_id")
    await db.appointments.create_index("physician_id")
    await db.appointments.create_index("date")
    await db.appointments.create_index([("user_id", 1), ("date", 1)])
    
    logger.info("Database indexes created successfully")

def get_database():
    """Return the database instance."""
    return db
