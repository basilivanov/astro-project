import sys
import os
sys.path.append(os.getcwd())
from backend.app.db import apply_runtime_migrations

if __name__ == "__main__":
    print("Running runtime migrations...")
    apply_runtime_migrations()
    print("Done.")
