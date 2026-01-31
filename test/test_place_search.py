import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.llm_wrapper import LLMWrapper

def test_restaurant_finder():
    llm = LLMWrapper()
    
    # Test 1: Find Restaurants (should map to find_places)
    print("\n--- Testing 'Find Restaurants' -> 'find_places' ---")
    query = "Find Italian restaurants in Downtown"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")
    
    # Note: process_query returns {type: multiple_tool_calls, calls: [...]}
    if processed['type'] == 'multiple_tool_calls':
         call = processed['calls'][0]
         if call['tool_name'] == 'find_places':
             print("SUCCESS: Tool call correct (find_places).")
             assert call['tool_args'].get('keyword') in ['Italian', 'Italian restaurants', 'Italian restaurant']
             assert 'Downtown' in call['tool_args'].get('location')
         else:
             print(f"FAILURE: Unexpected tool name {call['tool_name']}")
             assert False
    else:
        print("FAILURE: Tool call incorrect type.")
        assert False

    # Test 2: Find Places (Generic)
    print("\n--- Testing 'Find Hospitals' -> 'find_places' ---")
    query = "Find hospitals in Gangnam"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")

    if processed['type'] == 'multiple_tool_calls':
         call = processed['calls'][0]
         if call['tool_name'] == 'find_places':
             print("SUCCESS: Tool call correct (find_places).")
             assert 'hospital' in call['tool_args'].get('keyword').lower()
             assert 'Gangnam' in call['tool_args'].get('location')
         else:
             print(f"FAILURE: Unexpected tool name {call['tool_name']}")
             assert False
    else:
        print("FAILURE: Tool call incorrect type.")
        assert False

    # Test 3: Reserve Table (Unchanged)
    print("\n--- Testing 'Reserve Table' ---")
    query = "Book a table for 2 at Bella Italia on 2024-05-20 at 7pm"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    
    if processed['type'] == 'multiple_tool_calls':
         call = processed['calls'][0]
         if call['tool_name'] == 'reserve_table':
             print("SUCCESS: Tool call correct (reserve_table).")
         else:
             print(f"FAILURE: Unexpected tool name {call['tool_name']}")
             assert False
    else:
        print("FAILURE: Tool call incorrect type.")
        assert False

if __name__ == "__main__":
    test_restaurant_finder()
