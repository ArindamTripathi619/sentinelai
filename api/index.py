"""
Vercel serverless function entry point for SentinelAI backend.
Imports FastAPI app from backend/main.py and exposes it for Vercel's Python runtime.
"""
import sys
import os

# Add backend directory to path so modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the FastAPI app from backend
from main import app

# Export app for Vercel
__all__ = ['app']
