#!/usr/bin/env python3
"""
Simple test for two-pass AI confidence system
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_curation import AICurationService
from dummy_data import get_dummy_properties

def test_two_pass_confidence():
    """Test the two-pass AI confidence system"""
    
    print("🧪 Testing Two-Pass AI Confidence System")
    print("=" * 50)
    
    # Initialize AI service
    ai_service = AICurationService()
    properties = get_dummy_properties()
    
    # Sample content for testing
    test_content = """
    Martha Ballard's Diary Online is a digital edition of the diary of Martha Ballard, 
    a midwife who lived in Hallowell, Maine, from 1785 to 1812. The diary contains 
    detailed entries about her daily life, medical practices, and community interactions.
    This digital edition was created by the Center for History and New Media at 
    George Mason University and is freely available online.
    """
    
    test_url = "https://dohistory.org/diary/about.html"
    
    print(f"📝 Test content length: {len(test_content)} characters")
    print(f"🔗 Test URL: {test_url}")
    print(f"📋 Available properties: {len(properties)}")
    print()
    
    try:
        # Test Agent A (Reasoner)
        print("🤖 Testing Agent A (Reasoner)...")
        reasoned_suggestions = ai_service.generate_reasoned_suggestions(
            test_content,
            test_url,
            properties
        )
        
        print(f"✅ Agent A generated {len(reasoned_suggestions)} reasoned suggestions")
        
        if reasoned_suggestions:
            sample = reasoned_suggestions[0]
            print(f"📋 Sample reasoning length: {len(sample.get('long_reasoning', ''))}")
            print(f"🔍 Sample evidence length: {len(sample.get('evidence', ''))}")
            print(f"❓ Has confidence: {'confidence' in sample}")
            print()
        
        # Test Agent B (Confidence Interpreter)
        print("🎯 Testing Agent B (Confidence Interpreter)...")
        
        interpreter_results = ai_service.interpret_confidence(
            reasoned_suggestions, 
            properties, 
            test_url
        )
        
        print(f"✅ Agent B processed {len(interpreter_results)} confidence interpretations")
        
        if interpreter_results:
            # Analyze confidence distribution
            confidences = [float(r.get('confidence', 0)) for r in interpreter_results]
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)
            
            print(f"📊 Confidence Statistics:")
            print(f"   • Average: {avg_conf:.2f}")
            print(f"   • Range: {min_conf:.2f} - {max_conf:.2f}")
            print(f"   • High confidence (≥80%): {len([c for c in confidences if c >= 0.8])}")
            print(f"   • Low confidence (<50%): {len([c for c in confidences if c < 0.5])}")
            print()
            
            # Show sample interpretation
            sample_interp = interpreter_results[0]
            print(f"🔍 Sample Interpretation:")
            print(f"   • Property ID: {sample_interp.get('property_id')}")
            print(f"   • Confidence: {sample_interp.get('confidence', 0):.2f}")
            print(f"   • Rationale: {sample_interp.get('rationale', '')[:100]}...")
            print(f"   • Tags: {sample_interp.get('tags', [])}")
            print()
        
        print("✅ Two-pass AI confidence system test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_pass_comparison():
    """Compare single-pass vs two-pass results"""
    
    print("\n🔄 Testing Single-Pass vs Two-Pass Comparison")
    print("=" * 50)
    
    ai_service = AICurationService()
    properties = get_dummy_properties()
    
    test_content = """
    Martha Ballard's Diary Online provides access to the complete diary of Martha Ballard,
    a midwife who practiced in Maine from 1785 to 1812. The diary offers insights into
    early American medical practices, women's roles, and community life.
    """
    
    try:
        # Single-pass (traditional)
        print("🔄 Testing single-pass AI...")
        single_pass_results = ai_service.generate_metadata_suggestions(
            test_content,
            "https://dohistory.org/diary/about.html",
            properties
        )
        
        single_confidences = [s.get('confidence', 0) for s in single_pass_results]
        single_avg = sum(single_confidences) / len(single_confidences) if single_confidences else 0
        
        print(f"📊 Single-pass results:")
        print(f"   • Suggestions: {len(single_pass_results)}")
        print(f"   • Average confidence: {single_avg:.2f}")
        
        # Two-pass
        print("\n🤖 Testing two-pass AI...")
        reasoned = ai_service.generate_reasoned_suggestions(
            test_content,
            "https://dohistory.org/diary/about.html",
            properties
        )
        
        interpreted = ai_service.interpret_confidence(
            reasoned,
            properties,
            "https://dohistory.org/diary/about.html"
        )
        
        two_pass_confidences = [i.get('confidence', 0) for i in interpreted]
        two_pass_avg = sum(two_pass_confidences) / len(two_pass_confidences) if two_pass_confidences else 0
        
        print(f"📊 Two-pass results:")
        print(f"   • Suggestions: {len(reasoned)}")
        print(f"   • Average confidence: {two_pass_avg:.2f}")
        
        print(f"\n📈 Comparison:")
        print(f"   • Confidence difference: {two_pass_avg - single_avg:.2f}")
        print(f"   • Two-pass {'higher' if two_pass_avg > single_avg else 'lower'} confidence")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"🚀 Starting Two-Pass AI Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Please set it in your environment.")
        sys.exit(1)
    
    # Run tests
    test1_passed = test_two_pass_confidence()
    test2_passed = test_single_pass_comparison()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   • Two-pass system test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • Comparison test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Two-pass AI confidence system is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        sys.exit(1)
