import os
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv() # Load from .env file

# Configure API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class LLMWrapper:
    def __init__(self):
        if not GOOGLE_API_KEY:
             print("WARNING: GOOGLE_API_KEY not found. LLM features will fail.")
             
        # Define the tool for loan calculation
        auth_tool = {
            "function_declarations": [
                {
                    "name": "calculate_loan",
                    "description": "Calculate monthly loan payments and total interest. Use this tool when the user asks to calculate loan, mortgage, or interest payments.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "principal": {
                                "type": "NUMBER",
                                "description": "The loan amount (principal) in dollars."
                            },
                            "rate": {
                                "type": "NUMBER",
                                "description": "The annual interest rate as a percentage (e.g. 5.5 for 5.5%)."
                            },
                             "years": {
                                "type": "INTEGER",
                                "description": "The loan term in years."
                            }
                        },
                        "required": ["principal", "rate", "years"]
                    }
                },
                {
                    "name": "find_restaurants",
                    "description": "Find restaurants based on location and cuisine. Use this tool when the user asks to find a place to eat.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "location": {
                                "type": "STRING",
                                "description": "The city or area to search in (e.g. Seoul, Gangnam)."
                            },
                            "cuisine": {
                                "type": "STRING",
                                "description": "Key cuisine type (e.g. Italian, Korean, Sushi). Optional."
                            }
                        },
                        "required": ["location"]
                    }
                },
                {
                    "name": "reserve_table",
                    "description": "Make a table reservation at a restaurant.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "restaurant_name": {
                                "type": "STRING",
                                "description": "Name of the restaurant."
                            },
                            "date": {
                                "type": "STRING",
                                "description": "Date and time of reservation (e.g. 2024-05-20 19:00)."
                            },
                             "guests": {
                                "type": "INTEGER",
                                "description": "Number of guests."
                            }
                        },
                        "required": ["restaurant_name", "date", "guests"]
                    }
                },
                {
                    "name": "get_stock_chart",
                    "description": "Get the stock price history chart for a given symbol.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "symbol": {
                                "type": "STRING",
                                "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                            }
                        },
                        "required": ["symbol"]
                    }
                },
                {
                    "name": "get_stock_news",
                    "description": "Get recent news articles for a given stock symbol.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "symbol": {
                                "type": "STRING",
                                "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                            }
                        },
                        "required": ["symbol"]
                    }
                },
                {
                    "name": "search_products",
                    "description": "Search for products using Naver Shopping API. Use this when the user asks to find, search for, or buy products (e.g. 'search for bags', 'find me a laptop').",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {
                                "type": "STRING",
                                "description": "The product search query (e.g. 'slacks', 'gaming mouse')."
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[auth_tool],
            system_instruction="""You are a helpful assistant that uses tools to fulfill user requests.

IMPORTANT RULES:
1. When the user asks for something that can be done with a tool, ALWAYS call the tool immediately.
2. Do NOT ask clarifying questions - use reasonable defaults if optional parameters are not specified.
3. For restaurant searches: if cuisine is not specified, search for all types.
4. For stock queries: extract the stock symbol from the company name (e.g., Apple -> AAPL, Tesla -> TSLA, Nvidia -> NVDA).
5. Prefer action over conversation."""
        )
        self.chat = self.model.start_chat()

    def process_query(self, text: str) -> Dict[str, Any]:
        """
        Process the user query using Gemini.
        Returns a dict with:
        - 'type': 'tool_call' or 'text'
        - 'tool_name': (if tool_call)
        - 'tool_args': (if tool_call)
        - 'text': (if text)
        """
        try:
            response = self.chat.send_message(text)
            
            # Check for function calls across all parts
            tool_calls = []
            
            if response.parts:
                for part in response.parts:
                    if fn := part.function_call:
                        tool_calls.append({
                            "tool_name": fn.name,
                            "tool_args": dict(fn.args)
                        })
            
            if tool_calls:
                # Even if single call, we can use the list structure or return extracted single
                # But to support multi-intent, we return a special type
                return {
                    "type": "multiple_tool_calls",
                    "calls": tool_calls
                }
            else:
                return {
                    "type": "text",
                    "text": response.text
                }
                
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "type": "text",
                "text": f"Sorry, I encountered an error connecting to my brain. ({str(e)})"
            }

    def generate_commentary(self, symbol: str, current_price: float, price_change_pct: float = None) -> str:
        """
        Generate AI commentary about a stock based on its data.
        """
        try:
            # Use a simple model without tools for commentary generation
            commentary_model = genai.GenerativeModel(model_name='gemini-2.0-flash')
            
            prompt = f"""You are a helpful financial analyst assistant. Provide a brief, informative commentary about the stock {symbol}.
Current price: ${current_price:.2f}
{f"Recent price change: {price_change_pct:.1f}%" if price_change_pct else ""}

Guidelines:
- Keep your response concise (2-3 sentences max)
- Be informative but neutral (no financial advice)
- Mention any relevant context about the company
- Respond in Korean

Example format: "[Company name]는 [brief description]. 현재 가격은 [price context]."
"""
            response = commentary_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Commentary generation error: {e}")
            return ""

    async def generate_commentary_stream(self, symbol: str, current_price: float):
        """
        Stream AI commentary about a stock, yielding text chunks.
        """
        try:
            commentary_model = genai.GenerativeModel(model_name='gemini-2.0-flash')
            
            prompt = f"""You are a helpful financial analyst assistant. Provide a brief, informative commentary about the stock {symbol}.
Current price: ${current_price:.2f}

Guidelines:
- Keep your response concise (2-3 sentences max)
- Be informative but neutral (no financial advice)
- Mention any relevant context about the company
- Respond in Korean

Example format: "[Company name]는 [brief description]. 현재 가격은 [price context]."
"""
            response = commentary_model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            print(f"Streaming commentary error: {e}")
            yield f"(코멘터리 생성 중 오류 발생)"


