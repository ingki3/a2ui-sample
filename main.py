from fastapi import FastAPI, Depends, Request, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent import LoanCalculatorService
from models import A2UIResponse, TextResponse
from typing import Union, Dict, Any, Optional
from llm_wrapper import LLMWrapper

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

agent = LoanCalculatorService()
llm = LLMWrapper()

class ChatRequest(BaseModel):
    text: str
    client_context: Optional[Dict[str, Any]] = None

@app.post("/chat", response_model=Union[A2UIResponse, TextResponse])
async def chat(request: Request, chat_req: ChatRequest):
    text = chat_req.text
    
    # Check client A2UI capability
    is_a2ui_client = request.headers.get("x-client-a2ui") == "true"
    
    # Handle Recalculate Logic (Explicit Button Clicks)
    # This bypasses the LLM because it's a direct action from the UI
    if chat_req.client_context and "recalculate" in text.lower():
         context = chat_req.client_context
         principal = float(context.get("principal", 0))
         rate = float(context.get("annualRate", 0))
         years = int(float(context.get("years", 0)))
         return agent.calculate_loan(principal, rate, years, is_ui_mode=is_a2ui_client)

    # Use LLM for Natural Language Understanding
    processed = llm.process_query(text)
    
    if processed["type"] == "multiple_tool_calls":
        calls = processed["calls"]
        responses = []
        
        from agent import RestaurantService, StockService, ShoppingService
        restaurant_service = RestaurantService()
        stock_service = StockService()
        shopping_service = ShoppingService()
        
        for call in calls:
            tool_name = call["tool_name"]
            args = call["tool_args"]
            
            res = None
            if tool_name == "calculate_loan":
                principal = float(args.get("principal", 0))
                rate = float(args.get("rate", 0))
                years = int(args.get("years", 0))
                res = agent.calculate_loan(principal, rate, years, is_ui_mode=is_a2ui_client)
                
            elif tool_name == "find_restaurants":
                location = args.get("location")
                cuisine = args.get("cuisine")
                res = restaurant_service.find_restaurants(location, cuisine)
                
            elif tool_name == "reserve_table":
                r_name = args.get("restaurant_name")
                date = args.get("date")
                guests = int(args.get("guests", 2))
                res = restaurant_service.reserve_table(r_name, date, guests)

            elif tool_name == "reserve_table":
                r_name = args.get("restaurant_name")
                date = args.get("date")
                guests = int(args.get("guests", 2))
                res = restaurant_service.reserve_table(r_name, date, guests)

            elif tool_name == "search_products":
                query = args.get("query")
                res = shopping_service.search_products(query)

            elif tool_name == "get_stock_chart":
                symbol = args.get("symbol")
                res = stock_service.get_stock_chart(symbol)
                
                # Generate AI commentary for stock charts
                if isinstance(res, A2UIResponse) and res.data.surfaceUpdate:
                    # Extract current price from the response components
                    current_price = 0.0
                    for comp in res.data.surfaceUpdate.components:
                        if comp.component.Chart and comp.component.Chart.data:
                            # Get the last price value
                            current_price = comp.component.Chart.data[-1].value
                            break
                    
                    # Generate commentary
                    commentary = llm.generate_commentary(symbol, current_price)
                    
                    if commentary:
                        # Add commentary as a Text component
                        import uuid
                        commentary_id = f"commentary_{str(uuid.uuid4())[:8]}"
                        
                        from models import ComponentEntry, ComponentType, TextComponent, TextContent
                        
                        commentary_comp = ComponentEntry(
                            id=commentary_id,
                            component=ComponentType(
                                Text=TextComponent(
                                    text=TextContent(literalString=commentary),
                                    usageHint="body"
                                )
                            )
                        )
                        
                        # Add to components
                        res.data.surfaceUpdate.components.append(commentary_comp)
                        
                        # Update the root Column to include commentary
                        root_id = res.data.beginRendering.root
                        for comp in res.data.surfaceUpdate.components:
                            if comp.id == root_id and comp.component.Column:
                                comp.component.Column.children.explicitList.append(commentary_id)
                                break
                
            if res:
                responses.append(res)
        
        # Merge Responses
        if not responses:
            return TextResponse(text="No tools executed.")
            
        if len(responses) == 1:
            return responses[0]
            
        # Dashboard Merge Logic
        from models import A2UIData, SurfaceUpdate, DataModelUpdate, BeginRendering, ComponentEntry, ComponentType, ColumnComponent, ColumnChildren
        
        merged_components = []
        merged_data_contents = []
        root_ids = []
        
        for i, r in enumerate(responses):
            if isinstance(r, TextResponse):
                 # Convert text to component? For now, skip or log.
                 # Better: Create a simple TextComponent
                 pass
            elif isinstance(r, A2UIResponse):
                 # Add components
                 if r.data.surfaceUpdate:
                     merged_components.extend(r.data.surfaceUpdate.components)
                     # Track the root of this sub-surface
                     if r.data.beginRendering:
                         root_ids.append(r.data.beginRendering.root)
                 
                 # Add data model
                 if r.data.dataModelUpdate:
                     merged_data_contents.extend(r.data.dataModelUpdate.contents)

        # Create Dashboard Root
        import uuid
        dash_root_id = f"dashboard_{str(uuid.uuid4())[:8]}"
        
        dashboard_col = ComponentEntry(
            id=dash_root_id,
            component=ComponentType(
                Column=ColumnComponent(
                    children=ColumnChildren(explicitList=root_ids)
                )
            )
        )
        merged_components.insert(0, dashboard_col)
        
        return A2UIResponse(
            data=A2UIData(
                surfaceUpdate=SurfaceUpdate(
                    surfaceId="dashboard",
                    components=merged_components
                ),
                dataModelUpdate=DataModelUpdate(
                    surfaceId="dashboard",
                    contents=merged_data_contents
                ),
                beginRendering=BeginRendering(
                    surfaceId="dashboard",
                    root=dash_root_id
                )
            )
        )
            
    # Default Text Response
    return TextResponse(text=processed.get("text", "I didn't understand that."))

@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

@app.post("/chat/stream")
async def chat_stream(request: Request, chat_req: ChatRequest):
    """
    SSE streaming endpoint: sends A2UI first, then streams commentary.
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    text = chat_req.text
    is_a2ui_client = request.headers.get("x-client-a2ui") == "true"
    
    async def event_generator():
        # Process the query
        processed = llm.process_query(text)
        
        if processed["type"] == "multiple_tool_calls":
            from agent import StockService, RestaurantService, LoanCalculatorService, ShoppingService
            stock_service = StockService()
            restaurant_service = RestaurantService()
            loan_service = LoanCalculatorService()
            shopping_service = ShoppingService()
            
            for call in processed["calls"]:
                tool_name = call["tool_name"]
                args = call["tool_args"]
                
                res = None
                needs_commentary = False
                commentary_context = {}
                
                if tool_name == "get_stock_chart":
                    symbol = args.get("symbol")
                    res = stock_service.get_stock_chart(symbol)
                    needs_commentary = True
                    
                    if isinstance(res, A2UIResponse) and res.data.surfaceUpdate:
                        for comp in res.data.surfaceUpdate.components:
                            if comp.component.Chart and comp.component.Chart.data:
                                commentary_context = {
                                    "symbol": symbol,
                                    "price": comp.component.Chart.data[-1].value
                                }
                                break
                
                elif tool_name == "find_restaurants":
                    location = args.get("location")
                    cuisine = args.get("cuisine")
                    res = restaurant_service.find_restaurants(location, cuisine)
                
                elif tool_name == "reserve_table":
                    r_name = args.get("restaurant_name")
                    date = args.get("date")
                    guests = int(args.get("guests", 2))
                    res = restaurant_service.reserve_table(r_name, date, guests)
                
                elif tool_name == "calculate_loan":
                    principal = float(args.get("principal", 0))
                    rate = float(args.get("rate", 0))
                    years = int(args.get("years", 0))
                    res = loan_service.calculate_loan(principal, rate, years, is_ui_mode=True)
                
                elif tool_name == "get_stock_news":
                    symbol = args.get("symbol")
                    res = stock_service.get_stock_news(symbol)
                
                elif tool_name == "get_stock_news":
                    symbol = args.get("symbol")
                    res = stock_service.get_stock_news(symbol)

                elif tool_name == "search_products":
                    query = args.get("query")
                    res = shopping_service.search_products(query)
                
                # Send A2UI response if available
                if res and isinstance(res, A2UIResponse):
                    a2ui_data = res.model_dump()
                    yield f"event: a2ui\ndata: {json.dumps(a2ui_data)}\n\n"
                    
                    # Stream commentary for stock charts
                    if needs_commentary and commentary_context:
                        async for chunk in llm.generate_commentary_stream(
                            commentary_context.get("symbol"), 
                            commentary_context.get("price", 0)
                        ):
                            yield f"event: text\ndata: {json.dumps({'text': chunk})}\n\n"
                            await asyncio.sleep(0)
        
        else:
            # Non-tool response
            yield f"event: text\ndata: {json.dumps({'text': processed.get('text', '')})}\n\n"
        
        # Signal completion
        yield f"event: done\ndata: {{}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

