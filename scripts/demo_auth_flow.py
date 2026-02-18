import asyncio
import httpx
from loguru import logger

BASE_URL = "http://localhost:8000"

async def demo_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Health Check
        try:
            resp = await client.get("/health")
            logger.info(f"Health check: {resp.json()}")
        except Exception as e:
            logger.error(f"Server not running? {e}")
            return

        # 2. Register
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        logger.info(f"Registering user: {user_data['email']}")
        resp = await client.post("/api/auth/register", json=user_data)
        if resp.status_code == 201:
            logger.success("User registered successfully")
        elif resp.status_code == 400:
            logger.warning("User already exists or bad request")
        else:
            logger.error(f"Registration failed: {resp.text}")

        # 3. Login
        logger.info("Logging in...")
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        resp = await client.post("/api/auth/jwt/login", data=login_data)
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            logger.success("Login successful")
            headers = {"Authorization": f"Bearer {token}"}

            # 4. Get Profile
            logger.info("Fetching user profile...")
            resp = await client.get("/api/users/me", headers=headers)
            logger.success(f"User Profile: {resp.json()}")
        else:
            logger.error(f"Login failed: {resp.text}")

if __name__ == "__main__":
    asyncio.run(demo_auth())
