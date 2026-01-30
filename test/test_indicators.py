
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.llm_wrapper import LLMWrapper

def test_indicators():
    llm = LLMWrapper()
    
    print("\n--- Testing 'Get Technical Indicators' ---")
    query = "Check RSI and MACD for Tesla"
    print(f"Query: {query}")
    processed = llm.process_query(query)
    print(f"Result: {processed}")
    
    if processed['type'] == 'multiple_tool_calls':
         call = processed['calls'][0]
         if call['tool_name'] == 'get_technical_indicators':
             print("SUCCESS: Tool call correct (get_technical_indicators).")
             symbol = call['tool_args'].get('symbol')
             print(f"Symbol: {symbol}")
             assert 'TSLA' in symbol.upper() or 'TESLA' in symbol.upper()
         else:
             print(f"FAILURE: Unexpected tool name {call['tool_name']}")
             assert False
    else:
        print("FAILURE: Tool call incorrect type.")
        assert False

if __name__ == "__main__":
    test_indicators()
