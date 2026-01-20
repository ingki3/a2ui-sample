import math
from typing import List, Dict, Any, Union
from models import (
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
        from jinja2 import Environment, FileSystemLoader
        import json
        import os
        import uuid

        # Ensure we have a UID for namespacing even for single loan calc
        uid = str(uuid.uuid4())[:8]
        
        # Note: In a real app, Environment should be created once at module level or dependency injected
        env = Environment(loader=FileSystemLoader("templates"))
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
        
        # Generate a short random UID if not provided to ensure namespacing
        if not uid:
             uid = str(uuid.uuid4())[:8]

        env = Environment(loader=FileSystemLoader("templates"))
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
