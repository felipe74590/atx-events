from datetime import datetime
import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from src.api.main_api import app
from src.data.db_helper import get_current_active_user, get_session
from src.data.db_models import User, Event, UserEventsSaved


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Mock the form data class to simulate OAuth2PasswordRequestForm input
class MockOAuth2PasswordRequestForm:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


# Test function to handle the login endpoint
def test_login_for_access_token_success(client):
    mock_user = User(id=1, user_name="testuser", password_hash="hashed_password")
    mock_access_token = "mocked_access_token"

    with patch("src.api.main_api.authenticate_user", return_value=mock_user):
        with patch("src.api.main_api.create_access_token", return_value=mock_access_token):
            form_data = MockOAuth2PasswordRequestForm(username="testuser", password="testpassword")

            response = client.post("/token", data={"username": form_data.username, "password": form_data.password})

            assert response.status_code == 200

            token_data = response.json()
            assert "access_token" in token_data
            assert token_data["access_token"] == mock_access_token
            assert token_data["token_type"] == "bearer"


def test_login_for_access_token_failure(client):
    # Mock authenticate_user to return None (invalid user)
    with patch("src.api.main_api.authenticate_user", return_value=None):
        form_data = MockOAuth2PasswordRequestForm(username="invaliduser", password="wrongpassword")
        response = client.post("/token", data={"username": form_data.username, "password": form_data.password})

        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}


def mock_get_current_active_user():
    return User(id=1, user_name="testuser", email="test@gmail.com", password="testpassword", hashed_password="xxxxx---")


def mock_execute_query(session, user_id):
    mock_query_result = MagicMock()
    event_1 = Event(id=1, title="Event 1", category=None, event_link=None, venue="Here")
    mock_query_result.all.return_value = [event_1]
    return mock_query_result


def test_get_saved_events(client):
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with patch("src.api.main_api.get_current_active_user", mock_get_current_active_user):
        with patch("sqlmodel.Session.exec") as mock_exec:
            mock_exec.return_value = mock_execute_query(None, 1)
            response = client.get("/me/events/saved")
            print(response)
            assert response.status_code == 200
            events = response.json()
            assert len(events) == 1
            assert events[0]["title"] == "Event 1"


def test_get_attended_events(client):
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with patch("src.api.main_api.get_current_active_user", mock_get_current_active_user):
        with patch("sqlmodel.Session.exec") as mock_exec:
            mock_exec.return_value = mock_execute_query(None, 1)
            response = client.get("/me/events/attended")

            assert response.status_code == 200
            events = response.json()
            assert len(events) == 1
            assert events[0]["title"] == "Event 1"


def test_save_event_success(client):
    save_event_request = {"event_id": 101}
    mock_saved_event = UserEventsSaved(user_id=1, event_id=101)
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

    with (
        patch("sqlmodel.Session.exec") as mock_exec,
        patch("sqlmodel.Session.commit"),
        patch("sqlmodel.Session.refresh") as mock_refresh,
    ):
        mock_exec.return_value.first.side_effect = lambda: None
        mock_refresh.return_value = mock_saved_event

        response = client.post("/me/events/saved", json=save_event_request)

        assert response.status_code == 200

        response_data = response.json()
        assert response_data["user_id"] == 1
        assert response_data["event_id"] == 101
    # Clear the overrides to avoid affecting other tests
    app.dependency_overrides.clear()


def test_save_event_already_saved(client):
    save_event_request = {"event_id": 101}
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with patch("sqlmodel.Session.exec") as mock_exec:
        mock_exec.return_value.first.return_value = UserEventsSaved(user_id=1, event_id=101)

        response = client.post("/me/events/saved", json=save_event_request)

        assert response.status_code == 409
        assert response.json()["detail"] == "Event is already saved for this user."


def test_get_me_success(client):
    mock_user = User(id=1, user_name="testuser", email="testuser@example.com")

    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with patch("sqlmodel.Session.query") as mock_query:
        mock_query.return_value.filter.return_value.first.return_value = mock_user

        response = client.get("/users/me/")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["user_name"] == "testuser"
        assert response_data["email"] == "testuser@example.com"


# Test when the user is not found
def test_get_me_not_found(client):
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with patch("sqlmodel.Session.query") as mock_query:
        mock_query.return_value.filter.return_value.first.return_value = None

        response = client.get("/users/me/")

        assert response.status_code == 404
        assert response.json()["detail"] == "User email test@gmail.com with username testuser not found"


def mock_event_data():
    return


def insert_mock_events(session: Session):
    events = [
        Event(id=1, title="party", start_datetime=datetime(2024, 10, 25, 10, 0), venue="Venue A", category="Music"),
        Event(id=2, title="concert", start_datetime=datetime(2024, 10, 26, 10, 0), venue="Venue B", category="Art"),
    ]
    session.add_all(events)
    session.commit()


def test_search_events_success(client, session):
    # Mock the session and query response
    insert_mock_events(session)

    from_date = datetime(2024, 10, 24)
    to_date = datetime(2024, 10, 27)
    venue_keyword = "Venue"
    category_keyword = "Music"

    response = client.get(
        "/search_events/",
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "venue_keyword": venue_keyword,
            "category_keyword": category_keyword,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_events": 1,
        "events": [
            {
                "id": 1,
                "start_datetime": "2024-10-25T10:00:00",
                "venue": "Venue A",
                "category": "Music",
                "event_link": None,
                "title": "party",
            },
        ],
    }


def test_search_events_invalid_date_range(client):
    from_date = datetime(2024, 10, 26)
    to_date = datetime(2024, 10, 25)

    response = client.get(
        "/search_events/",
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "from_date must be before to_date"


def test_search_events_missing_from_date(client):
    to_date = datetime(2024, 10, 25)

    response = client.get(
        "/search_events/",
        params={
            "to_date": to_date.isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "must provide a from_date if to_date is provided."


def test_search_events_no_results(client):
    from_date = datetime(2024, 10, 24)
    to_date = datetime(2024, 10, 27)

    response = client.get(
        "/search_events/",
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"total_events": 0, "events": []}


class CustomTestClient(TestClient):
    def delete_with_payload(self, url: str, **kwargs):
        return self.request(method="DELETE", url=url, **kwargs)


def test_remove_saved_event_success():
    save_event_request = {"event_id": 101}
    mock_saved_event = UserEventsSaved(user_id=1, event_id=101)

    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with (
        patch("sqlmodel.Session.exec") as mock_exec,
        patch("sqlmodel.Session.delete") as mock_delete,
        patch("sqlmodel.Session.commit"),
    ):
        # Mock the query to return the saved event (meaning the event is currently saved)
        mock_exec.return_value.first.return_value = mock_saved_event

        mock_delete.return_value = None
        client = CustomTestClient(app)
        response = client.delete_with_payload("/me/events/saved", json=save_event_request)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["user_id"] == 1
        assert response_data["event_id"] == 101


def test_remove_saved_event_not_found():
    save_event_request = {"event_id": 101}
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with patch("sqlmodel.Session.exec") as mock_exec:
        # Mock the query to return None (meaning the event is not saved for the user)
        mock_exec.return_value.first.return_value = None

        client = CustomTestClient(app)
        response = client.delete_with_payload("/me/events/saved", json=save_event_request)

        assert response.status_code == 404
        assert response.json()["detail"] == "Event is not currently saved for this user."
