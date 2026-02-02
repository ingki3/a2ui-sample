import os
from fastapi import FastAPI, Depends, Request, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.services.agent import LoanCalculatorService
from app.schemas.models import A2UIResponse, TextResponse
from typing import Union, Dict, Any, Optional
from app.services.llm_wrapper import LLMWrapper

app = FastAPI()

# Mount static files
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static"))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

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
        
        from app.services.agent import RestaurantService, StockService, ShoppingService
        restaurant_service = RestaurantService()
        stock_service = StockService()
        shopping_service = ShoppingService()
        
        for call in calls:
            tool_name = call["tool_name"]
            args = call["tool_args"]
            
            if tool_name == "calculate_loan":
                principal = float(args.get("principal", 0))
                rate = float(args.get("rate", 0))
                years = int(args.get("years", 0))
                res, _ = agent.calculate_loan(principal, rate, years, is_ui_mode=is_a2ui_client)
                
            elif tool_name == "find_places":
                location = args.get("location")
                keyword = args.get("keyword")
                res, _ = restaurant_service.find_places(location, keyword)
                
            elif tool_name == "reserve_table":
                r_name = args.get("restaurant_name")
                date = args.get("date")
                guests = int(args.get("guests", 2))
                res, _ = restaurant_service.reserve_table(r_name, date, guests)

            elif tool_name == "search_products":
                query = args.get("query")
                res, _ = shopping_service.search_products(query)

            elif tool_name == "get_stock_info":
                symbol = args.get("symbol")
                res, _ = stock_service.get_stock_info(symbol)

            elif tool_name == "get_technical_indicators":
                symbol = args.get("symbol")
                res, _ = stock_service.get_technical_indicators(symbol)

            elif tool_name == "get_company_fundamentals":
                symbol = args.get("symbol")
                res, _ = stock_service.get_company_fundamentals(symbol)

            elif tool_name == "get_stock_chart":
                symbol = args.get("symbol")
                res, _ = stock_service.get_stock_chart(symbol)

            elif tool_name == "get_stock_dividends":
                symbol = args.get("symbol")
                res, _ = stock_service.get_stock_dividends(symbol)

            elif tool_name == "get_stock_holders":
                symbol = args.get("symbol")
                res, _ = stock_service.get_stock_holders(symbol)

            elif tool_name == "get_stock_calendar":
                symbol = args.get("symbol")
                res, _ = stock_service.get_stock_calendar(symbol)
                
            if res:
                responses.append(res)
        
        # Merge Responses
        if not responses:
            return TextResponse(text="No tools executed.")
            
        if len(responses) == 1:
            return responses[0]
            
        # Dashboard Merge Logic
        from app.schemas.models import A2UIData, SurfaceUpdate, DataModelUpdate, BeginRendering, ComponentEntry, ComponentType, ColumnComponent, ColumnChildren
        
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
    return FileResponse(os.path.join(static_dir, 'index.html'))

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
        import logging
        logger = logging.getLogger(__name__)
        
        # Process the query
        processed = llm.process_query(text)
        logger.info(f"Stream endpoint received query: {text[:50]}... | Type: {processed['type']}")
        
        if processed["type"] == "multiple_tool_calls":
            from app.services.agent import StockService, RestaurantService, LoanCalculatorService, ShoppingService
            stock_service = StockService()
            restaurant_service = RestaurantService()
            loan_service = LoanCalculatorService()
            shopping_service = ShoppingService()
            
            context_accumulator = []

            for call in processed["calls"]:
                tool_name = call["tool_name"]
                args = call["tool_args"]
                
                res = None
                context = ""
                
                if tool_name == "get_stock_chart":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_stock_chart(symbol)
                
                elif tool_name == "find_places":
                    location = args.get("location")
                    keyword = args.get("keyword")
                    res, context = restaurant_service.find_places(location, keyword)
                
                elif tool_name == "reserve_table":
                    r_name = args.get("restaurant_name")
                    date = args.get("date")
                    guests = int(args.get("guests", 2))
                    res, context = restaurant_service.reserve_table(r_name, date, guests)
                
                elif tool_name == "calculate_loan":
                    principal = float(args.get("principal", 0))
                    rate = float(args.get("rate", 0))
                    years = int(args.get("years", 0))
                    res, context = loan_service.calculate_loan(principal, rate, years, is_ui_mode=True)
                
                elif tool_name == "get_stock_news":
                    symbol = args.get("symbol")
                    print(f"Calling get_stock_news for symbol: {symbol}")
                    res, context = stock_service.get_stock_news(symbol)
                    print(f"get_stock_news returned: type={type(res).__name__}")
                
                elif tool_name == "search_products":
                    query = args.get("query")
                    res, context = shopping_service.search_products(query)

                elif tool_name == "get_stock_info":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_stock_info(symbol)

                elif tool_name == "get_technical_indicators":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_technical_indicators(symbol)

                elif tool_name == "get_company_fundamentals":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_company_fundamentals(symbol)

                elif tool_name == "get_stock_dividends":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_stock_dividends(symbol)

                elif tool_name == "get_stock_holders":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_stock_holders(symbol)

                elif tool_name == "get_stock_calendar":
                    symbol = args.get("symbol")
                    res, context = stock_service.get_stock_calendar(symbol)
                
                # Send A2UI response if available
                if res and isinstance(res, A2UIResponse):
                    print(f"Sending A2UI event for tool: {tool_name}")
                    a2ui_data = res.model_dump()
                    yield f"event: a2ui\ndata: {json.dumps(a2ui_data)}\n\n"
                else:
                    print(f"NOT sending A2UI for {tool_name}, res type: {type(res).__name__ if res else 'None'}")
                
                if context:
                    context_accumulator.append(context)

            # Generate and stream final answer based on accumulated context
            if context_accumulator:
                 async for chunk in llm.answer_with_context_stream(text, context_accumulator):
                      yield f"event: text\ndata: {json.dumps({'text': chunk})}\n\n"
                      await asyncio.sleep(0)
        
        else:
            # Non-tool response: Stream the response for consistency
            logger.info(f"No tool call - streaming text response directly")
            text_response = processed.get('text', '')
            
            # If LLM provided a text response, stream it
            if text_response:
                words = text_response.split(' ')
                chunk_size = 3  # Send 3 words at a time
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i+chunk_size])
                    if i + chunk_size < len(words):
                        chunk += ' '
                    yield f"event: text\ndata: {json.dumps({'text': chunk})}\n\n"
                    await asyncio.sleep(0.02)
            else:
                yield f"event: text\ndata: {json.dumps({'text': '응답을 생성할 수 없습니다.'})}\n\n"
        
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

