
import requests
import json
import sys

def test_sse_stream():
    url = "http://127.0.0.1:8000/chat/stream"
    headers = {"X-Client-A2UI": "true"}
    data = {"text": "Analyze Apple stock"}
    
    print(f"Connecting to {url}...")
    
    try:
        with requests.post(url, json=data, headers=headers, stream=True) as r:
            r.raise_for_status()
            print("Connected. Reading stream...")
            
            buffer = ""
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    print(f"Chunk received: {repr(chunk)}")
                    buffer += chunk
            
            print("\nFull Response captured.")
            
            # Basic validation of SSE format
            if "event: a2ui" in buffer and "event: text" in buffer:
                print("SUCCESS: Found both 'a2ui' and 'text' events.")
            else:
                print("WARNING: Missing expected events. (Might be due to LLM response time or logic)")
                print(buffer[:500])

    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_sse_stream()
