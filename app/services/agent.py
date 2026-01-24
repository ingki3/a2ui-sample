import math
from typing import List, Dict, Any, Union
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
            return self.create_loan_result_ui(principal, annual_rate, years, monthly_payment, total_payment, total_interest)
        else:
            return TextResponse(text=f"Monthly Payment: ${monthly_payment:.2f}, Total Interest: ${total_interest:.2f}")

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
            
            restaurants = []
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
                
                restaurants.append({
                    "id": f"naver_{idx}",
                    "name": title,
                    "cuisine": category.split(">")[-1] if ">" in category else category,
                    "rating": 4.5,  # Naver API doesn't provide ratings
                    "location": road_address or address,
                    "address": address,
                    "road_address": road_address,
                    "lat": lat,
                    "lng": lng,
                    "map_url": f"https://www.google.com/maps?q={lat},{lng}"
                })
            
            return restaurants
            
        except Exception as e:
            print(f"Naver API Error: {e}")
            return []
    
    def find_restaurants(self, location: str, cuisine: str = None) -> Union[A2UIResponse, TextResponse]:
        print(f"Finding {cuisine or 'any'} restaurants in {location}")
        
        # Build search query
        query = f"{location} 맛집"
        if cuisine:
            query = f"{location} {cuisine}"
        
        # Call Naver API
        restaurants = self._search_naver_local(query, display=5)
        
        if not restaurants:
            print("No results from Naver API, using fallback mock data")
            # Fallback to mock data
            restaurants = [
                {
                    "id": "r1",
                    "name": "Seoul Kitchen",
                    "cuisine": "Korean",
                    "rating": 4.8,
                    "location": location,
                    "lat": 37.5665,
                    "lng": 126.9780,
                    "map_url": "https://www.google.com/maps?q=37.5665,126.9780"
                }
            ]

        import os
        maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        return self._render_template("restaurant_list.json.j2", {
            "restaurants": restaurants, 
            "location": location,
            "maps_api_key": maps_api_key
        })

    def reserve_table(self, restaurant_name: str, date: str, guests: int) -> Union[A2UIResponse, TextResponse]:
        print(f"Reserving {restaurant_name} for {guests} on {date}")
        return self._render_template("reservation_confirmed.json.j2", {
            "restaurant_name": restaurant_name,
            "date": date,
            "guests": guests
        })
    
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
            return A2UIResponse(data=A2UIData(**data_dict))
        except Exception as e:
            print(f"Template Rendering Error: {e}")
            return TextResponse(text=f"Error rendering UI: {e}")

class StockService(RestaurantService):
    def get_stock_chart(self, symbol: str) -> Union[A2UIResponse, TextResponse]:
        import yfinance as yf
        
        print(f"Fetching stock chart for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 1 year history
            hist = ticker.history(period="1y")
            
            if hist.empty:
                 return TextResponse(text=f"No data found for {symbol}")

            # Prepare data for ChartComponent (native rendering)
            prices = []
            
            for index, row in hist.iterrows():
                prices.append({
                    "time": index.strftime("%Y-%m-%d"),
                    "value": float(row['Close'])
                })

            return self._render_template("stock_chart.json.j2", {
                "symbol": symbol.upper(),
                "prices": prices, # List of {time, value}
                "current_price": f"${hist['Close'].iloc[-1]:.2f}"
            })
            
        except Exception as e:
            print(f"Stock Error: {e}")
            return TextResponse(text=f"Error fetching stock data: {e}")

    
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
                    'title': content.get('title', 'No title'),
                    'link': link,
                    'publisher': publisher,
                    'date': date_str
                })
            
            return self._render_template("stock_news.json.j2", {
                "symbol": symbol.upper(),
                "news_list": news_list
            })
            
        except Exception as e:
            print(f"News Error: {e}")
            return TextResponse(text=f"Error fetching news: {e}")

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
                return TextResponse(text=f"No products found for '{query}'")
                
            return self._render_template("product_list.json.j2", {
                "query": query,
                "items": items
            })
            
        except Exception as e:
            print(f"Shopping API Error: {e}")
            return TextResponse(text=f"Error searching products: {e}")
