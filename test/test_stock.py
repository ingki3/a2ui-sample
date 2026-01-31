import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.llm_wrapper import LLMWrapper

def test_stock_chart():
    llm = LLMWrapper()
    
    # Test: Get Stock Chart
    print("\n--- Testing 'Get Stock Chart' ---")
    query = "Show me the stock chart for NVDA"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")
    
    if processed['type'] == 'tool_call' and processed['tool_name'] == 'get_stock_chart':
        print("SUCCESS: Tool call correct.")
    else:
        print("FAILURE: Tool call incorrect.")

if __name__ == "__main__":
    test_stock_chart()
