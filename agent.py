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
    def find_restaurants(self, location: str, cuisine: str = None) -> Union[A2UIResponse, TextResponse]:
        print(f"Finding {cuisine or 'any'} restaurants in {location}")
        
        # Mock Data
        restaurants = [
            {
                "id": "r1",
                "name": "Bella Italia",
                "cuisine": "Italian",
                "rating": 4.5,
                "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&q=80",
                "location": "Downtown"
            },
            {
                "id": "r2",
                "name": "Seoul Kitchen",
                "cuisine": "Korean",
                "rating": 4.8,
                "image": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=500&q=80",
                "location": "Gangnam"
            },
            {
                "id": "r3",
                "name": "Sushi Zen",
                "cuisine": "Japanese",
                "rating": 4.7,
                "image": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500&q=80",
                "location": "Uptown"
            }
        ]

        # Filter
        results = [r for r in restaurants if location.lower() in r['location'].lower() or location.lower() == "any"]
        if cuisine:
             results = [r for r in results if cuisine.lower() in r['cuisine'].lower()]
        
        # If no strict match, show all for demo purposes if location matches
        if not results:
             print("No exact match, showing some defaults for demo")
             results = restaurants[:2]

        return self._render_template("restaurant_list.json.j2", {"restaurants": results, "location": location})

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
            # Fetch 1 month history
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                 return TextResponse(text=f"No data found for {symbol}")

            # Prepare data for ChartComponent (native rendering)
            prices = []
            
            for index, row in hist.iterrows():
                prices.append({
                    "label": index.strftime("%m/%d"),
                    "value": float(row['Close'])
                })

            return self._render_template("stock_chart.json.j2", {
                "symbol": symbol.upper(),
                "prices": prices, # List of {label, value}
                "current_price": f"${hist['Close'].iloc[-1]:.2f}"
            })
            
        except Exception as e:
            print(f"Stock Error: {e}")
            return TextResponse(text=f"Error fetching stock data: {e}")
