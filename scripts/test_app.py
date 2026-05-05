#!/usr/bin/env python3
import os
import sys

# Set DATABASE_URL before importing anything from the app
os.environ['DATABASE_URL'] = "postgresql://postgres:mybday28jul@db.yevnlrajklfkqjhcrdps.supabase.co:5432/postgres?sslmode=require"
os.environ['SUPABASE_URL'] = "https://yevnlrajklfkqjhcrdps.supabase.co"
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlldm5scmFqa2xma3FqaGNyZHBzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzY4ODkxMywiZXhwIjoyMDkzMjY0OTEzfQ.tbLzIGd4JK0kH7rSnCYGhPd5m5UB9wnOpQpk2KWJqY4"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    print("Importing FastAPI app...")
    from main import app
    print("✅ App imported successfully")
    
    print("Testing health endpoint...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text[:200]}")
    if response.status_code == 200:
        print(f"JSON: {response.json()}")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
