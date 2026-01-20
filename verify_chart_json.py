from agent import StockService
import json

def verify_chart():
    service = StockService()
    # Use a well known symbol
    response = service.get_stock_chart("AAPL")
    
    if response.kind != "a2ui":
        print(f"FAILED: Expected a2ui response, got {response.kind}")
        return

    data = response.data
    surface = data.surfaceUpdate
    
    # Find Chart component
    chart_comp = None
    for comp in surface.components:
        if comp.component.Chart:
            chart_comp = comp.component.Chart
            break
            
    if chart_comp:
        print("SUCCESS: Found Chart component")
        print(f"Data points: {len(chart_comp.data)}")
        if len(chart_comp.data) > 0:
            point = chart_comp.data[0]
            print(f"First point: {point}")
            if "time" not in point:
                print("FAILED: 'time' key missing in data point")
            if "value" not in point:
                print("FAILED: 'value' key missing in data point")
            print(f"Color: {chart_comp.color}")
    else:
        print("FAILED: Chart component not found in response")
        print(json.dumps(surface.dict(), indent=2))

if __name__ == "__main__":
    verify_chart()
