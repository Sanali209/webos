from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from src.core.config import settings
from src.core.auth import User, UserManager, BeanieUserDatabase
from src.core.schemas import UserCreate
import asyncio

async def setup_default_user():
    """
    Seeds the default admin user if no users exist in the database.
    """
    logger.info("📡 Checking for existing users...")
    
    try:
        # Check if any user exists
        user_count = await User.count()
        
        if user_count == 0:
            admin_email = "admin@webos.io"
            admin_pass = "admin123"
            
            user_db = BeanieUserDatabase(User)
            manager = UserManager(user_db)
            
            logger.info(f"👤 No users found. Creating Default Admin User: {admin_email}")
            await manager.create(
                UserCreate(
                    email=admin_email,
                    password=admin_pass,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                    role="admin"
                )
            )
            logger.info("✅ Default Admin User created.")
        else:
            logger.info(f"✅ Found {user_count} existing users. Skipping default user creation.")
            
    except Exception as e:
        logger.error(f"❌ Failed to clear/seed database: {e}")
        # Note: We don't necessarily want to block startup if seeding fails
