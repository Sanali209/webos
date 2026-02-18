import sys
import os
import traceback

# Add project root to PYTHONPATH
sys.path.append(os.getcwd())

from src.core.module_loader import loader
from beanie import Document

def test_discovery():
    results_file = "test_results.txt"
    with open(results_file, "w") as f:
        f.write("🧪 Testing Model Discovery...\n")
        try:
            loader.discover_and_load()
            f.write(f"Loaded modules: {loader.loaded_modules}\n")
            
            models = loader.get_all_models()
            model_names = [m.__name__ for m in models]
            
            f.write(f"Found models: {model_names}\n")
            
            for m in models:
                f.write(f"Model {m.__name__} from module {m.__module__}\n")
                f.write(f"  MRO: {[c.__name__ for c in m.__mro__]}\n")
                f.write(f"  Is Document subclass: {issubclass(m, Document)}\n")

            if "BlogPost" not in model_names:
                f.write("❌ Error: BlogPost not found!\n")
                # Let's try to import it manually and check
                from src.modules.blogger.models import BlogPost
                f.write(f"Manual BlogPost import: {BlogPost}\n")
                f.write(f"Manual BlogPost Is Document subclass: {issubclass(BlogPost, Document)}\n")
                f.write(f"Document ID: {id(Document)}\n")
                from src.modules.blogger.models import Document as BloggerDocument
                f.write(f"Blogger Document ID: {id(BloggerDocument)}\n")

            if "Secret" not in model_names:
                f.write("❌ Error: Secret not found!\n")

            if "BlogPost" in model_names and "Secret" in model_names:
                f.write("✅ Model discovery test passed!\n")
            else:
                f.write("FAIL\n")
                sys.exit(1)
                
        except Exception as e:
            f.write(f"❌ Test crashed: {e}\n")
            f.write(traceback.format_exc())
            sys.exit(1)

if __name__ == "__main__":
    test_discovery()
