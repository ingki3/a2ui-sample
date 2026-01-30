
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.llm_wrapper import LLMWrapper

def test_stock_info():
    llm = LLMWrapper()
    
    print("\n--- Testing 'Get Stock Info' ---")
    query = "Analyze Apple stock and show me the profile"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")
    
    if processed['type'] == 'multiple_tool_calls':
         call = processed['calls'][0]
         if call['tool_name'] == 'get_stock_info':
             print("SUCCESS: Tool call correct (get_stock_info).")
             symbol = call['tool_args'].get('symbol')
             print(f"Symbol: {symbol}")
             assert symbol.upper() == 'AAPL' or 'APPLE' in symbol.upper() # LLM might output AAPL or Apple
         else:
             print(f"FAILURE: Unexpected tool name {call['tool_name']}")
             assert False
    else:
        print("FAILURE: Tool call incorrect type.")
        assert False

if __name__ == "__main__":
    test_stock_info()
