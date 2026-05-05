#!/usr/bin/env python3
import os
import sys

# Set all required environment variables
os.environ['DATABASE_URL'] = "postgresql://postgres:mybday28jul@db.yevnlrajklfkqjhcrdps.supabase.co:5432/postgres?sslmode=require"
os.environ['SUPABASE_URL'] = "https://yevnlrajklfkqjhcrdps.supabase.co"
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlldm5scmFqa2xma3FqaGNyZHBzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzY4ODkxMywiZXhwIjoyMDkzMjY0OTEzfQ.tbLzIGd4JK0kH7rSnCYGhPd5m5UB9wnOpQpk2KWJqY4"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("Importing modules step by step...")

try:
    print("1. Importing database...")
    from database import engine, get_db
    print("   ✅ database imported")
    
    print("2. Importing models...")
    from models import Base
    print("   ✅ models imported")
    
    print("3. Importing auth...")
    import auth
    print("   ✅ auth imported")
    
    print("4. Importing users...")
    import users
    print("   ✅ users imported")
    
    print("5. Importing alerts...")
    import alerts
    print("   ✅ alerts imported")
    
    print("6. Importing analytics...")
    import analytics
    print("   ✅ analytics imported")
    
    print("7. Importing scoring...")
    import scoring
    print("   ✅ scoring imported")
    
    print("8. Importing FastAPI main...")
    from main import app
    print("   ✅ main (FastAPI app) imported")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    import traceback
    print(f"\n❌ Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)
