import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Must precede importing app configuration and SQLAlchemy engine.
_tmpdir = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + _tmpdir.name.replace('\\','/') + '/test_foodops.db'
os.environ['DEMO_SEED'] = 'true'
os.environ['OPENAI_API_KEY'] = ''
os.environ['RAG_EMBEDDINGS'] = 'tfidf'
from app.main import app  # noqa: E402

@pytest.fixture(scope='session')
def client():
    with TestClient(app) as client:
        yield client
