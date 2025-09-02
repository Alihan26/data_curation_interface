#!/usr/bin/env python3
"""
Test script to debug AI curation service
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

def test_ai_service():
    """Test the AI service directly"""
    print("🧪 Testing AI Curation Service...")
    
    try:
        from ai_curation import AICurationService
        
        # Check environment
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"🔑 API Key present: {'Yes' if api_key else 'No'}")
        if api_key:
            print(f"🔑 API Key length: {len(api_key)}")
            print(f"🔑 API Key starts with: {api_key[:20]}...")
        
        # Initialize service
        print("\n🚀 Initializing AI service...")
        ai_service = AICurationService()
        print("✅ AI service initialized")
        
        # Check availability
        print("\n🔍 Checking service availability...")
        is_available = ai_service.is_available()
        print(f"✅ Service available: {is_available}")
        
        if is_available:
            # Test with sample data
            print("\n🧠 Testing suggestion generation...")
            
            # Sample HTML content
            sample_html = """
            <html>
            <head><title>Test Page</title></head>
            <body>
            <h1>Digital Library Test</h1>
            <p>This is a test page for digital library metadata curation.</p>
            <p>The content focuses on ancient texts and manuscripts.</p>
            <p>Published in 2023 by University Press.</p>
            </body>
            </html>
            """
            
            # Sample properties
            sample_properties = [
                {
                    "id": 1,
                    "name": "Content Type",
                    "type": "SINGLE_CHOICE",
                    "technical_name": "content_type",
                    "property_options": [
                        {"id": 1, "name": "Manuscript"},
                        {"id": 2, "name": "Book"},
                        {"id": 3, "name": "Article"}
                    ]
                },
                {
                    "id": 2,
                    "name": "Language",
                    "type": "SINGLE_CHOICE", 
                    "technical_name": "language",
                    "property_options": [
                        {"id": 4, "name": "English"},
                        {"id": 5, "name": "German"},
                        {"id": 6, "name": "Latin"}
                    ]
                },
                {
                    "id": 3,
                    "name": "Publication Year",
                    "type": "NUMERICAL",
                    "technical_name": "publication_year"
                }
            ]
            
            print(f"📄 Sample HTML length: {len(sample_html)} characters")
            print(f"🏷️ Sample properties: {len(sample_properties)} properties")
            
            # Generate suggestions
            suggestions = ai_service.generate_metadata_suggestions(
                sample_html, 
                "https://test.example.com", 
                sample_properties
            )
            
            print(f"\n🎯 Raw AI suggestions received: {len(suggestions)}")
            if suggestions:
                print("📝 First suggestion:")
                print(f"   {suggestions[0]}")
                
                # Validate suggestions
                print("\n✅ Validating suggestions...")
                validated = ai_service.validate_suggestions(suggestions, sample_properties)
                print(f"✅ Validated suggestions: {len(validated)}")
                
                if validated:
                    print("📝 First validated suggestion:")
                    print(f"   {validated[0]}")
            else:
                print("❌ No suggestions received from AI")
                
        else:
            print("❌ AI service not available")
            
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_service()
