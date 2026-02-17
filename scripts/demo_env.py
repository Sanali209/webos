import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

async def check_mongo():
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017/?authSource=admin")
        await client.admin.command('ping')
        print("✅ MongoDB: Connected")
    except Exception as e:
        print(f"❌ MongoDB: Failed - {e}")

async def check_redis():
    try:
        import redis.asyncio as redis
        r = redis.from_url("redis://localhost:6380")
        await r.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"❌ Redis: Failed - {e}")

async def check_minio():
    try:
        # MinIO check via http request as quick smoke test
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:9000/minio/health/live")
            if resp.status_code == 200:
                print("✅ MinIO: Alive")
            else:
                print(f"❌ MinIO: Status {resp.status_code}")
    except Exception as e:
        print(f"❌ MinIO: Failed - {e}")

async def main():
    print("System Integrity Check...")
    await asyncio.gather(
        check_mongo(),
        check_redis(),
        check_minio()
    )
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
