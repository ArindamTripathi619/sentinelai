"""
Vercel serverless function entry point for SentinelAI backend.
Imports FastAPI app from backend/main.py and exposes it for Vercel's Python runtime.
"""
import sys
import os

# Add backend directory to path so modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    # Try to import the real app first
    from main import app
    print("Loaded main.py app", file=sys.stderr)
except Exception as e:
    # Fall back to minimal app if main.py fails to import
    print(f"WARNING: Failed to import main.py, loading minimal app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    from minimal_app import app
    print("Loaded minimal_app.py", file=sys.stderr)

# Export app for Vercel ASGI
__all__ = ['app']


