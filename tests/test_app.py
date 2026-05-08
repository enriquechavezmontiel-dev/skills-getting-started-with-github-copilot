import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture to provide a TestClient instance for testing the FastAPI app."""
    return TestClient(app)


def test_get_activities(client):
    """Test GET /activities endpoint returns all activities."""
    # Arrange - No special setup needed

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Based on the hardcoded activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Verify structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client):
    """Test successful signup for an activity."""
    # Arrange
    activity_name = "Basketball Team"  # Starts with empty participants
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    # Verify the participant was added
    response_check = client.get("/activities")
    data = response_check.json()
    assert email in data[activity_name]["participants"]


def test_signup_for_activity_duplicate(client):
    """Test signup fails when student is already signed up."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already in participants

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}


def test_signup_for_activity_invalid(client):
    """Test signup fails for non-existent activity."""
    # Arrange
    activity_name = "NonExistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_from_activity_success(client):
    """Test successful removal of a participant from an activity."""
    # Arrange
    activity_name = "Programming Class"
    email = "emma@mergington.edu"  # Already in participants

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}

    # Verify the participant was removed
    response_check = client.get("/activities")
    data = response_check.json()
    assert email not in data[activity_name]["participants"]


def test_remove_from_activity_invalid_activity(client):
    """Test removal fails for non-existent activity."""
    # Arrange
    activity_name = "NonExistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_from_activity_not_signed_up(client):
    """Test removal fails when student is not signed up."""
    # Arrange
    activity_name = "Art Club"  # Has empty participants initially
    email = "notsignedup@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found in this activity"}


def test_data_integrity_multiple_operations(client):
    """Test data integrity across multiple signup and removal operations."""
    # Arrange
    activity_name = "Soccer Club"
    email1 = "student1@mergington.edu"
    email2 = "student2@mergington.edu"

    # Act - Signup two students
    response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email1})
    response2 = client.post(f"/activities/{activity_name}/signup", params={"email": email2})

    # Assert signups successful
    assert response1.status_code == 200
    assert response2.status_code == 200

    # Verify both added
    response_check = client.get("/activities")
    data = response_check.json()
    assert email1 in data[activity_name]["participants"]
    assert email2 in data[activity_name]["participants"]
    assert len(data[activity_name]["participants"]) == 2

    # Act - Remove one student
    response_remove = client.delete(f"/activities/{activity_name}/participants/{email1}")

    # Assert removal successful
    assert response_remove.status_code == 200

    # Verify final state
    response_final = client.get("/activities")
    data_final = response_final.json()
    assert email1 not in data_final[activity_name]["participants"]
    assert email2 in data_final[activity_name]["participants"]
    assert len(data_final[activity_name]["participants"]) == 1