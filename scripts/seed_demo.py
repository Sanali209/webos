import asyncio
import os
import uuid
from src.core.database import init_db
from src.core.auth import User, UserManager, BeanieUserDatabase
from src.modules.blogger.models import BlogPost
from src.modules.vault.models import Secret
from src.core.module_loader import loader
from src.core.config import settings

async def seed():
    print("🌱 Seeding Demo Data...")
    
    # 1. Ensure models are discovered
    loader.discover_and_load()
    discovered_models = loader.get_all_models()
    all_models = [User] + discovered_models
    
    print(f"🔍 Discovered {len(discovered_models)} models from modules: {[m.__name__ for m in discovered_models]}")
    
    # Initialize Core DB using the utility
    try:
        await init_db(all_models)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # 2. Setup User Manager for standalone use
    user_db = BeanieUserDatabase(User)
    # Mocking a context for the manager
    manager = UserManager(user_db)
    
    # 3. Create Admin User
    admin_email = "admin@webos.io"
    admin_pass = "admin123"
    
    from src.core.schemas import UserCreate
    
    user = await User.find_one({"email": admin_email})
    if not user:
        print(f"👤 Creating Admin User: {admin_email}")
        user = await manager.create(
            UserCreate(
                email=admin_email, 
                password=admin_pass, 
                is_active=True, 
                is_superuser=True, 
                is_verified=True,
                role="admin"
            )
        )
    else:
        print("✅ Admin user already exists.")

    # 4. Create Sample Blog Post
    blog_count = await BlogPost.count()
    if blog_count == 0:
        print("📝 Creating Sample Blog Post...")
        post = BlogPost(
            title="Welcome to WebOS Phase 8",
            slug="welcome-to-webos",
            content="This is a fully functional blog post created by the seeding script. "
                    "You can edit this in the Blogger Portal!",
            summary="A short introduction to the WebOS ecosystem.",
            status="published"
        )
        await post.save()
    else:
        print("✅ Blog posts already seeded.")

    # 5. Create Sample Secret
    secret_count = await Secret.count()
    if secret_count == 0:
        print("🔐 Creating Sample Vault Secret...")
        secret = Secret(
            label="Example Service",
            username="webos_demo",
            password="super_secret_password_123",
            website="https://demo.webos.io",
            notes="This is a demo secret that is visible only to you (the admin).",
            owner_id=user.id
        )
        await secret.save()
    else:
        print("✅ Vault secrets already seeded.")

    # 6. Ensure local storage exists
    os.makedirs("data/storage/local", exist_ok=True)
    with open("data/storage/local/readme.txt", "w") as f:
        f.write("Welcome to the WebOS File System!\nYou can manage files across Local and S3 storage using the File Commander.")

    print("\n✨ Seeding Complete!")

if __name__ == "__main__":
    # Ensure we can import from src
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(seed())
