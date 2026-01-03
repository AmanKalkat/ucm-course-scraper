from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


"""
Things we can test:
    whether the by prefix query actually gives a response that has
        said prefix
    credit parsing (single value and range)
"""

def test_nonexistent_course():
    response = client.get("/courses/code/CSE 300")
    assert response.status_code == 404
    assert response.json() == {"detail": "Course with code 'CSE 300' not found"}

# total courses currently: 8388
def test_all_courses():
    response = client.get("/courses")
    data = response.json()
    assert len(data) == 8388
