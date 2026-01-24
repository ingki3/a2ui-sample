import os
from dotenv import load_dotenv
from agent import ShoppingService

# Load environment variables
load_dotenv()

def test_search_products():
    service = ShoppingService()
    query = "가방"
    print(f"Testing search_products with query: {query}")
    
    response = service.search_products(query)
    
    if hasattr(response, 'data'):
        print("✅ Received A2UIResponse")
        print(f"Surface ID: {response.data.surfaceUpdate.surfaceId}")
        
        components = response.data.surfaceUpdate.components
        print(f"Total Components: {len(components)}")
        
        # Verify structure
        has_header = any(c.component.Column and c.component.Column.style == 'news-header' for c in components if c.component.Column)
        has_items = any(c.component.Column and c.component.Column.style == 'news-card' for c in components if c.component.Column)
        
        if has_header:
            print("✅ Header found")
        else:
            print("❌ Header NOT found")
            
        if has_items:
            print(f"✅ Product items found")
            # Print details for first 3 items
            count = 0
            for c in components:
                 if c.component.Text and c.component.Text.usageHint == 'news-title':
                     print(f"   Item {count+1}: {c.component.Text.text.literalString}")
                     count += 1
                     if count >= 3:
                         break
        else:
             print("❌ Product items NOT found")
             
    else:
        print("❌ Received TextResponse (Error):")
        print(response.text)

if __name__ == "__main__":
    test_search_products()
