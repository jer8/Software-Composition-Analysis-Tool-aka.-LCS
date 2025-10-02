"""
Unit tests for License Scanner API
Run with: pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import json
from main import app, NPMParser, PipParser, MavenParser

client = TestClient(app)

# ============= Test API Endpoints =============

def test_root_endpoint():
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()