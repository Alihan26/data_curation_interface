#!/usr/bin/env python3
"""
Comprehensive test for the confidence threshold system
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_curation import AICurationService
from dummy_data import get_dummy_properties

def test_confidence_distribution():
    """Test that confidence scores are realistic and varied"""
    
    print("🧪 Testing Confidence Distribution")
    print("=" * 50)
    
    # Initialize AI service
    ai_service = AICurationService()
    properties = get_dummy_properties()
    
    # Test content
    test_content = """
    Martha Ballard's Diary Online is a digital edition of the diary of Martha Ballard, 
    a midwife who lived in Hallowell, Maine, from 1785 to 1812. The diary contains 
    detailed entries about her daily life, medical practices, and community interactions.
    This digital edition was created by the Center for History and New Media at 
    George Mason University and is freely available online.
    """
    
    test_url = "https://dohistory.org/diary/about.html"
    
    try:
        # Generate reasoned suggestions
        reasoned_suggestions = ai_service.generate_reasoned_suggestions(
            test_content,
            test_url,
            properties
        )
        
        # Interpret confidence
        interpreter_results = ai_service.interpret_confidence(
            reasoned_suggestions, 
            properties, 
            test_url
        )
        
        if not interpreter_results:
            print("❌ No confidence interpretations returned")
            return False
            
        # Analyze confidence distribution
        confidences = [float(r.get('confidence', 0)) for r in interpreter_results]
        avg_conf = sum(confidences) / len(confidences)
        min_conf = min(confidences)
        max_conf = max(confidences)
        
        print(f"📊 Confidence Statistics:")
        print(f"   • Count: {len(confidences)}")
        print(f"   • Average: {avg_conf:.2f}")
        print(f"   • Range: {min_conf:.2f} - {max_conf:.2f}")
        print(f"   • High confidence (≥80%): {len([c for c in confidences if c >= 0.8])}")
        print(f"   • Medium confidence (50-80%): {len([c for c in confidences if 0.5 <= c < 0.8])}")
        print(f"   • Low confidence (<50%): {len([c for c in confidences if c < 0.5])}")
        print()
        
        # Show individual confidence scores
        print("🔍 Individual Confidence Scores:")
        for result in interpreter_results:
            pid = result.get('property_id')
            conf = result.get('confidence', 0)
            rationale = result.get('rationale', '')[:80] + '...' if len(result.get('rationale', '')) > 80 else result.get('rationale', '')
            print(f"   • Property {pid}: {conf:.2f} ({conf*100:.0f}%) - {rationale}")
        print()
        
        # Test different threshold scenarios
        print("🎯 Threshold Filtering Tests:")
        thresholds = [0.3, 0.5, 0.7, 0.9]
        for threshold in thresholds:
            passing = [c for c in confidences if c >= threshold]
            print(f"   • Threshold {threshold:.1f} ({threshold*100:.0f}%): {len(passing)}/{len(confidences)} suggestions pass")
        print()
        
        # Validate that scores are realistic
        if avg_conf > 0.8:
            print("⚠️  WARNING: Average confidence too high (>80%)")
            return False
        elif avg_conf < 0.3:
            print("⚠️  WARNING: Average confidence too low (<30%)")
            return False
        elif max_conf - min_conf < 0.2:
            print("⚠️  WARNING: Confidence range too narrow (<20%)")
            return False
        else:
            print("✅ Confidence distribution looks realistic!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_runs():
    """Test that confidence scores vary between runs (due to temperature)"""
    
    print("\n🔄 Testing Confidence Variation Across Runs")
    print("=" * 50)
    
    ai_service = AICurationService()
    properties = get_dummy_properties()
    
    test_content = "Martha Ballard's diary from 1785-1812 documenting daily life and medical practices."
    test_url = "https://test.com"
    
    all_confidences = []
    
    try:
        for run in range(3):
            print(f"Run {run + 1}:")
            
            reasoned = ai_service.generate_reasoned_suggestions(
                test_content, test_url, properties
            )
            
            interpreted = ai_service.interpret_confidence(
                reasoned, properties, test_url
            )
            
            if interpreted:
                confidences = [r.get('confidence', 0) for r in interpreted]
                avg_conf = sum(confidences) / len(confidences)
                all_confidences.extend(confidences)
                print(f"   • Average confidence: {avg_conf:.2f}")
            else:
                print(f"   • No confidence interpretations")
        
        if len(all_confidences) > 0:
            # Check for variation
            unique_confidences = set([round(c, 1) for c in all_confidences])
            variation = len(unique_confidences) / len(all_confidences)
            
            print(f"\n📊 Variation Analysis:")
            print(f"   • Total confidence scores: {len(all_confidences)}")
            print(f"   • Unique values (rounded): {len(unique_confidences)}")
            print(f"   • Variation ratio: {variation:.2f}")
            
            if variation > 0.3:  # At least 30% variation
                print("✅ Good variation in confidence scores!")
                return True
            else:
                print("⚠️  Low variation - temperature might be too low")
                return False
        else:
            print("❌ No confidence scores generated")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print(f"🚀 Starting Comprehensive Confidence Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Please set it in your environment.")
        sys.exit(1)
    
    # Run tests
    test1_passed = test_confidence_distribution()
    test2_passed = test_multiple_runs()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   • Confidence distribution test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • Variation across runs test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Confidence system is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        sys.exit(1)
