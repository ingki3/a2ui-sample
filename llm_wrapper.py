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
                }
            ]
        }
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[auth_tool]
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
