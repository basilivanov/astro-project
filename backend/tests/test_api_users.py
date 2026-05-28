"""Tests for the in-memory user CRUD API router."""

import httpx
import pytest
from fastapi import FastAPI

from app.api.users import clear_user_store, router


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    clear_user_store()
    app = FastAPI()
    app.include_router(router)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


async def create_user(
    client: httpx.AsyncClient,
    username: str = "valid_user",
    email: str = "user@example.com",
):
    return await client.post("/api/users", json={"username": username, "email": email})


@pytest.mark.anyio
async def test_create_user_success(client):
    response = await create_user(client)

    assert response.status_code == 201
    payload = response.json()
    assert payload["username"] == "valid_user"
    assert payload["email"] == "user@example.com"
    assert payload["is_active"] is True
    assert payload["id"]
    assert payload["created_at"]


@pytest.mark.anyio
async def test_create_user_rejects_invalid_username(client):
    response = await create_user(client, username="no spaces")

    assert response.status_code == 400
    assert "Username must be 3-50 characters" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_user_rejects_invalid_email(client):
    response = await create_user(client, email="not-an-email")

    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be a valid email address"


@pytest.mark.anyio
async def test_create_user_rejects_duplicate_username(client):
    await create_user(client, username="same_user", email="first@example.com")

    response = await create_user(client, username="SAME_USER", email="second@example.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already exists"


@pytest.mark.anyio
async def test_create_user_rejects_duplicate_email(client):
    await create_user(client, username="first_user", email="same@example.com")

    response = await create_user(client, username="second_user", email="SAME@example.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


@pytest.mark.anyio
async def test_get_user_by_id_success(client):
    created = (await create_user(client)).json()

    response = await client.get(f"/api/users/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


@pytest.mark.anyio
async def test_get_user_by_id_returns_400_for_invalid_uuid(client):
    response = await client.get("/api/users/not-a-uuid")

    assert response.status_code == 400
    assert response.json()["detail"] == "User ID must be a valid UUID"


@pytest.mark.anyio
async def test_get_user_by_id_returns_404_for_missing_user(client):
    response = await client.get("/api/users/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.anyio
async def test_list_users_without_filter_returns_all_users(client):
    first = (await create_user(client, username="first_user", email="first@example.com")).json()
    second = (await create_user(client, username="second_user", email="second@example.com")).json()
    await client.delete(f"/api/users/{second['id']}")

    response = await client.get("/api/users")

    assert response.status_code == 200
    assert [user["id"] for user in response.json()] == [first["id"], second["id"]]


@pytest.mark.anyio
async def test_list_users_filters_by_active_status(client):
    active = (await create_user(client, username="active_user", email="active@example.com")).json()
    inactive = (await create_user(client, username="inactive_user", email="inactive@example.com")).json()
    await client.delete(f"/api/users/{inactive['id']}")

    active_response = await client.get("/api/users?active=true")
    inactive_response = await client.get("/api/users?active=false")

    assert active_response.status_code == 200
    assert [user["id"] for user in active_response.json()] == [active["id"]]
    assert inactive_response.status_code == 200
    assert [user["id"] for user in inactive_response.json()] == [inactive["id"]]


@pytest.mark.anyio
async def test_update_user_success(client):
    created = (await create_user(client)).json()

    response = await client.put(
        f"/api/users/{created['id']}",
        json={"email": "updated@example.com", "is_active": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "updated@example.com"
    assert payload["is_active"] is False
    assert payload["username"] == created["username"]


@pytest.mark.anyio
async def test_update_user_rejects_invalid_email(client):
    created = (await create_user(client)).json()

    response = await client.put(f"/api/users/{created['id']}", json={"email": "bad"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be a valid email address"


@pytest.mark.anyio
async def test_update_user_rejects_duplicate_email(client):
    first = (await create_user(client, username="first_user", email="first@example.com")).json()
    await create_user(client, username="second_user", email="second@example.com")

    response = await client.put(f"/api/users/{first['id']}", json={"email": "second@example.com"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


@pytest.mark.anyio
async def test_update_user_rejects_unsupported_fields(client):
    created = (await create_user(client)).json()

    response = await client.put(f"/api/users/{created['id']}", json={"username": "new_name"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported update field(s): username"


@pytest.mark.anyio
async def test_delete_user_soft_deletes_account(client):
    created = (await create_user(client)).json()

    response = await client.delete(f"/api/users/{created['id']}")

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    get_response = await client.get(f"/api/users/{created['id']}")
    assert get_response.json()["is_active"] is False
