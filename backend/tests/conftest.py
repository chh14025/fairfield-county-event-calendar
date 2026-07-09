import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["ADMIN_PASSWORD"] = "testpw"

import pytest
from fastapi.testclient import TestClient

from app.api.submissions import _submissions_by_ip
from app.api.tips import _tips_by_ip
from app.db import Base, SessionLocal, engine
from app.main import app


@pytest.fixture()
def client():
    _submissions_by_ip.clear()
    _tips_by_ip.clear()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(engine)
    session = SessionLocal()
    yield session
    session.close()
