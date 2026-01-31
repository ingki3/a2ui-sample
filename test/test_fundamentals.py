
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.llm_wrapper import LLMWrapper

def test_fundamentals():
    llm = LLMWrapper()
    
    print("\n--- Testing 'Get Company Fundamentals' ---")
    query = "Show me the financials and ownership of Apple"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")
    
    if processed['type'] == 'multiple_tool_calls':
         call = processed['calls'][0]
         if call['tool_name'] == 'get_company_fundamentals':
             print("SUCCESS: Tool call correct (get_company_fundamentals).")
             symbol = call['tool_args'].get('symbol')
             print(f"Symbol: {symbol}")
             assert 'AAPL' in symbol.upper() or 'APPLE' in symbol.upper()
         else:
             print(f"FAILURE: Unexpected tool name {call['tool_name']}")
             assert False
    else:
        print("FAILURE: Tool call incorrect type.")
        assert False

if __name__ == "__main__":
    test_fundamentals()
