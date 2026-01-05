import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_nonexistent_course():
    response = client.get("/courses/code/CSE 300")
    assert response.status_code == 404
    assert response.json() == {"detail": "Course with code 'CSE 300' not found"}

# total courses currently: 8388
def test_all_courses():
    response = client.get("/courses")
    data = response.json()
    assert len(data) == 8388

def test_prefix_query():
    response = client.get("/courses?course_prefix=CS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(course["course_code"].startswith("CS") for course in data), "Not all courses have CS prefix"

def test_credit_parsing():
    # test course with single credit value
    response_single = client.get("/courses/code/CSE 030")
    assert response_single.status_code == 200
    single_data = response_single.json()[0]
    assert isinstance(single_data["credits"], int)
    assert single_data["credits"] > 0

    # test course with credit range
    response_range = client.get("/courses/code/CSE 095")
    assert response_range.status_code == 200
    range_data = response_range.json()[0]
    assert isinstance(range_data["credits"], list)
    assert len(range_data["credits"]) > 0
    assert all(isinstance(c, int) and c > 0 for c in range_data["credits"])

def test_prereq_contains():
    response = client.get("/courses/code/CSE 030")
    assert response.status_code == 200
    data = response.json()[0]
    assert data["prereqs"][0] == "CSE 024"