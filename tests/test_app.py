import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that /activities endpoint returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that /activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_activities_contain_required_fields(self):
        """Test that each activity contains required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_participants(self):
        """Test that some activities have participants"""
        response = client.get("/activities")
        activities = response.json()

        has_participants = any(
            len(activity["participants"]) > 0 for activity in activities.values()
        )
        assert has_participants


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student(self):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_student(self):
        """Test that duplicate signup returns 400 error"""
        email = "duplicate@mergington.edu"
        # First signup
        client.post("/activities/Basketball/signup?email=test.student@mergington.edu")
        # Try duplicate signup
        client.post(f"/activities/Basketball/signup?email={email}")
        response = client.post(f"/activities/Basketball/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/InvalidActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds participant to activity"""
        email = "participant.test@mergington.edu"
        activity = "Tennis"

        # Get initial participant count
        initial = client.get("/activities").json()[activity]["participants"]
        initial_count = len(initial)

        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

        # Verify participant was added
        updated = client.get("/activities").json()[activity]["participants"]
        assert len(updated) == initial_count + 1
        assert email in updated


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        email = "unregister.test@mergington.edu"
        activity = "Art Club"

        # First sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Then unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_non_participant(self):
        """Test that unregistering non-participant returns 400"""
        response = client.post(
            "/activities/Music Ensemble/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_invalid_activity(self):
        """Test unregister for non-existent activity returns 404"""
        response = client.post(
            "/activities/InvalidActivity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant from activity"""
        email = "removal.test@mergington.edu"
        activity = "Robotics Club"

        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        participants = client.get("/activities").json()[activity]["participants"]
        assert email in participants

        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        participants = client.get("/activities").json()[activity]["participants"]
        assert email not in participants


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects(self):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
