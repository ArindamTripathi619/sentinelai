"""
Vercel serverless entry point - imports and returns FastAPI app.
Falls back to a minimal app if imports fail, returning errors as JSON.
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

app_init_error = None

try:
    from main import app
except Exception as e:
    app_init_error = str(e)
    import traceback
    error_trace = traceback.format_exc()
    print(f"FAILED TO IMPORT MAIN: {error_trace}", file=sys.stderr)
    
    # If main fails, try minimal app
    try:
        from minimal_app import app
    except Exception as e2:
        # Both failed - create emergency app
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/{path_name:path}")
        @app.post("/{path_name:path}")
        @app.put("/{path_name:path}")
        @app.delete("/{path_name:path}")
        async def catch_all(path_name: str):
            return {
                "error": "App initialization failed",
                "main_error": app_init_error,
                "fallback_error": str(e2),
            }

__all__ = ['app']


