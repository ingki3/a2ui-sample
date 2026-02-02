import os
import logging
import asyncio
from google import genai
from google.genai import types
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()  # Load from .env file

# Configure API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

class LLMWrapper:
    def __init__(self):
        if not GOOGLE_API_KEY:
            print("WARNING: GOOGLE_API_KEY not found. LLM features will fail.")
        
        # Initialize the client
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # ========== STOCK DOMAIN TOOLS ==========
        self.stock_tools_declarations = [
            {
                "name": "get_stock_chart",
                "description": "Provide stock price history chart with moving averages (MA20, MA60, MA120) and current price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_stock_news",
                "description": "Provide recent news articles and headlines for a given stock symbol.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_stock_info",
                "description": "Provide company profile including business summary, market cap, sector, and key financials.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_technical_indicators",
                "description": "Provide technical indicators (RSI, MACD) for a given stock symbol.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_company_fundamentals",
                "description": "Provide detailed fundamental data including financial history (revenue, net income), shareholder structure, and analyst ratings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_stock_dividends",
                "description": "Provide dividend history and yield information for a stock.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_stock_holders",
                "description": "Provide information about major holders, institutional ownership, and insider holdings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_stock_calendar",
                "description": "Provide upcoming events including earnings dates and ex-dividend dates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                        }
                    },
                    "required": ["symbol"]
                }
            }
        ]
        
        # ========== LIFE DOMAIN TOOLS ==========
        self.life_tools_declarations = [
            {
                "name": "calculate_loan",
                "description": "Provide monthly loan payment calculations including principal, interest, and total cost.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "principal": {
                            "type": "number",
                            "description": "The loan amount (principal) in dollars."
                        },
                        "rate": {
                            "type": "number",
                            "description": "The annual interest rate as a percentage (e.g. 5.5 for 5.5%)."
                        },
                        "years": {
                            "type": "integer",
                            "description": "The loan term in years."
                        }
                    },
                    "required": ["principal", "rate", "years"]
                }
            },
            {
                "name": "find_places",
                "description": "Provide a list of places (restaurants, cafes, hospitals, banks, stores, etc.) based on location and keyword.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city or area to search in (e.g. Seoul, Gangnam)."
                        },
                        "keyword": {
                            "type": "string",
                            "description": "The type of place or specific keyword (e.g. restaurant, Apple Store, hospital, pharmacy). Optional."
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "reserve_table",
                "description": "Provide table reservation confirmation at a specified restaurant.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_name": {
                            "type": "string",
                            "description": "Name of the restaurant."
                        },
                        "date": {
                            "type": "string",
                            "description": "Date and time of reservation (e.g. 2024-05-20 19:00)."
                        },
                        "guests": {
                            "type": "integer",
                            "description": "Number of guests."
                        }
                    },
                    "required": ["restaurant_name", "date", "guests"]
                }
            },
            {
                "name": "search_products",
                "description": "Search for products and provide shopping results including product name, price, and store name from Naver Shopping. Use this when users ask about product prices, want to buy something, or compare shopping options.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The product search query in Korean (e.g. '애플 아이폰', '삼성 갤럭시', '나이키 운동화')."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        # Create tools configs
        self.stock_tools = types.Tool(function_declarations=self.stock_tools_declarations)
        self.life_tools = types.Tool(function_declarations=self.life_tools_declarations)
        
        # System prompts for each domain
        self.stock_system_prompt = """You are a financial assistant specialized in stock market analysis.

IMPORTANT RULES:
1. If the query contains ANY stock-related keywords (주가, stock, chart, 차트, 투자, investment, 주식), call the appropriate stock tools.
2. Focus ONLY on the stock-related part of the query. Ignore requests about locations, restaurants, or other non-financial topics.
3. Extract stock symbols from company names (e.g., Apple -> AAPL, Tesla -> TSLA, Starbucks -> SBUX, Samsung -> 005930.KS).
4. If the user explicitly requests specific information (e.g., "chart only"), provide ONLY that - do not call unnecessary tools.
5. Select only the tools appropriate for answering the stock-related part of the question."""

        self.life_system_prompt = """You are a lifestyle assistant helping with everyday tasks.

IMPORTANT RULES:
1. If the query contains keywords like "가격", "price", "구매", "buy", "쇼핑", call `search_products` for product searches.
2. If the query is ONLY about stocks (주가, stock chart, 투자) with no shopping/product context, return NO tool calls.
3. For place searches: understand context (e.g., "애플 매장" means Apple Store location).
4. IMPORTANT: Keep Korean text AS-IS in tool arguments. Do NOT translate Korean to English. (e.g., location="서울", keyword="애플 매장")
5. If query mentions both "가격" (product price) AND "주가" (stock price), call `search_products` for the product part.
6. Select only the tools appropriate for answering the lifestyle-related question."""

    def _extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fn = part.function_call
                    tool_calls.append({
                        "tool_name": fn.name,
                        "tool_args": dict(fn.args)
                    })
        return tool_calls

    def process_query_for_stock(self, text: str) -> List[Dict[str, Any]]:
        """
        Process query for stock-related tools only.
        Returns list of tool calls (may be empty if not stock-related).
        """
        try:
            user_content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
            
            config = types.GenerateContentConfig(
                tools=[self.stock_tools],
                system_instruction=self.stock_system_prompt
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[user_content],
                config=config
            )
            
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                logger.info(f"[STOCK] Tool calls: {[c['tool_name'] for c in tool_calls]}")
            return tool_calls
            
        except Exception as e:
            logger.error(f"[STOCK] Error: {e}", exc_info=True)
            return []

    def process_query_for_life(self, text: str) -> List[Dict[str, Any]]:
        """
        Process query for life-related tools only.
        Returns list of tool calls (may be empty if not life-related).
        """
        try:
            user_content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
            
            config = types.GenerateContentConfig(
                tools=[self.life_tools],
                system_instruction=self.life_system_prompt
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[user_content],
                config=config
            )
            
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                logger.info(f"[LIFE] Tool calls: {[c['tool_name'] for c in tool_calls]}")
            return tool_calls
            
        except Exception as e:
            logger.error(f"[LIFE] Error: {e}", exc_info=True)
            return []

    def process_query(self, text: str) -> Dict[str, Any]:
        """
        Process the user query by calling both domain-specific functions
        and aggregating the results.
        """
        import concurrent.futures
        
        # Call both functions in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            stock_future = executor.submit(self.process_query_for_stock, text)
            life_future = executor.submit(self.process_query_for_life, text)
            
            stock_calls = stock_future.result()
            life_calls = life_future.result()
        
        # Aggregate tool calls
        all_tool_calls = stock_calls + life_calls
        
        if all_tool_calls:
            logger.info(f"[AGGREGATED] Total {len(all_tool_calls)} tool call(s): {[c['tool_name'] for c in all_tool_calls]}")
            return {
                "type": "multiple_tool_calls",
                "calls": all_tool_calls
            }
        else:
            # No tools called - generate text response
            logger.warning(f"No tools called for query: {text[:100]}")
            return {
                "type": "text",
                "text": "죄송합니다, 해당 질문에 대한 도구를 찾지 못했습니다."
            }

    def generate_commentary(self, symbol: str, current_price: float, price_change_pct: float = None) -> str:
        """
        Generate AI commentary about a stock based on its data.
        """
        try:
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
            response = self.client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt
            )
            return response.text.strip() if response.text else ""
        except Exception as e:
            logger.error(f"Commentary generation error: {e}")
            return ""

    async def generate_commentary_stream(self, symbol: str, current_price: float):
        """
        Stream AI commentary about a stock, yielding text chunks.
        """
        try:
            prompt = f"""You are a helpful financial analyst assistant. Provide a brief, informative commentary about the stock {symbol}.
Current price: ${current_price:.2f}

Guidelines:
- Keep your response concise (2-3 sentences max)
- Be informative but neutral (no financial advice)
- Mention any relevant context about the company
- Respond in Korean

Example format: "[Company name]는 [brief description]. 현재 가격은 [price context]."
"""
            # Use streaming with the new API
            for chunk in self.client.models.generate_content_stream(
                model='gemini-3-flash-preview',
                contents=prompt
            ):
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Streaming commentary error: {e}")
            yield f"(코멘터리 생성 중 오류 발생)"

    async def answer_with_context_stream(self, user_query: str, context_items: list):
        """
        Generate a final answer based on the user query and collected context.
        """
        try:
            context_str = "\n".join(f"- {c}" for c in context_items)
            
            prompt = f"""You are a helpful assistant.
User Question: {user_query}

Data Collected from Tools:
{context_str}

Please provide a helpful, detailed answer to the user's question based on the data above.
Respond in Korean.
"""
            for chunk in self.client.models.generate_content_stream(
                model='gemini-3-flash-preview',
                contents=prompt
            ):
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            yield f"(답변 생성 중 오류 발생: {e})"
