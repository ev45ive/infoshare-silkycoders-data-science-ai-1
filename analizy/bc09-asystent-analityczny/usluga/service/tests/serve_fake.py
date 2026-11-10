"""Serwer testowy z modelem testowym (bez kosztu): python serve_fake.py PORT."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import uvicorn  # noqa: E402

from conftest import fake_chat  # noqa: E402
from svc.api import create_app  # noqa: E402
from svc.config import get_settings  # noqa: E402

uvicorn.run(create_app(get_settings(), base_chat=fake_chat), host="127.0.0.1", port=int(sys.argv[1]), log_level="warning")
