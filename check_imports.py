try:
    from src.core.schemas import UserRead
    print("✅ Successfully imported UserRead from src.core.schemas")
except ImportError as e:
    print(f"❌ Failed to import UserRead: {e}")

try:
    from src.main import app
    print("✅ Successfully imported app from src.main")
    
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from src.core.config import settings
    
    async def check_mongo():
        url = settings.MONGO_URL
        print(f"Connecting to {url} (No Auth)...")
        client = AsyncIOMotorClient(url)
        await client.admin.command('ping')
        print("✅ MongoDB: Connection Successful (No Auth)")
    
    import asyncio
    asyncio.run(check_mongo())
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
