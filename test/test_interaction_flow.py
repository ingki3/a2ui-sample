
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.agent import StockService, RestaurantService
from app.services.llm_wrapper import LLMWrapper
from app.schemas.models import A2UIResponse

async def test_flow():
    print("\n--- Testing Service Context Return ---")
    stock_service = StockService()
    
    # Test get_stock_info
    print("1. Calling get_stock_info('AAPL')...")
    res, context = stock_service.get_stock_info("AAPL")
    
    if isinstance(res, A2UIResponse):
        print("SUCCESS: Received A2UIResponse")
    else:
        print(f"FAILURE: Received {type(res)}")
        
    if isinstance(context, str) and len(context) > 0:
        print(f"SUCCESS: Received Context: {context[:50]}...")
    else:
        print(f"FAILURE: Invalid Context: {context}")

    # Test get_technical_indicators
    print("\n2. Calling get_technical_indicators('AAPL')...")
    res, context = stock_service.get_technical_indicators("AAPL")
    print(f"Context: {context}")

    print("\n--- Testing LLM Answer Generation ---")
    llm = LLMWrapper()
    query = "Analyze Apple's financials and technicals."
    context_list = [
        "Company Profile for AAPL: Apple Inc. (Consumer Electronics). Market Cap $3.4T.",
        "Fundamentals: Revenue $394B, Net Income $99B. Analyst Ratings: Buy.",
        "Technical Indicators: RSI 55 (Neutral), MACD Bullish Trend."
    ]
    
    print(f"Query: {query}")
    print(f"Context Items: {len(context_list)}")
    print("Streaming Answer:")
    
    try:
        async for chunk in llm.answer_with_context_stream(query, context_list):
            print(chunk, end="", flush=True)
        print("\n\nSUCCESS: Stream completed.")
    except Exception as e:
        print(f"\nFAILURE: Stream error: {e}")

if __name__ == "__main__":
    asyncio.run(test_flow())
