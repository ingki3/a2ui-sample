import requests
import os

# Note: This script assumes the server is running on localhost:8000 and GOOGLE_API_KEY is set in the server's environment.
# You can run this script to sanity check the LLM integration if you have the key locally too (though the server handles the key).

def test_llm_query():
    print("Testing Natural Language Query...")
    query = "I want to calculate a loan for $25000 with 4.2% interest over 15 years."
    try:
        response = requests.post("http://localhost:8000/chat", json={"text": query}, headers={"X-Client-A2UI": "true"})
        data = response.json()
        
        if data.get("kind") == "a2ui":
            print("SUCCESS: LLM triggered A2UI response.")
            print("Surface Components:", len(data["data"]["surfaceUpdate"]["components"]))
        else:
            print("FAILURE: LLM did not trigger A2UI. Response:", data)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm_query()
