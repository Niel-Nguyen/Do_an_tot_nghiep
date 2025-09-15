#!/usr/bin/env python3
"""
Script test hệ thống recommendation engine cải tiến
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recommendation_engine import recommendation_engine

def test_basic_functionality():
    """Test chức năng cơ bản"""
    print("🧪 Testing basic functionality...")
    
    test_cases = [
        {
            "name": "High Protein + Gym Diet",
            "input": "Tôi muốn ăn món giàu protein, ít chất béo, phù hợp cho người tập gym",
            "expected_diet": ['high-protein', 'low-fat']
        },
        {
            "name": "Vegetarian Diet", 
            "input": "Tôi ăn chay, không thích thịt cá, thích rau củ và đậu phụ",
            "expected_diet": ['chay']
        },
        {
            "name": "Regional Preference",
            "input": "Tôi thích món miền Nam, cay cay, có tôm và cua", 
            "expected_region": ['south'],
            "expected_ingredients": ['seafood']
        },
        {
            "name": "Health Conditions",
            "input": "Tôi muốn giảm cân, ăn clean, không dầu mỡ, món hấp hoặc luộc",
            "expected_health": ['weight-loss'],
            "expected_methods": ['steamed', 'boiled']
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Test case: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        # Test phân tích sở thích
        analysis = recommendation_engine.analyze_preferences(test_case['input'])
        print(f"Analysis: {analysis}")
        
        # Kiểm tra kết quả mong đợi
        if 'expected_diet' in test_case:
            for diet in test_case['expected_diet']:
                if diet in analysis['diet_type']:
                    print(f"✅ Diet '{diet}' detected correctly")
                else:
                    print(f"❌ Diet '{diet}' not detected")
        
        if 'expected_region' in test_case:
            for region in test_case['expected_region']:
                if region in analysis['regional_preferences']:
                    print(f"✅ Region '{region}' detected correctly")
                else:
                    print(f"❌ Region '{region}' not detected")
        
        if 'expected_ingredients' in test_case:
            for ingredient in test_case['expected_ingredients']:
                if ingredient in analysis['liked_ingredients']:
                    print(f"✅ Ingredient '{ingredient}' detected correctly")
                else:
                    print(f"❌ Ingredient '{ingredient}' not detected")
        
        if 'expected_health' in test_case:
            for health in test_case['expected_health']:
                if health in analysis['health_conditions']:
                    print(f"✅ Health condition '{health}' detected correctly")
                else:
                    print(f"❌ Health condition '{health}' not detected")
        
        if 'expected_methods' in test_case:
            for method in test_case['expected_methods']:
                if method in analysis['cooking_methods']:
                    print(f"✅ Cooking method '{method}' detected correctly")
                else:
                    print(f"❌ Cooking method '{method}' not detected")

def test_recommendation_generation():
    """Test tạo đề xuất"""
    print("\n\n🎯 Testing recommendation generation...")
    
    test_inputs = [
        "Tôi muốn ăn món giàu protein, ít béo, phù hợp cho người tập gym",
        "Tôi ăn chay, thích rau xanh và đậu phụ", 
        "Tôi thích hải sản, món miền Nam, cay cay một chút",
        "Tôi muốn giảm cân, ăn clean, món hấp hoặc luộc"
    ]
    
    for i, input_text in enumerate(test_inputs, 1):
        print(f"\n📊 Test {i}: {input_text}")
        
        try:
            recommendations = recommendation_engine.get_recommendations(input_text, top_k=5)
            
            if recommendations:
                print(f"✅ Generated {len(recommendations)} recommendations")
                
                # Kiểm tra diversity của confidence scores
                confidence_scores = [rec['confidence'] for rec in recommendations]
                unique_scores = len(set(confidence_scores))
                print(f"📈 Confidence diversity: {unique_scores}/{len(confidence_scores)} unique scores")
                
                # Hiển thị top 3 recommendations
                for j, rec in enumerate(recommendations[:3], 1):
                    dish = rec['dish']
                    dish_name = recommendation_engine._get_dish_attr(dish, 'name', 'Unknown')
                    confidence = rec['confidence']
                    reasons = rec['reasons']
                    
                    print(f"  {j}. {dish_name} - {confidence}% confidence")
                    print(f"     Reasons: {', '.join(reasons[:2])}")
                
            else:
                print("❌ No recommendations generated")
                
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")

def test_ai_reason_generation():
    """Test tạo lý do bằng AI"""
    print("\n\n🤖 Testing AI reason generation...")
    
    # Load một món ăn mẫu để test
    if recommendation_engine.dishes:
        sample_dish = recommendation_engine.dishes[0]
        dish_name = recommendation_engine._get_dish_attr(sample_dish, 'name', 'Test Dish')
        
        print(f"Testing with dish: {dish_name}")
        
        # Test analysis
        test_analysis = {
            'diet_type': ['high-protein', 'low-fat'],
            'liked_ingredients': ['seafood'],
            'cooking_methods': ['steamed'],
            'health_conditions': ['weight-loss']
        }
        
        basic_reasons = ["Giàu protein", "Ít chất béo"]
        
        try:
            ai_reasons = recommendation_engine._generate_ai_reasons(
                sample_dish, test_analysis, basic_reasons
            )
            
            print(f"✅ AI generated reasons: {ai_reasons}")
            
            if len(ai_reasons) > len(basic_reasons):
                print("✅ AI generated more diverse reasons than basic ones")
            else:
                print("⚠️  AI fallback to basic reasons (might be expected)")
                
        except Exception as e:
            print(f"❌ AI reason generation failed: {e}")
    else:
        print("❌ No dishes loaded for testing")

def test_vegetarian_classification():
    """Test phân loại chay/mặn cải tiến"""
    print("\n\n🥬 Testing vegetarian/meat classification...")
    
    if recommendation_engine.dishes:
        # Test với 10 món đầu tiên
        for i, dish in enumerate(recommendation_engine.dishes[:10]):
            dish_name = recommendation_engine._get_dish_attr(dish, 'name', f'Dish {i}')
            classification = recommendation_engine._classify_vegetarian_meat(dish)
            
            print(f"{i+1}. {dish_name} -> {classification}")
            
        print("✅ Vegetarian classification test completed")
    else:
        print("❌ No dishes loaded for testing")

def run_performance_test():
    """Test hiệu suất"""
    print("\n\n⚡ Testing performance...")
    
    import time
    
    test_input = "Tôi muốn ăn món giàu protein, ít béo, phù hợp tập gym"
    
    # Test thời gian phân tích sở thích
    start_time = time.time()
    analysis = recommendation_engine.analyze_preferences(test_input)
    analysis_time = time.time() - start_time
    print(f"⏱️  Preference analysis: {analysis_time:.3f}s")
    
    # Test thời gian tạo đề xuất
    start_time = time.time()
    recommendations = recommendation_engine.get_recommendations(test_input, top_k=10)
    recommendation_time = time.time() - start_time
    print(f"⏱️  Recommendation generation: {recommendation_time:.3f}s")
    
    # Test thời gian format HTML
    start_time = time.time()
    html_output = recommendation_engine.format_recommendation_response(recommendations, test_input)
    format_time = time.time() - start_time
    print(f"⏱️  HTML formatting: {format_time:.3f}s")
    
    total_time = analysis_time + recommendation_time + format_time
    print(f"🏁 Total time: {total_time:.3f}s")
    
    if total_time < 2.0:
        print("✅ Performance is good (< 2s)")
    elif total_time < 5.0:
        print("⚠️  Performance is acceptable (2-5s)")
    else:
        print("❌ Performance is slow (> 5s)")

def main():
    """Main test runner"""
    print("🚀 Starting Enhanced Recommendation Engine Tests")
    print("=" * 60)
    
    try:
        # Test cơ bản
        test_basic_functionality()
        
        # Test tạo đề xuất
        test_recommendation_generation()
        
        # Test phân loại chay/mặn
        test_vegetarian_classification()
        
        # Test AI (có thể fail nếu không có API key)
        test_ai_reason_generation()
        
        # Test hiệu suất
        run_performance_test()
        
        print("\n\n✅ All tests completed!")
        print("Note: Some AI features may not work without proper API configuration.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()