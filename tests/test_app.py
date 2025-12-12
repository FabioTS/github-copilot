"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, reset_activities):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, reset_activities):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_fields(self, reset_activities):
        """Test that activities have expected fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        assert "Chess Club" in activities_data
        assert "description" in activities_data["Chess Club"]
        assert "schedule" in activities_data["Chess Club"]
        assert "max_participants" in activities_data["Chess Club"]
        assert "participants" in activities_data["Chess Club"]
    
    def test_get_activities_participants_is_list(self, reset_activities):
        """Test that participants is a list"""
        response = client.get("/activities")
        activities_data = response.json()
        
        assert isinstance(activities_data["Chess Club"]["participants"], list)


class TestSignupForActivity:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds the participant"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants
    
    def test_signup_duplicate_returns_400(self, reset_activities):
        """Test that signing up twice returns 400 error"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 400
        assert "Already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, reset_activities):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_multiple_activities(self, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "alice@mergington.edu"
        
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        assert email in response.json()["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Test DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, reset_activities):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email not in participants
    
    def test_unregister_nonexistent_activity_returns_404(self, reset_activities):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_unregister_not_signed_up_returns_400(self, reset_activities):
        """Test that unregistering when not signed up returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_signup_after_unregister(self, reset_activities):
        """Test that a student can re-register after unregistering"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        # Re-register
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify re-registration
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestRootRoute:
    """Test root route"""
    
    def test_root_redirects(self, reset_activities):
        """Test that root route redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
