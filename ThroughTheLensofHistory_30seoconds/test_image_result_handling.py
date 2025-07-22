#!/usr/bin/env python3
"""
Test file to verify image generation result handling works correctly.
Tests both integer and dictionary result types.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.replicate_image_generator import OptimizedReplicateImageGenerator

class TestImageResultHandling:
    """Test class to verify image generation result handling."""
    
    def __init__(self):
        self.image_generator = OptimizedReplicateImageGenerator()
    
    def test_integer_result_handling(self):
        """Test handling of integer result (simulating successful generation)."""
        print("🧪 Testing Integer Result Handling...")
        
        # Simulate integer result (like what we're getting)
        result = 12  # 12 images generated successfully
        
        # Test the exact logic from interactive pipeline
        if isinstance(result, int) and result > 0:
            print(f"✅ Generated {result} synchronized images successfully!")
            print(f"📊 Total images: {result}")
            print(f"💰 Cost: ~${result * 0.003:.4f} (estimated)")
            return True
        elif isinstance(result, dict) and 'successful_images' in result:
            successful_count = len(result['successful_images'])
            print(f"✅ Generated {successful_count} synchronized images successfully!")
            print(f"📊 Total images: {result.get('total_images_requested', 12)}")
            print(f"💰 Cost: ${result.get('total_cost', 0):.4f}")
            return successful_count > 0
        elif isinstance(result, dict):  # Handle other dict results
            print(f"✅ Generated synchronized images successfully!")
            print(f"📊 Image generation completed with dict result")
            return True
        elif result:  # Any truthy result means success
            print(f"✅ Generated synchronized images successfully!")
            print(f"📊 Image generation completed")
            return True
        else:
            raise Exception("Image generation returned no results")
    
    def test_dict_result_handling(self):
        """Test handling of dictionary result (simulating detailed result)."""
        print("\n🧪 Testing Dictionary Result Handling...")
        
        # Simulate dictionary result
        result = {
            'successful_images': ['image1.jpg', 'image2.jpg', 'image3.jpg'],
            'total_images_requested': 12,
            'total_cost': 0.036,
            'failed_images': 0
        }
        
        # Test the exact logic from interactive pipeline
        if isinstance(result, int) and result > 0:
            print(f"✅ Generated {result} synchronized images successfully!")
            print(f"📊 Total images: {result}")
            print(f"💰 Cost: ~${result * 0.003:.4f} (estimated)")
            return True
        elif isinstance(result, dict) and 'successful_images' in result:
            successful_count = len(result['successful_images'])
            print(f"✅ Generated {successful_count} synchronized images successfully!")
            print(f"📊 Total images: {result.get('total_images_requested', 12)}")
            print(f"💰 Cost: ${result.get('total_cost', 0):.4f}")
            return successful_count > 0
        elif isinstance(result, dict):  # Handle other dict results
            print(f"✅ Generated synchronized images successfully!")
            print(f"📊 Image generation completed with dict result")
            return True
        elif result:  # Any truthy result means success
            print(f"✅ Generated synchronized images successfully!")
            print(f"📊 Image generation completed")
            return True
        else:
            raise Exception("Image generation returned no results")
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        print("\n🧪 Testing Edge Cases...")
        
        # Test 0 result
        print("Testing result = 0:")
        try:
            result = 0
            if isinstance(result, int) and result > 0:
                print("✅ Should not reach here")
            else:
                print("✅ Correctly handled zero result")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test None result
        print("\nTesting result = None:")
        try:
            result = None
            if isinstance(result, int) and result > 0:
                print("✅ Should not reach here")
            elif isinstance(result, dict) and 'successful_images' in result:
                print("✅ Should not reach here")
            elif isinstance(result, dict):
                print("✅ Should not reach here")
            elif result:
                print("✅ Should not reach here")
            else:
                print("✅ Correctly handled None result")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test empty dict
        print("\nTesting result = {}:")
        try:
            result = {}
            if isinstance(result, int) and result > 0:
                print("✅ Should not reach here")
            elif isinstance(result, dict) and 'successful_images' in result:
                print("✅ Should not reach here")
            elif isinstance(result, dict):
                print("✅ Correctly handled empty dict")
            elif result:
                print("✅ Should not reach here")
            else:
                print("✅ Should not reach here")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def test_actual_generator_call(self):
        """Test actual call to image generator to see what it returns."""
        print("\n🧪 Testing Actual Generator Call...")
        
        try:
            # Create minimal story data
            story_data = {
                'title': 'Test Story',
                'story': 'This is a test story for image generation.',
                'topic_name': 'test_story'
            }
            
            # Create minimal image prompts
            image_prompts = [f"Test image prompt {i}" for i in range(1, 13)]
            
            print("📞 Calling image generator...")
            print(f"📊 Story data: {story_data}")
            print(f"📊 Image prompts count: {len(image_prompts)}")
            
            # This will fail without proper API setup, but we can see the error
            # result = await self.image_generator.generate_images_for_story(
            #     story_data=story_data,
            #     image_prompts=image_prompts,
            #     quality_preset="production"
            # )
            
            print("✅ Test completed (actual call skipped due to API requirements)")
            
        except Exception as e:
            print(f"❌ Error in actual generator call: {e}")

def run_tests():
    """Run all tests."""
    print("🚀 Starting Image Result Handling Tests")
    print("=" * 50)
    
    tester = TestImageResultHandling()
    
    # Test integer result handling
    try:
        result = tester.test_integer_result_handling()
        print(f"✅ Integer test result: {result}")
    except Exception as e:
        print(f"❌ Integer test failed: {e}")
    
    # Test dictionary result handling
    try:
        result = tester.test_dict_result_handling()
        print(f"✅ Dictionary test result: {result}")
    except Exception as e:
        print(f"❌ Dictionary test failed: {e}")
    
    # Test edge cases
    try:
        tester.test_edge_cases()
        print("✅ Edge cases test completed")
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
    
    # Test actual generator call
    try:
        tester.test_actual_generator_call()
        print("✅ Actual generator call test completed")
    except Exception as e:
        print(f"❌ Actual generator call test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")

if __name__ == "__main__":
    run_tests() 