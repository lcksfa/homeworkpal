#!/usr/bin/env python3
"""
Entry point for running the simplified API server.
"""
import sys
from homeworkpal.simple.api import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)