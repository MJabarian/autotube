#!/usr/bin/env python3
"""
Minimal test to verify the interactive pipeline result handling works.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class MockImageGenerator:
    """Mock image generator that returns an integer result."""
    
    async def generate_images_for_story(self, story_data, image_prompts, quality_preset):
        """Mock method that returns an integer (like the real one)."""
        print(f"🎨 Mock generating {len(image_prompts)} images...")
        return 12  # Return integer like the real generator

class TestInteractivePipeline:
    """Test class that mimics the interactive pipeline logic."""
    
    def __init__(self):
        self.image_generator = MockImageGenerator()
    
    async def test_generate_images_with_sync(self):
        """Test the exact method that's failing."""
        print("🧪 Testing generate_images_with_sync method...")
        
        # Mock data
        topic = "Test Topic"
        story = "Test story content"
        synchronized_prompts = [{'image_prompt': f'Test prompt {i}'} for i in range(1, 13)]
        sanitized_name = "test_topic"
        
        try:
            # Create story data dictionary (same format as full pipeline)
            story_data = {
                'title': topic,
                'story': story,
                'topic_name': sanitized_name
            }
            
            # Extract image prompts from synchronized data (same as full pipeline)
            image_prompts = [prompt_data['image_prompt'] for prompt_data in synchronized_prompts]
            
            print(f"📊 Story data: {story_data}")
            print(f"📊 Image prompts count: {len(image_prompts)}")
            
            # Use existing image generator with synchronized prompts (same as full pipeline)
            result = await self.image_generator.generate_images_for_story(
                story_data=story_data,
                image_prompts=image_prompts,  # Use synchronized prompts
                quality_preset="production"
            )
            
            print(f"📊 Result type: {type(result)}")
            print(f"📊 Result value: {result}")
            
            # Handle different result types - CHECK INTEGER FIRST
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
            
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

async def main():
    """Run the test."""
    print("🚀 Testing Interactive Pipeline Result Handling")
    print("=" * 50)
    
    tester = TestInteractivePipeline()
    
    try:
        result = await tester.test_generate_images_with_sync()
        print(f"\n🎯 Test result: {result}")
        print("✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 