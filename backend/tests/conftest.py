"""
Shared pytest fixtures for the test suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_knowledge_base_service
from app.api.main import app
from app.models import Comment, Document, Ticket, User

AUTH_HEADERS = {"X-API-Key": "devmate-local-key"}


@pytest.fixture(autouse=True)
def reset_registries():
    """
    Document/Ticket/Comment/User each keep a class-level `registry`
    list - a single, shared, mutable list every constructor call
    appends to, regardless of which test (or which request) created
    the object. Without resetting these between tests, objects built
    by one test silently leak into every test that runs after it in
    the same pytest session - and specifically corrupt
    Document.find_by_id() / User.find_by_id(), which the Team Mismatch
    logic depends on internally.

    autouse=True means every single test in this whole suite gets this
    fixture automatically - no test file needs to explicitly request
    it by name.
    """
    yield
    Document.registry.clear()
    Ticket.registry.clear()
    Comment.registry.clear()
    User.registry.clear()
    # The KnowledgeBaseService provider is @lru_cache'd at the process
    # level too - clear that cache as well, so the NEXT test that
    # touches the real app rebuilds it fresh (reloading docs/ and
    # tickets.csv, re-seeding users) instead of reusing a stale
    # instance built by an earlier test.
    get_knowledge_base_service.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """A fresh TestClient wrapping the real FastAPI app, for integration tests."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return AUTH_HEADERS