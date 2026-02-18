import asyncio
import time
from src.core.storage import afs
from src.modules.cache.manager import cache
from src.core.module_loader import ModuleLoader
from src.core.hooks import WebOSHookSpec

async def demo_storage():
    print("--- Phase 5: Storage & Caching Demo ---")
    
    # 1. Setup Environment (Bootstrap Hooks)
    from src.core.module_loader import loader
    loader.discover_and_load()
    loader.register_data_sources(afs)
    print(f"Registered sources in AFS: {list(afs._sources.keys())}")
    
    # 2. Test Local Storage
    print("\n[Local Storage Test]")
    source_local, path = await afs.resolve("fs://local/test_folder/hello.txt")
    await source_local.save_file(path, b"Hello from WebOS AFS!")
    print(f"✅ Saved to fs://local/{path}")
    
    files = await source_local.list_dir("test_folder")
    print(f"📁 List dir 'test_folder': {[f.name for f in files]}")
    
    content = await source_local.open_file(path)
    print(f"📖 Read content: {content.read().decode()}")

    # 3. Test S3 Storage (MinIO)
    print("\n[S3 Storage Test]")
    try:
        source_s3, s3_path = await afs.resolve("fs://s3/demo/cloud.txt")
        await source_s3.connect()
        await source_s3.save_file(s3_path, b"Hello from the Cloud!")
        print(f"✅ Saved to fs://s3/{s3_path}")
        
        s3_files = await source_s3.list_dir("demo")
        print(f"📁 List S3 dir 'demo': {[f.name for f in s3_files]}")
    except Exception as e:
        print(f"❌ S3 Test Failed (Is MinIO running?): {e}")

    # 4. Test Caching
    print("\n[Caching Test]")
    
    @cache.memoize(expire=2)
    def expensive_func(n):
        print(f"   (Computing expensive_func({n})...)")
        time.sleep(1)
        return n * 2

    print("Call 1 (Cache Miss):")
    start = time.time()
    res1 = expensive_func(10)
    print(f"   Result: {res1} (Time: {time.time() - start:.2f}s)")

    print("Call 2 (Cache Hit):")
    start = time.time()
    res2 = expensive_func(10)
    print(f"   Result: {res2} (Time: {time.time() - start:.2f}s)")

    print("Waiting 3s for cache expiration...")
    time.sleep(3)

    print("Call 3 (Expired - Cache Miss):")
    start = time.time()
    res3 = expensive_func(10)
    print(f"   Result: {res3} (Time: {time.time() - start:.2f}s)")

    print("\n🏁 Demo Complete")

if __name__ == "__main__":
    asyncio.run(demo_storage())
