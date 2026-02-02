import math
from typing import List, Dict, Any, Union, Tuple
from app.schemas.models import (
    A2UIResponse, A2UIData, SurfaceUpdate, ComponentEntry, ComponentType,
    TextComponent, TextContent, TextFieldComponent, ButtonComponent, Action,
    ActionContext, ColumnComponent, ColumnChildren, DataModelUpdate,
    DataModelContents, DataValue, BeginRendering, TextResponse
)

class LoanCalculatorService:
    def calculate_loan(self, principal: float, annual_rate: float, years: int, is_ui_mode: bool = False) -> Union[A2UIResponse, TextResponse]:
        print(f"Calculating loan: ${principal}, {annual_rate}% APR, {years} years")


        # Loan calculation
        monthly_rate = annual_rate / 100 / 12
        months = years * 12
        if monthly_rate > 0:
            monthly_payment = principal * (monthly_rate * math.pow(1 + monthly_rate, months)) / (math.pow(1 + monthly_rate, months) - 1)
        else:
             monthly_payment = principal / months
        
        total_payment = monthly_payment * months
        total_interest = total_payment - principal

        if is_ui_mode:
            context = f"Loan Calculation: Principal ${principal}, Rate {annual_rate}%, {years} Years. Monthly: ${monthly_payment:.2f}. Total Interest: ${total_interest:.2f}."
            return self.create_loan_result_ui(principal, annual_rate, years, monthly_payment, total_payment, total_interest), context
        else:
            return TextResponse(text=f"Monthly Payment: ${monthly_payment:.2f}, Total Interest: ${total_interest:.2f}"), f"Loan calculated: Monthly ${monthly_payment:.2f}."

    def create_loan_result_ui(self, principal, rate, years, monthly, total, interest) -> A2UIResponse:
        print("create_loan_result_ui called.") # Added for debugging
        from jinja2 import Environment, FileSystemLoader
        import json
        import os
        import uuid

        # Ensure we have a UID for namespacing even for single loan calc
        uid = str(uuid.uuid4())[:8]
        
        # Note: In a real app, Environment should be created once at module level or dependency injected
        prompts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
        env = Environment(loader=FileSystemLoader(prompts_dir))
        template = env.get_template("loan_result.json.j2")
        
        # Render template with variables
        rendered_json_str = template.render(
            principal=principal,
            rate=rate,
            years=years,
            monthly=monthly,
            total=total,
            interest=interest,
            uid=uid
        )
        
        # Parse JSON and validate with Pydantic model
        try:
            data_dict = json.loads(rendered_json_str)
            return A2UIResponse(data=A2UIData(**data_dict))
        except Exception as e:
            print(f"Template Rendering Error: {e}")
            # Fallback text
            return TextResponse(text=f"Error rendering UI: {e}")

class RestaurantService:
    NAVER_CLIENT_ID = "QVYRUg158Y_uP0qaUiXt"
    NAVER_CLIENT_SECRET = "xLOYCyFquE"
    
    def _search_naver_local(self, query: str, display: int = 5) -> list:
        """
        Search restaurants using Naver Local Search API.
        Returns a list of restaurant dictionaries.
        """
        import httpx
        import xml.etree.ElementTree as ET
        from urllib.parse import quote
        
        url = f"https://openapi.naver.com/v1/search/local.xml?query={quote(query)}&display={display}&start=1&sort=random"
        
        headers = {
            "X-Naver-Client-Id": self.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": self.NAVER_CLIENT_SECRET
        }
        
        try:
            response = httpx.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.text)
            channel = root.find("channel")
            
            places = []
            for idx, item in enumerate(channel.findall("item")):
                # Clean HTML tags from title
                title = item.find("title").text or ""
                title = title.replace("<b>", "").replace("</b>", "")
                
                category = item.find("category").text or ""
                address = item.find("address").text or ""
                road_address = item.find("roadAddress").text or ""
                
                # Get map coordinates (Naver uses WGS84 * 10^7 format)
                mapx = item.find("mapx").text or "0"
                mapy = item.find("mapy").text or "0"
                
                # Convert Naver coordinates to standard lat/lng
                # Naver's mapx/mapy are in WGS84 but scaled/formatted differently
                # They appear to be in KATEC or similar - need to convert
                # For Google Maps, we'll use the coordinates directly as they're close enough
                lng = float(mapx) / 10000000 if len(mapx) > 6 else float(mapx)
                lat = float(mapy) / 10000000 if len(mapy) > 6 else float(mapy)
                
                places.append({
                    "id": f"naver_{idx}",
                    "name": title,
                    "category": category.split(">")[-1] if ">" in category else category,
                    "rating": 4.5,  # Naver API doesn't provide ratings
                    "location": road_address or address,
                    "address": address,
                    "road_address": road_address,
                    "lat": lat,
                    "lng": lng,
                    "map_url": f"https://www.google.com/maps?q={lat},{lng}"
                })
            
            return places
            
        except Exception as e:
            print(f"Naver API Error: {e}")
            return []
    
    def find_places(self, location: str, keyword: str = None) -> Union[A2UIResponse, TextResponse]:
        print(f"Finding {keyword or 'places'} in {location}")
        
        # Build search query - keep original language from user
        # The LLM may translate to English, so we need to handle both
        if keyword:
            # Try direct query first
            query = f"{location} {keyword}"
        else:
            query = f"{location} 가볼만한곳"
        
        # Call Naver API
        places = self._search_naver_local(query, display=5)
        
        if not places:
            print("No results from Naver API, using fallback mock data")
            # Use keyword for fallback data
            fallback_name = f"{keyword or '장소'} in {location}" if keyword else f"Place in {location}"
            places = [
                {
                    "id": "p1",
                    "name": fallback_name,
                    "category": keyword or "Place",
                    "rating": 4.5,
                    "location": location,
                    "lat": 37.5665,
                    "lng": 126.9780,
                    "map_url": "https://www.google.com/maps?q=37.5665,126.9780"
                }
            ]

        import os
        context = f"Found {len(places)} places in {location} for keyword '{keyword}'. Top results: " + ", ".join([p['name'] for p in places[:3]])
        maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        return self._render_template("place_list.json.j2", {
            "places": places, 
            "location": location,
            "keyword": keyword,
            "maps_api_key": maps_api_key
        }), context

    def reserve_table(self, restaurant_name: str, date: str, guests: int) -> Union[A2UIResponse, TextResponse]:
        context = f"Reservation confirmed at {restaurant_name} for {guests} guests on {date}."
        return self._render_template("reservation_confirmed.json.j2", {
            "restaurant_name": restaurant_name,
            "date": date,
            "guests": guests
        }), context
    
    def _render_template(self, template_name: str, context: Dict[str, Any], uid: str = None) -> A2UIResponse:
        from jinja2 import Environment, FileSystemLoader
        import json
        import uuid
        import os
        
        # Generate a short random UID if not provided to ensure namespacing
        if not uid:
             uid = str(uuid.uuid4())[:8]

        prompts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
        env = Environment(loader=FileSystemLoader(prompts_dir))
        template = env.get_template(template_name)
        
        # Inject uid into context
        context['uid'] = uid
        
        rendered_json_str = template.render(**context)

        try:
            data_dict = json.loads(rendered_json_str)
            print(f"Template rendered successfully for {template_name}")
            result = A2UIResponse(data=A2UIData(**data_dict))
            print(f"A2UIResponse created: kind={result.kind}")
            return result
        except Exception as e:
            print(f"Template Rendering Error for {template_name}: {e}")
            print(f"Rendered JSON (first 500 chars): {rendered_json_str[:500]}")
            return TextResponse(text=f"Error rendering UI: {e}")

class StockService(RestaurantService):
    def get_stock_chart(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        import pandas as pd
        
        print(f"Fetching stock chart for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 1 year history
            hist = ticker.history(period="1y")
            
            if hist.empty:
                 return TextResponse(text=f"No data found for {symbol}")

            # Calculate moving averages
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            hist['MA60'] = hist['Close'].rolling(window=60).mean()
            hist['MA120'] = hist['Close'].rolling(window=120).mean()

            # Prepare data for ChartComponent (native rendering)
            prices = []
            ma20 = []
            ma60 = []
            ma120 = []
            
            for index, row in hist.iterrows():
                time_str = index.strftime("%Y-%m-%d")
                prices.append({
                    "time": time_str,
                    "value": float(row['Close'])
                })
                # Only add MA values if they exist (not NaN)
                if not pd.isna(row['MA20']):
                    ma20.append({"time": time_str, "value": float(row['MA20'])})
                if not pd.isna(row['MA60']):
                    ma60.append({"time": time_str, "value": float(row['MA60'])})
                if not pd.isna(row['MA120']):
                    ma120.append({"time": time_str, "value": float(row['MA120'])})

            context = f"Showing stock chart for {symbol} with 20/60/120 day moving averages. Current price is ${hist['Close'].iloc[-1]:.2f}."
            return self._render_template("stock_chart.json.j2", {
                "symbol": symbol.upper(),
                "prices": prices,
                "ma20": ma20,
                "ma60": ma60,
                "ma120": ma120,
                "current_price": f"${hist['Close'].iloc[-1]:.2f}"
            }), context
            
        except Exception as e:
            print(f"Stock Error: {e}")
            return TextResponse(text=f"Error fetching stock data: {e}"), f"Error fetching stock chart for {symbol}: {e}"

    def get_stock_dividends(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            divs = ticker.dividends
            if divs.empty:
                return TextResponse(text=f"No dividend data found for {symbol}"), f"No dividend data for {symbol}"
            
            # Last 20 entries
            recent_divs = divs.tail(20)
            data = []
            for date, value in recent_divs.items():
                data.append({"time": date.strftime("%Y-%m-%d"), "value": float(value)})
            
            current_yield = ticker.info.get('dividendYield', 0) * 100 if ticker.info.get('dividendYield') else 0
            
            return self._render_template("stock_dividends.json.j2", {
                "symbol": symbol.upper(),
                "dividends": data,
                "yield": f"{current_yield:.2f}%"
            }), f"Showing dividend history for {symbol}"
        except Exception as e:
            return TextResponse(text=f"Error fetching dividends: {e}"), f"Error: {e}"

    def get_stock_holders(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            inst = ticker.institutional_holders
            
            insider_pct = f"{info.get('heldPercentInsiders', 0)*100:.2f}%" if info.get('heldPercentInsiders') is not None else "N/A"
            inst_pct = f"{info.get('heldPercentInstitutions', 0)*100:.2f}%" if info.get('heldPercentInstitutions') is not None else "N/A"

            top_holders = []
            if inst is not None and not inst.empty:
                for _, row in inst.head(5).iterrows():
                    top_holders.append({
                        "name": row['Holder'],
                        "shares": f"{row['Shares']:,}",
                        "value": f"${row['Value']:,}" if 'Value' in row else "-",
                        "pct": f"{row['pctChange']*100:.2f}%" if 'pctChange' in row else "-"
                    })
            
            return self._render_template("stock_holders.json.j2", {
                "symbol": symbol.upper(),
                "insider_pct": insider_pct,
                "inst_pct": inst_pct,
                "top_holders": top_holders
            }), f"Showing holders for {symbol}"
        except Exception as e:
            return TextResponse(text=f"Error fetching holders: {e}"), f"Error: {e}"

    def get_stock_calendar(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            cal = ticker.calendar
            
            events = []
            if isinstance(cal, dict):
                for k, v in cal.items():
                    val = str(v)
                    if hasattr(v, 'strftime'):
                        val = v.strftime("%Y-%m-%d")
                    elif isinstance(v, list) and len(v) > 0 and hasattr(v[0], 'strftime'):
                         val = ", ".join([d.strftime("%Y-%m-%d") for d in v])
                    elif isinstance(v, list):
                        val = ", ".join(map(str, v))
                    
                    events.append({"name": k, "value": val})
            
            return self._render_template("stock_calendar.json.j2", {
                "symbol": symbol.upper(),
                "events": events
            }), f"Showing calendar for {symbol}"
        except Exception as e:
            return TextResponse(text=f"Error fetching calendar: {e}"), f"Error: {e}"

    
    def get_stock_news(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        from datetime import datetime
        
        print(f"Fetching news for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return TextResponse(text=f"No news found for {symbol}")
            
            # Extract news items (limit to 10)
            news_list = []
            for item in news[:10]:
                # New yfinance API structure: data is inside 'content' object
                content = item.get('content', item)
                
                # Parse publish time (new format uses ISO string 'pubDate')
                pub_date = content.get('pubDate', '')
                if pub_date:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = pub_date[:16] if len(pub_date) > 16 else pub_date
                else:
                    date_str = ''
                
                # Get URL from canonicalUrl or clickThroughUrl
                canonical = content.get('canonicalUrl', {})
                click_through = content.get('clickThroughUrl', {})
                link = canonical.get('url') or click_through.get('url') or '#'
                
                # Get publisher from provider
                provider = content.get('provider', {})
                publisher = provider.get('displayName', 'Unknown')
                
                news_list.append({
                    'title': content.get('title', 'No title').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' '),
                    'link': link,
                    'publisher': publisher.replace('\\', '\\\\').replace('"', '\\"'),
                    'date': date_str
                })
            
            context = f"Found {len(news_list)} recent news items for {symbol}. Top stories: " + ", ".join([n['title'] for n in news_list[:3]])
            return self._render_template("stock_news.json.j2", {
                "symbol": symbol.upper(),
                "news_list": news_list
            }), context
            
        except Exception as e:
            print(f"News Error: {e}")
            return TextResponse(text=f"Error fetching news: {e}"), f"Error fetching news for {symbol}: {e}"

    def get_stock_info(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        
        print(f"Fetching stock info for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract key data with fallbacks
            profile = {
                "name": info.get("longName", symbol.upper()),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "summary": info.get("longBusinessSummary", "No summary available."),
                "website": info.get("website", "#")
            }
            
            # Truncate summary if too long
            if len(profile["summary"]) > 300:
                profile["summary"] = profile["summary"][:297] + "..."
                
            financials = {
                "marketCap": info.get("marketCap", "N/A"),
                "trailingPE": info.get("trailingPE", "N/A"),
                "dividendYield": info.get("dividendYield", "N/A"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", "N/A"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", "N/A"),
                "targetMeanPrice": info.get("targetMeanPrice", "N/A"),
                "recommendationKey": info.get("recommendationKey", "N/A").replace("_", " ").title()
            }
            
            # Format large numbers
            if isinstance(financials["marketCap"], (int, float)):
                financials["marketCap"] = f"${financials['marketCap'] / 1e9:.2f}B"
                
            if isinstance(financials["dividendYield"], (int, float)):
                financials["dividendYield"] = f"{financials['dividendYield'] * 100:.2f}%"
                
            context = f"Company Profile for {symbol}: {profile['name']} ({profile['sector']}). Summary: {profile['summary'][:100]}... Key Stats: Market Cap {financials['marketCap']}, P/E {financials['trailingPE']}."
            return self._render_template("stock_info.json.j2", {
                "symbol": symbol.upper(),
                "profile": profile,
                "financials": financials
            }), context
            
        except Exception as e:
            print(f"Stock Info Error: {e}")
            return TextResponse(text=f"Error fetching stock info: {e}"), f"Error fetching profile for {symbol}: {e}"

    def get_technical_indicators(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        
        print(f"Calculating technical indicators for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 6 months of data to ensure enough for MACD/RSI
            hist = ticker.history(period="6mo")
            
            if hist.empty:
                return TextResponse(text=f"No historical data found for {symbol}")
            
            # Close prices
            close = hist['Close']
            
            # --- RSI (14) Calculation ---
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            rsi_signal = "Neutral"
            if current_rsi > 70:
                rsi_signal = "Overbought (Sell Warning)"
            elif current_rsi < 30:
                rsi_signal = "Oversold (Buy Opportunity)"
                
            # --- MACD (12, 26, 9) Calculation ---
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_hist = histogram.iloc[-1]
            
            macd_signal = "Neutral"
            if current_hist > 0 and histogram.iloc[-2] <= 0:
                macd_signal = "Bullish Crossover (Buy)"
            elif current_hist < 0 and histogram.iloc[-2] >= 0:
                macd_signal = "Bearish Crossover (Sell)"
            elif current_macd > current_signal:
                macd_signal = "Bullish Trend"
            elif current_macd < current_signal:
                macd_signal = "Bearish Trend"
            
            context = f"Technical Indicators for {symbol}: RSI is {current_rsi:.1f} ({rsi_signal}). MACD is {current_macd:.2f} ({macd_signal}). Price: ${close.iloc[-1]:.2f}."
            return self._render_template("stock_indicators.json.j2", {
                "symbol": symbol.upper(),
                "rsi": {
                    "value": f"{current_rsi:.1f}",
                    "signal": rsi_signal,
                    "color": "#ef4444" if current_rsi > 70 else ("#22c55e" if current_rsi < 30 else "#eab308")
                },
                "macd": {
                    "line": f"{current_macd:.2f}",
                    "signal_line": f"{current_signal:.2f}",
                    "histogram": f"{current_hist:.2f}",
                    "signal": macd_signal,
                    "color": "#22c55e" if current_macd > current_signal else "#ef4444"
                },
                "price": f"${close.iloc[-1]:.2f}",
                "date": hist.index[-1].strftime("%Y-%m-%d")
            }), context
            
        except Exception as e:
            print(f"Technical Indicator Error: {e}")
            return TextResponse(text=f"Error calculating indicators: {e}"), f"Error calculating technical indicators for {symbol}: {e}"

    def get_company_fundamentals(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        import pandas as pd
        
        print(f"Fetching fundamentals for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            
            # 1. Financials (Income Statement) - Last 4 years
            financials_data = []
            try:
                fin = ticker.financials
                if not fin.empty:
                    # Get Total Revenue and Net Income
                    # Transpose to iterate by date (columns)
                    # Take last 4 columns (years)
                    recent_fin = fin.loc[['Total Revenue', 'Net Income']].T.head(4)
                    
                    for date, row in recent_fin.iterrows():
                        financials_data.append({
                            "year": date.strftime("%Y"),
                            "revenue": f"${row['Total Revenue'] / 1e9:.1f}B",
                            "net_income": f"${row['Net Income'] / 1e9:.1f}B"
                        })
            except Exception as e:
                print(f"Financials Error: {e}")

            # 2. Major Holders
            holders_data = {"insiders": "N/A", "institutions": "N/A"}
            try:
                holders = ticker.major_holders
                # yfinance major_holders can be a DataFrame or dict depending on version/data
                # Typically it matches output from research script:
                # 0: 0.17% % of Shares Held by All Insider
                # 1: 64.82% % of Shares Held by Institutions
                # But recent output showed 'insidersPercentHeld', 'institutionsPercentHeld' in columns/index
                if holders is not None:
                     # Attempt to find specific keys/values based on research output structure
                     # Output was: breakdown by index/value
                     if 'Value' in holders.columns: # If dataframe
                         if 'insidersPercentHeld' in holders.index:
                             val = holders.loc['insidersPercentHeld', 'Value']
                             holders_data['insiders'] = f"{val * 100:.1f}%"
                         if 'institutionsPercentHeld' in holders.index:
                             val = holders.loc['institutionsPercentHeld', 'Value']
                             holders_data['institutions'] = f"{val * 100:.1f}%"
            except Exception as e:
                print(f"Holders Error: {e}")

            # 3. Recommendations
            recommendations_data = []
            try:
                recs = ticker.recommendations_summary
                if recs is not None and not recs.empty:
                    # Take the most recent period (period='0m')
                    latest = recs.iloc[0]
                    recommendations_data = [
                        {"label": "Strong Buy", "count": int(latest['strongBuy'])},
                        {"label": "Buy", "count": int(latest['buy'])},
                        {"label": "Hold", "count": int(latest['hold'])},
                        {"label": "Sell", "count": int(latest['sell'])},
                        {"label": "Strong Sell", "count": int(latest['strongSell'])}
                    ]
            except Exception as e:
                 print(f"Recs Error: {e}")

            context = f"Fundamentals for {symbol}: Financials (Last 4Y Revenue/NetIncome): {financials_data}. Recommendations: {recommendations_data}. Major Holders: {holders_data}."
            return self._render_template("stock_fundamentals.json.j2", {
                "symbol": symbol.upper(),
                "financials": financials_data,
                "holders": holders_data,
                "recommendations": recommendations_data
            }), context
            
        except Exception as e:
            print(f"Fundamentals Error: {e}")
            return TextResponse(text=f"Error fetching fundamentals: {e}"), f"Error fetching fundamentals for {symbol}: {e}"

class ShoppingService(RestaurantService):
    def search_products(self, query: str) -> Union[A2UIResponse, TextResponse]:
        import httpx
        import xml.etree.ElementTree as ET
        from urllib.parse import quote
        import os
        
        print(f"Searching products for {query}")
        
        # Prefer env vars, fallback to class constants if empty (for backward compat)
        client_id = os.environ.get("NAVER_CLIENT_ID", self.NAVER_CLIENT_ID)
        client_secret = os.environ.get("NAVER_CLIENT_SECRET", self.NAVER_CLIENT_SECRET)
        
        url = f"https://openapi.naver.com/v1/search/shop.xml?query={quote(query)}&display=10&start=1&sort=sim"
        
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        
        try:
            response = httpx.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.text)
            channel = root.find("channel")
            
            items = []
            if channel:
                for item in channel.findall("item"):
                    # Clean tags
                    title = item.find("title").text or ""
                    title = title.replace("<b>", "").replace("</b>", "")
                    
                    link = item.find("link").text or "#"
                    image = item.find("image").text or ""
                    mall_name = item.find("mallName").text or "Unknown Store"
                    lprice = item.find("lprice").text or "0"
                    
                    # Format price with commas
                    try:
                        lprice_fmt = f"{int(lprice):,}"
                    except:
                        lprice_fmt = lprice
                    
                    items.append({
                        "title": title,
                        "link": link,
                        "image": image,
                        "mallName": mall_name,
                        "lprice": lprice_fmt
                    })
            
            if not items:
                return TextResponse(text=f"No products found for '{query}'"), f"No products found for {query}."
                
            context = f"Found {len(items)} products for '{query}'. Top items: " + ", ".join([i['title'] for i in items[:3]])
            return self._render_template("product_list.json.j2", {
                "query": query,
                "items": items
            }), context
            
        except Exception as e:
            print(f"Shopping API Error: {e}")
            return TextResponse(text=f"Error searching products: {e}"), f"Error searching products: {e}"
