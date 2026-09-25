"""Integration checks for suggestions against an explicitly configured test database."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import DATABASE_URL
from app.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated PostgreSQL database to run integration tests")
    database_name = make_url(test_url).database
    if not database_name or not database_name.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must name a database ending in _test")
    if make_url(test_url).set(password=None) == make_url(DATABASE_URL).set(password=None):
        pytest.fail("TEST_DATABASE_URL must differ from DATABASE_URL")

    backend_dir = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_dir,
        env={**os.environ, "DATABASE_URL": test_url},
        check=True,
    )
    engine = create_engine(test_url)
    yield engine
    engine.dispose()


@pytest.fixture
def client(test_engine):
    with test_engine.connect() as connection:
        outer = connection.begin()

        def override_db():
            with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as session:
                yield session

        app.dependency_overrides[get_db] = override_db
        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.pop(get_db, None)
            outer.rollback()


def entry(roaster: str, product: str, grinder: str) -> dict:
    return {
        "date": "2026-09-24",
        "roaster": roaster,
        "product": product,
        "roast_level": 3,
        "recipe_type": "pour_over",
        "coffee_weight_g": 18,
        "brew_time_seconds": 150,
        "total_yield_g": 300,
        "grind_setting": 18.5,
        "grinder": grinder,
        "rating": 4,
    }


def test_suggestions_are_scoped_sorted_and_referenced(client: TestClient) -> None:
    first = client.post("/api/coffee/recipes", json=entry("North Roaster", "House Blend", "A Grinder"))
    second = client.post("/api/coffee/recipes", json=entry("South Roaster", "House Blend", "B Grinder"))
    third = client.post("/api/coffee/recipes", json=entry("North Roaster", "Honey Lot", "A Grinder"))
    assert [result.status_code for result in (first, second, third)] == [201, 201, 201]

    assert client.get("/api/coffee/recipes/suggestions", params={"field": "roaster"}).json() == {
        "values": ["North Roaster", "South Roaster"]
    }
    assert client.get("/api/coffee/recipes/suggestions", params={
        "field": "product", "roaster": "north roaster", "q": "h",
    }).json() == {"values": ["Honey Lot", "House Blend"]}
    assert client.get("/api/coffee/recipes/suggestions", params={
        "field": "product", "roaster": "unknown",
    }).json() == {"values": []}
    assert client.get("/api/coffee/recipes/suggestions", params={
        "field": "grinder", "q": "A",
    }).json() == {"values": ["A Grinder"]}

    assert client.delete(f"/api/coffee/recipes/{second.json()['id']}").status_code == 204
    assert client.get("/api/coffee/recipes/suggestions", params={"field": "roaster"}).json() == {
        "values": ["North Roaster"]
    }
    assert client.get("/api/coffee/recipes/suggestions", params={"field": "grinder"}).json() == {
        "values": ["A Grinder"]
    }


def test_product_suggestions_require_roaster(client: TestClient) -> None:
    assert client.get("/api/coffee/recipes/suggestions", params={"field": "product"}).status_code == 422
    assert client.get("/api/coffee/recipes/suggestions", params={
        "field": "grinder", "roaster": "North Roaster",
    }).status_code == 422
