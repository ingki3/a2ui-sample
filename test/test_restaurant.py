import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.llm_wrapper import LLMWrapper

def test_restaurant_finder():
    llm = LLMWrapper()
    
    # Test 1: Find Restaurants
    print("\n--- Testing 'Find Restaurants' ---")
    query = "Find Italian restaurants in Downtown"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")
    
    if processed['type'] == 'tool_call' and processed['tool_name'] == 'find_restaurants':
        print("SUCCESS: Tool call correct.")
    else:
        print("FAILURE: Tool call incorrect.")

    # Test 2: Reserve Table
    print("\n--- Testing 'Reserve Table' ---")
    query = "Book a table for 2 at Bella Italia on 2024-05-20 at 7pm"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")

    if processed['type'] == 'tool_call' and processed['tool_name'] == 'reserve_table':
        print("SUCCESS: Tool call correct.")
    else:
         print("FAILURE: Tool call incorrect.")

if __name__ == "__main__":
    test_restaurant_finder()
