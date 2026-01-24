import os
from dotenv import load_dotenv
from llm_wrapper import LLMWrapper

# Load environment variables
load_dotenv()

def test_tool_selection():
    print("Initializing LLMWrapper...")
    llm = LLMWrapper()
    
    queries = [
        "가방 찾아줘",
        "노트북 검색해줘",
        "나이키 신발 사고 싶어"
    ]
    
    for q in queries:
        print(f"\nProcessing query: '{q}'")
        result = llm.process_query(q)
        
        if result['type'] == 'multiple_tool_calls':
            found = False
            for call in result['calls']:
                print(f"  Tool called: {call['tool_name']}")
                print(f"  Args: {call['tool_args']}")
                if call['tool_name'] == 'search_products':
                    found = True
            
            if found:
                print("  ✅ 'search_products' tool was selected.")
            else:
                print("  ❌ 'search_products' tool was NOT selected.")
        else:
            print(f"  ❌ No tool calls. Response type: {result['type']}")
            if 'text' in result:
                print(f"  Text: {result['text']}")

if __name__ == "__main__":
    test_tool_selection()
