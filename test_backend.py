from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_text_response():
    response = client.post("/chat", json={"text": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "text"
    print("Text response test passed")

def test_a2ui_response():
    # Simulate A2UI client
    response = client.post("/chat", json={"text": "Calculate loan for 10000"}, headers={"X-Client-A2UI": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "a2ui"
    assert "surfaceUpdate" in data["data"]
    assert len(data["data"]["surfaceUpdate"]["components"]) > 0
    print("A2UI response test passed")

def test_recalculate_action():
    # Simulate recalculate action
    context = {
        "principal": "50000",
        "annualRate": "4.5",
        "years": "10"
    }
    response = client.post("/chat", json={"text": "recalculate", "client_context": context}, headers={"X-Client-A2UI": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "a2ui"
    # Verify values in data model/response if possible, but structure check is good enough for now
    print("Recalculate action test passed")

def test_shopping_response():
    # Simulate shopping query
    response = client.post("/chat", json={"text": "find me some nice shoes"}, headers={"X-Client-A2UI": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "a2ui"
    assert "surfaceUpdate" in data["data"]
    # Check for a component ID that contains "item_col"
    component_ids = [comp["id"] for comp in data["data"]["surfaceUpdate"]["components"]]
    assert any("item_col" in comp_id for comp_id in component_ids)
    print("Shopping response test passed")

if __name__ == "__main__":
    try:
        test_text_response()
        test_a2ui_response()
        test_recalculate_action()
        test_shopping_response()
        print("All tests passed!")
    except Exception as e:
        import traceback
        print(f"Test failed: {e}")
        traceback.print_exc()
        exit(1)
