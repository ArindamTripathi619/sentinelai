#!/usr/bin/env python3
"""Minimal FastAPI app to test"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "app": "minimal"}

@app.get("/health")
def health():
    return {"status": "healthy", "app": "minimal"}

@app.get("/api/")
def api_root():
    return {"status": "ok", "app": "minimal"}

@app.get("/api/health")
def api_health():
    return {"status": "healthy", "app": "minimal"}
