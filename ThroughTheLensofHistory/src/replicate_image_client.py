"""
IMPROVED Replicate Image Client for AutoTube - Optimized for Viral Video Quality
Based on Replicate's official documentation and best practices
"""

import os
import replicate
import yaml
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
class OptimizedPromptEnhancer:
    """Streamlined prompt enhancement that focuses on what actually works."""
    
    def __init__(self):
        # SINGLE source of truth for style
        self.core_style = (
            "highlydetailed cinematic illustration, Baroque painting fused with 1970ter film aesthetic, "
            "dramatic chiaroscuro lighting, Rembrandt-style shadows, warm candlelit interiors, "
            "expressive faces with consistent proportions, painterly texture"
        )
        
        # AGGRESSIVE text prevention (put at START of prompt for maximum impact)
        self.text_prevention = (
            "NO TEXT NO WRITING NO LETTERS NO DOCUMENTS NO BOOKS NO NEWSPAPERS NO SIGNS "
            "NO LABELS NO LOGOS NO WRITTEN MATERIAL OF ANY KIND"
        )
        
        # COMPREHENSIVE negative prompt focused on text prevention
        self.negative_prompt = (
            # TEXT PREVENTION (most important - listed first)
            "text, writing, letters, words, documents, books, newspapers, magazines, "
            "signs, posters, labels, logos, captions, subtitles, headlines, articles, "
            "writtenmaterial, readable text, typography, fonts, characters, symbols, "
            "numbers, equations, formulas, handwriting, calligraphy, inscriptions, "
            
            # QUALITY ISSUES
            "blurry, low quality, out of focus, poorly drawn face, distorted face, "
            "disfigured, extra limbs, mutated hands, extra fingers, bad anatomy, "
            "ugly,boring composition, poor lighting, overexposed, underexposed, "
            "noise, artifacts, deformed, low resolution, pixelated, watermark, signature, "
            
            # ANACHRONISTIC ELEMENTS  
            "modern clothing, modern technology, modern buildings, cars, smartphones, "
            "contemporary items, digital screens, LED lights, plastic materials"
        )

    def enhance_prompt(self, base_prompt: str) -> str:
        """Create optimized prompt with text prevention FIRST for maximum impact."""
        # Build prompt in optimal order: Text prevention → Base prompt → Style
        enhanced = f"{self.text_prevention}, {base_prompt}, {self.core_style}"
        return enhanced.strip()

    def get_negative_prompt(self) -> str:
        """The comprehensive negative prompt."""
        return self.negative_prompt

class OptimizedReplicateImageClient:
    """
    OPTIMIZED Replicate client for maximum image quality and viral content.
    
    Key improvements based on Replicate docs:
    - Optimal parameter settings for FLUX Schnell/Dev
    - Multiple model support with automatic fallback
    - Quality-focused configuration for viral content
    - Proper aspect ratios for social media
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_key:
            raise ValueError("REPLICATE_API_TOKEN environment variable is required")
        
        # Set the API token for the replicate client
        os.environ["REPLICATE_API_TOKEN"] = self.api_key
        
        # Initialize the new prompt enhancer
        self.prompt_enhancer = OptimizedPromptEnhancer()
        
        # Load negative prompt from project-specific or global prompts.yaml
        try:
            from src.prompt_resolver import PROMPTS
            self.negative_prompt = PROMPTS.get("negative_prompt") or self.prompt_enhancer.get_negative_prompt()
        except Exception:
            self.negative_prompt = self.prompt_enhancer.get_negative_prompt()
        
        # Model setup - ONLY Schnell enabled for cost optimization
        self.models = {
            "flux-schnell": "black-forest-labs/flux-schnell",
        }
        
        self.default_model = "flux-schnell"
        self.images_dir = Config.OUTPUT_DIR / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Cost tracking
        self.total_cost = 0.0
        self.images_generated = 0
        self.model_costs = {
            "flux-schnell": 0.003
        }

    def generate_image(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None,
        model: str = None,
        quality_mode: str = "balanced",  # Only Schnell is enabled
        aspect_ratio: str = "9:16",    # Perfect for YouTube Shorts - ALWAYS DEFAULT TO THIS
        enhance_prompt: bool = True,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
          Generate optimized image for viral content.
        Args:
            prompt: Base image prompt
            negative_prompt: What to avoid in image
            model: Specific model to use ("flux-schnell", "flux-dev", "flux-pro")
            quality_mode: "fast" (Schnell), "balanced" (Dev), "premium" (Pro)
            aspect_ratio: "9:16" (Shorts), "16:9" (landscape), "1:1" (square)
            enhance_prompt: Add viral content optimizations to prompt
            seed: For reproducible results
        """
        
        # Auto-select model based on quality mode (only Schnell available)
        if not model:
            model = self.default_model  # Always use Schnell for cost optimization
        
        # Get optimal settings for the model
        model_settings = self._get_model_settings(model, aspect_ratio)
        
        # Enhance prompt using new system
        if enhance_prompt:
            prompt = self._enhance_prompt_for_viral(prompt)
        
        # Use optimized negative prompt (unless user provides their own)
        final_negative_prompt = negative_prompt or self.negative_prompt
        
        # Prepare optimized input parameters
        input_params = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,  # Use the aspect_ratio parameter (9:16)
            "num_inference_steps": model_settings["steps"],
            "guidance_scale": model_settings["guidance_scale"],
            "num_outputs": 1,
            "scheduler": model_settings["scheduler"],
            "output_format": "jpg",
            "output_quality": 95  # Maximum quality for viral content
        }
        
        # Add negative prompt if provided
        if negative_prompt or self.negative_prompt:
            input_params["negative_prompt"] = negative_prompt or self.negative_prompt
        else:
            # Always include negative prompt by default
            input_params["negative_prompt"] = self._load_negative_prompt()
        
        # Add seed if provided
        if seed is not None:
            input_params["seed"] = seed
        
        # Model-specific optimizations
        if model == "flux-schnell":
            # Schnell works best with guidance_scale=0 and 1-4 steps
            input_params["guidance_scale"] = 0.0
            input_params["num_inference_steps"] = min(4, input_params["num_inference_steps"])
        # Remove dev/pro logic
        
        try:
            start_time = time.time()
            
            print(f"🎨 Generating with {model} ({quality_mode} quality)...")
            print(f"📐 Aspect ratio: {input_params['aspect_ratio']}")
            print(f"⚙️ Steps: {input_params['num_inference_steps']}, Guidance: {input_params['guidance_scale']}")
            
            # Generate with Replicate
            output = replicate.run(
                self.models[model],
                input=input_params
            )
            
            generation_time = time.time() - start_time
            cost = self.model_costs[model]
            self.total_cost += cost
            self.images_generated += 1
            
            return {
                "success": True,
                "output": output,
                "generation_time": generation_time,
                "cost": cost,
                "prompt": prompt,
                "model": model,
                "quality_mode": quality_mode,
                "settings": input_params
            }
            
        except Exception as e:
            # No fallback - just return error since we only use Schnell
            return {"error": f"Generation failed: {str(e)}"}

    def _get_model_settings(self, model: str, aspect_ratio: str) -> Dict[str, Any]:
        """Get optimal settings for Schnell model based on Replicate documentation."""
        # FLUX Schnell uses aspect_ratio parameter, not custom dimensions
        # The model will automatically choose the correct dimensions for each aspect ratio
        dimensions = {
            "9:16": {"aspect_ratio": "9:16"},  # YouTube Shorts/TikTok
            "16:9": {"aspect_ratio": "16:9"},  # Landscape/YouTube
            "1:1": {"aspect_ratio": "1:1"},    # Square/Instagram
            "4:3": {"aspect_ratio": "4:3"},    # Traditional
            "3:2": {"aspect_ratio": "3:2"},    # Photography
        }
        base_settings = dimensions.get(aspect_ratio, dimensions["9:16"])
        return {
            **base_settings,
            "steps": 4,              # Schnell optimized for 1-4 steps
            "guidance_scale": 0.0,   # Schnell doesn't use guidance
            "scheduler": "simple"    # Best for Schnell
        }

    def _enhance_prompt_for_viral(self, prompt: str) -> str:
        """Enhance prompts using the new optimized system."""
        return self.prompt_enhancer.enhance_prompt(prompt)

    def generate_and_download_image(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None, 
        story_folder: Optional[str] = None, 
        idx: int = 0,
        quality_mode: str = "balanced",
        aspect_ratio: str = "9:16",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate and download optimized image for viral content."""
        
        # Generate the image with optimizations
        gen_result = self.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            quality_mode=quality_mode,
            aspect_ratio=aspect_ratio,
            enhance_prompt=kwargs.get("enhance_prompt", True),
            seed=kwargs.get("seed"),
            model=kwargs.get("model")
        )
        
        if "error" in gen_result:
            return gen_result
        
        # Extract image data from output
        output = gen_result.get("output", [])
        if not output:
            return {"error": "No image data in generation output"}
        
        # Save image with quality mode in filename
        quality_suffix = {
            "fast": "_fast",
            "balanced": "_hq", 
            "premium": "_ultra"
        }.get(quality_mode, "")
        
        if story_folder:
            story_dir = self.images_dir / story_folder
            story_dir.mkdir(parents=True, exist_ok=True)
            image_path = story_dir / f"image_{idx+1:02d}{quality_suffix}.jpg"
        else:
            image_path = self.images_dir / f"image_{idx+1:02d}{quality_suffix}.jpg"
        
        # Download and save the image
        dl_result = self.download_image(output, save_path=str(image_path))
        
        if "error" in dl_result:
            return dl_result
        
        return {
            "image_path": str(image_path),
            "prompt": prompt,
            "download_url": dl_result.get("download_url"),
            "generation_time": gen_result.get("generation_time", 0),
            "cost": gen_result.get("cost", 0),
            "quality_mode": quality_mode,
            "model_used": gen_result.get("model"),
            "settings": gen_result.get("settings", {})
        }

    def download_image(self, image_data, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Download image with retry logic for reliability."""
        try:
            # Handle different output formats
            if isinstance(image_data, list) and len(image_data) > 0:
                image_url = image_data[0]
            elif isinstance(image_data, str):
                image_url = image_data
            else:
                return {"error": f"Unexpected image data format: {type(image_data)}"}
            
            # Download with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(image_url, timeout=60)
                    if response.status_code == 200:
                        break
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        return {"error": f"Download failed after {max_retries} attempts: {e}"}
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            if response.status_code != 200:
                return {"error": f"Download failed: {response.status_code}"}
            
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"💾 Saved high-quality image: {save_path}")
            
            return {
                "image_bytes": response.content,
                "image_path": save_path,
                "download_url": image_url,
                "file_size": len(response.content)
            }
            
        except Exception as e:
            return {"error": f"Download failed: {str(e)}"}

    def batch_generate_for_viral_video(
        self,
        prompts: List[str],
        story_folder: str,
        quality_mode: str = "balanced",
        fallback_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Optimized batch generation for viral video content.
        Only Schnell model is supported.
        """
        print(f"🎬 Starting batch generation: {len(prompts)} images")
        print(f"🎯 Using optimized prompts with aggressive text prevention")
        print(f"💰 Estimated cost: ${len(prompts) * self.model_costs['flux-schnell']:.2f}")
        results = []
        successful = 0
        total_cost = 0
        
        for i, prompt in enumerate(prompts):
            print(f"\n📸 Generating image {i+1}/{len(prompts)}")
            
            # Retry logic for failed generations
            max_retries = 3
            retry_delay = 15  # 15 seconds between retries
            
            for attempt in range(max_retries):
                result = self.generate_and_download_image(
                    prompt=prompt,
                    story_folder=story_folder,
                    idx=i,
                    quality_mode=quality_mode,
                    aspect_ratio="9:16",  # Optimized for viral content
                    # No need to pass negative_prompt - using optimized default
                )
                
                if "error" not in result:
                    successful += 1
                    total_cost += result.get("cost", 0)
                    print(f"✅ Success! Running cost: ${total_cost:.3f}")
                    break
                else:
                    print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {result['error']}")
                    
                    if attempt < max_retries - 1:
                        print(f"⏳ Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                    else:
                        print(f"❌ Failed after {max_retries} attempts - skipping image {i+1}")
            
            results.append(result)
            time.sleep(0.5)  # Small delay between images
            
        return {
            "total_images": len(prompts),
            "successful_images": successful,
            "failed_images": len(prompts) - successful,
            "total_cost": total_cost,
            "final_quality_mode": quality_mode,
            "results": results,
            "average_cost_per_image": total_cost / max(1, successful)
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Enhanced usage statistics."""
        return {
            "total_images": self.images_generated,
            "total_cost": self.total_cost,
            "avg_cost_per_image": self.total_cost / max(1, self.images_generated),
            "estimated_monthly_cost": self.total_cost * (30 * 6),  # 6 videos per day
            "model_costs": self.model_costs,
            "recommended_quality": self._recommend_quality_mode()
        }
    
    def _recommend_quality_mode(self) -> str:
        """Recommend quality mode based on usage patterns."""
        avg_cost = self.total_cost / max(1, self.images_generated)
        
        if avg_cost < 0.01:
            return "You're using fast mode efficiently!"
        elif avg_cost < 0.05:
            return "Balanced mode is perfect for your use case"
        else:
            return "Consider using balanced or fast mode to reduce costs"

    def _load_negative_prompt(self) -> str:
        """Load optimized negative prompt for viral content."""
        try:
            from src.prompt_resolver import PROMPTS
            return PROMPTS.get("negative_prompt", "")
        except Exception as e:
            print(f"[WARNING] Failed to load negative prompt: {e}")
            # Comprehensive negative prompt to avoid common issues
            return (
                "blurry, low quality, out of focus, poorly drawn face, distorted face, disfigured, "
                "extra limbs, mutated hands, extra fingers, watermark, signature, text, writing, "
                "logo, label, document, book, newspaper, modern clothing, modern tech, "
                "ugly, bad anatomy, boring composition, poor lighting, overexposed, underexposed, "
                "noise, artifacts, deformed, low resolution, pixelated"
            )
    
    def _load_style_enhancer(self) -> str:
        """Load style enhancer for viral content."""
        try:
            from src.prompt_resolver import PROMPTS
            return PROMPTS.get("default_image_style", "")
        except Exception as e:
            print(f"[WARNING] Failed to load style guide: {e}")
            # Baroque/1970ngster style guide
            return (
                "highlydetailed cinematic illustration in the style of a Baroque painting fused with 1970gangster films, "
                "dramatic chiaroscuro lighting, expressive faces, sharp shadows, warm candlelit interiors, "
                "Rembrandt-style intensity, hyper-realistic but stylized characters, consistent facial proportions, "
                "painterly texture (do not include any text, written material, or logos in the image)"
            )

    def cleanup_images(self) -> Dict[str, Any]:
        """Cleanup method for compatibility."""
        return {
            "status": "success", 
            "message": "Replicate predictions auto-cleanup after completion"
        }

# Quality presets for different use cases
QUALITY_PRESETS = {
    "mvp_testing": {
        "quality_mode": "fast",
        "model": "flux-schnell", 
        "enhance_prompt": True,
        "cost_per_video": 0.06  # 20 images × $0.003
    },
    "production": {
        "quality_mode": "balanced",
        "model": "flux-schnell",
        "enhance_prompt": True, 
        "cost_per_video": 0.06  # 20 images × $0.003
    },
    "premium_content": {
        "quality_mode": "premium",
        "model": "flux-schnell",
        "enhance_prompt": True,
        "cost_per_video": 0.06  # 20 images × $0.003
    }
}

# Example usage with quality presets
def create_viral_images_with_presets(story_title: str, prompts: List[str], preset: str = "production"):
    """Create viral images using quality presets."""
    
    client = OptimizedReplicateImageClient()
    config = QUALITY_PRESETS[preset]
    
    print(f"🎬 Creating viral images with '{preset}' preset")
    print(f"💰 Estimated cost: ${config['cost_per_video']:.2f}")
    
    return client.batch_generate_for_viral_video(
        prompts=prompts,
        story_folder=story_title,
        quality_mode=config["quality_mode"]
    )