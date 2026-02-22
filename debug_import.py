import sys
import traceback

try:
    import src.modules.dam.hooks
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
