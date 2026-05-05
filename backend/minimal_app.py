#!/usr/bin/env python3
"""Minimal FastAPI app to test"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}
