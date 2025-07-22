"""
AutoTube Project Manager
Manages multiple AutoTube projects with isolated configurations and outputs
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class AutoTubeProjectManager:
    """Manages multiple AutoTube projects with isolated workspaces."""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.projects_file = self.root_dir / "projects.json"
        self.projects = self._load_projects()
    
    def _load_projects(self) -> Dict:
        """Load projects configuration."""
        if self.projects_file.exists():
            with open(self.projects_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_projects(self):
        """Save projects configuration."""
        with open(self.projects_file, 'w') as f:
            json.dump(self.projects, f, indent=2)
    
    def create_project(self, project_name: str, description: str = "", theme: str = "historical") -> bool:
        """
        Create a new AutoTube project with isolated workspace.
        
        Args:
            project_name: Name of the project (e.g., "ThroughTheLensofHistory")
            description: Project description
            theme: Project theme (historical, modern, etc.)
        """
        try:
            # Sanitize project name
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '')
            
            project_dir = self.root_dir / safe_name
            
            if project_dir.exists():
                print(f"❌ Project '{safe_name}' already exists!")
                return False
            
            print(f"🚀 Creating new AutoTube project: {safe_name}")
            
            # Create project directory structure
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create project subdirectories
            (project_dir / "output").mkdir(exist_ok=True)
            (project_dir / "data").mkdir(exist_ok=True)
            (project_dir / "prompts").mkdir(exist_ok=True)
            (project_dir / "topics_used").mkdir(exist_ok=True)
            
            # Create output subdirectories
            output_dirs = [
                "stories", "images", "audio", "videos", "logs",
                "music_selections", "mixed_audio", "subtitles_processed_video", "audio_sync_data"
            ]
            for subdir in output_dirs:
                (project_dir / "output" / subdir).mkdir(exist_ok=True)
            
            # Create project-specific config
            self._create_project_config(project_dir, project_name, description, theme)
            
            # Create project-specific prompts
            self._create_project_prompts(project_dir, project_name, theme)
            
            # Create project pipelines
            self._create_project_pipelines(project_dir, project_name)
            
            # Add to projects registry
            self.projects[safe_name] = {
                "name": project_name,
                "description": description,
                "theme": theme,
                "created": str(Path.cwd()),
                "directory": str(project_dir),
                "active": False
            }
            self._save_projects()
            
            print(f"✅ Project '{safe_name}' created successfully!")
            print(f"📁 Project directory: {project_dir}")
            print(f"📋 To activate this project: python project_manager.py activate {safe_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create project: {e}")
            return False
    
    def _create_project_config(self, project_dir: Path, project_name: str, description: str, theme: str):
        """Create project-specific configuration file."""
        config_content = f'''"""
Project-specific configuration for {project_name}
This config overrides the global config to ensure all outputs go to this project's directory
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Define project-specific paths
PROJECT_ROOT = Path(__file__).parent
PROJECT_NAME = "{project_name}"

# Project-specific directories
PROJECT_OUTPUT_DIR = PROJECT_ROOT / "output"
PROJECT_DATA_DIR = PROJECT_ROOT / "data"
PROJECT_PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Create project directories
def _create_project_directories():
    """Create all necessary directories for this project."""
    for path in [
        PROJECT_OUTPUT_DIR / 'stories',
        PROJECT_OUTPUT_DIR / 'images',
        PROJECT_OUTPUT_DIR / 'audio',
        PROJECT_OUTPUT_DIR / 'videos',
        PROJECT_OUTPUT_DIR / 'logs',
        PROJECT_OUTPUT_DIR / 'music_selections',
        PROJECT_OUTPUT_DIR / 'mixed_audio',
        PROJECT_OUTPUT_DIR / 'subtitles_processed_video',
        PROJECT_OUTPUT_DIR / 'audio_sync_data',
        PROJECT_DATA_DIR,
        PROJECT_PROMPTS_DIR
    ]:
        path.mkdir(parents=True, exist_ok=True)

_create_project_directories()

class ProjectConfig:
    """Project-specific configuration that overrides global config."""
    
    # Project identification
    PROJECT_NAME = PROJECT_NAME
    PROJECT_ROOT = PROJECT_ROOT
    
    # Project-specific directories
    OUTPUT_DIR = PROJECT_OUTPUT_DIR
    DATA_DIR = PROJECT_DATA_DIR
    PROMPTS_DIR = PROJECT_PROMPTS_DIR
    
    # Paths to project-specific template files
    PROMPT_TEMPLATES = PROJECT_PROMPTS_DIR / "prompts.yaml"
    
    # API Keys (loaded from environment variables)
    class API:
        ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
        RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY', '')
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        YOUTUBE_CLIENT_SECRETS = PROJECT_ROOT / "config" / "client_secret.json"
    
    # RunPod settings
    class RUNPOD:
        GPU_TYPE = os.getenv('RUNPOD_GPU_TYPE', 'RTX 3090')
        IMAGE_MODEL = os.getenv('RUNPOD_IMAGE_MODEL', 'flux-dev')
        MAX_IMAGES_PER_BATCH = int(os.getenv('RUNPOD_MAX_IMAGES_PER_BATCH', 20))
        AUTO_SHUTDOWN = os.getenv('RUNPOD_AUTO_SHUTDOWN', 'true').lower() == 'true'
        COST_LIMIT_PER_DAY = float(os.getenv('RUNPOD_COST_LIMIT_PER_DAY', 2.00))

    # OpenAI settings
    class OPENAI:
        API_KEY = os.getenv('OPENAI_API_KEY', '')
        MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    # Video configurations
    class Video:
        # FLUX Schnell 9:16 dimensions (actual generated size from test)
        WIDTH = int(os.getenv('VIDEO_WIDTH', 768))
        HEIGHT = int(os.getenv('VIDEO_HEIGHT', 1344))
        FPS = int(os.getenv('VIDEO_FPS', 30))
        DURATION = int(os.getenv('VIDEO_DURATION', 60))
        BACKGROUND_COLOR = (0, 0, 0)  # Black
        
        class Text:
            FONT = str(PROJECT_ROOT / "assets" / "fonts" / "Roboto-Bold.ttf")
            FONT_SIZE = 72
            COLOR = (255, 255, 255)  # White
            STROKE_COLOR = (0, 0, 0)  # Black
            STROKE_WIDTH = 2
    
    # Project-specific settings
    class Project:
        # Project theme and style
        THEME = "{theme}"
        STYLE_DESCRIPTION = "{description}"
        
        # Content focus
        CONTENT_FOCUS = "Historical events and figures through a modern lens"
        
        # Output naming
        OUTPUT_PREFIX = "{project_name.replace(' ', '')}"
        
        # Project-specific prompts (can override global prompts)
        CUSTOM_PROMPTS = {{
            "story_generation": {{
                "system": "You are a YouTube Shorts creator specializing in {theme} content. Focus on {project_name} - {description}",
                "template": "Create a viral YouTube Short about: {{topic}}\\n\\nFocus on {description}. Use the {project_name} perspective."
            }}
        }}
    
    # Configuration loading/saving methods
    @classmethod
    def load_yaml_config(cls, file_path: str) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {{}}
    
    @classmethod
    def save_yaml_config(cls, config: Dict[str, Any], file_path: str) -> None:
        """Save configuration to a YAML file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)

# Create project paths dictionary for easy access
PROJECT_PATHS = {{
    'PROJECT_ROOT': PROJECT_ROOT,
    'OUTPUT_DIR': PROJECT_OUTPUT_DIR,
    'DATA_DIR': PROJECT_DATA_DIR,
    'PROMPTS_DIR': PROJECT_PROMPTS_DIR,
    'STORIES': PROJECT_OUTPUT_DIR / 'stories',
    'IMAGES': PROJECT_OUTPUT_DIR / 'images',
    'AUDIO': PROJECT_OUTPUT_DIR / 'audio',
    'VIDEOS': PROJECT_OUTPUT_DIR / 'videos',
    'LOGS': PROJECT_OUTPUT_DIR / 'logs',
    'MUSIC_SELECTIONS': PROJECT_OUTPUT_DIR / 'music_selections',
    'MIXED_AUDIO': PROJECT_OUTPUT_DIR / 'mixed_audio',
    'SUBTITLES': PROJECT_OUTPUT_DIR / 'subtitles_processed_video',
    'AUDIO_SYNC': PROJECT_OUTPUT_DIR / 'audio_sync_data'
}}

# Export the project config as the main config for this project
Config = ProjectConfig
PATHS = PROJECT_PATHS
'''
        
        with open(project_dir / "config.py", 'w') as f:
            f.write(config_content)
    
    def _create_project_prompts(self, project_dir: Path, project_name: str, theme: str):
        """Create project-specific prompts file."""
        prompts_content = f'''# Project-specific prompts for {project_name}
# Theme: {theme}

story_generation:
  system: |
    You are a YouTube Shorts creator specializing in {theme} content. 
    Generate a complete 160-170 words for a 60 to 70 seconds short video script with all required metadata.
    Total length: 160-170 words (NOT counting PAUSE TAG or VOICE MODULATION TAGS)
    
    CRITICAL: Create UNIQUE, CREATIVE hooks for every story. Never use generic phrases. Each hook should be specific to the story and immediately grab attention with a unique angle.
    
    LENGTH REQUIREMENT: The story MUST be 160-170 words for 60-70 second video duration.

    VISUAL STORYTELLING REQUIREMENTS:
    - Create stories that are inherently VISUALLY COMPELLING and CINEMATIC
    - Include dramatic scenes, visual contrasts, and memorable moments
    - Use symbolic imagery, atmospheric conditions, and expressive character actions
    - Ensure every story beat has a unique visual identity for image generation

    PERSONALITY:
    Your tone is curious, passionate, and effortlessly cool—like someone who genuinely loves {theme} and can make anyone care about it.
    - Speak naturally, like a smart friend at dinner
    - Be confident, never arrogant
    - Avoid lectures or activism
    - Get to the point fast; assume the viewer is smart but impatient
    - Inject subtle irony or humor when appropriate
    - Only use complex words when needed, a good storyteller doesnt need to brag about his vocabulary.
    - Dont try to sound "viral"—just tell a killer story
    - Dont say cheesy things...
    - End with a surprising insight or question
    - NEVER end with "subscribe", "let me know in the comments" or any robotic call-to-action.
    - Instead, end with something that makes viewers think "wait, what?!" or want to research more.
    - Add a little bit of humor , not cheesy if context allows and only if the story is not sad.
    VOICE MODULATION TAGS:
    - [excited], [sarcastic], [whispers], [curious], [angry], [mysterious], [dramatic], [nervous], [confident], [sad]

    PAUSE TAGS:
    - [pause:0.5s], [pause:1s]
  template: |
    Create a viral YouTube Short about: {{topic}}
    
    REMEMBER: The story MUST be 160-170 words for 60-70 second video duration.

    CRITICAL REQUIREMENT: The "story" field MUST be 160-170 words (NOT counting voice tags).

    STORY STRUCTURE REQUIREMENTS:
    - The story MUST begin with a powerful hook that grabs attention in the first 3 seconds
    - The hook should be the FIRST sentence of the story, using voice tags (e.g., [excited], [curious], etc.)
    - The hook must be emotionally charged, surprising, weird, or shocking
    - Include multiple interesting facts about the event to keep viewers engaged, but dont overload—aim for a balanced, compelling flow. 
    - AVOID generic phrases like "You won't believe this" or "Imagine if" - be creative and unique
    - AVOID using "Picture this" or "Imagine" - these sound cheesy and generic
    - Use diverse, creative openers - the examples below are just good examples, not limited to these:
      * "[shocked] In 1912, a ship sailed into port with no crew..."
      * "[mysterious] The king's secret was buried with him..."
      * "[excited] What happened next changed everything..."
      * "[curious] No one knows why they vanished..."
      * "[dramatic] The truth was hidden for 400 years..."
      * "[nervous] Something was wrong with the painting..."
    - Be creative and original - these are just examples to inspire you
    - Each hook should be unique and specific to the story
    - Use simple, everyday language
    - The hook flows naturally into the rest of the story
    - Maintain proper grammar and punctuation throughout the entire story including the hook

    VISUAL STORYTELLING:
    - Write for 20 visually distinct, cinematic moments
    - Include dramatic scenes, emotional faces, architecture, clothing
    - Include visual contrasts: rich vs poor, indoor vs outdoor, light vs shadow

    ORGANIZATION:
    - All assets (story, images, audio, music selection, etc.) should be saved in subfolders named after the sanitized story title/topic.
    - Each asset type (story, images, audio, music) should have its own subfolder under the main story folder.

    Return your response in this EXACT JSON format: |
      {{
        "title": "Viral title under 60 characters (NO EMOJIS)",
        "story": "Full story (160-170 words) starting with a powerful hook and voice tags, flowing naturally into the narrative with cinematic pacing",
        "description": "Short YouTube description with hashtags",
        "tags": ["tag1", "tag2", "tag3"],
        "keywords": ["keyword1", "keyword2", "keyword3"]
      }}

# Add other prompt templates as needed...
'''
        
        with open(project_dir / "prompts" / "prompts.yaml", 'w') as f:
            f.write(prompts_content)
    
    def _create_project_pipelines(self, project_dir: Path, project_name: str):
        """Create project-specific pipeline files and source code."""
        # Copy the pipeline files from the main directory
        main_pipelines = [
            "content_generation_pipeline.py",
            "audio_video_processor_pipeline.py"
        ]
        
        for pipeline in main_pipelines:
            source = self.root_dir / pipeline
            if source.exists():
                shutil.copy2(source, project_dir / pipeline)
                print(f"📄 Created {pipeline}")
        
        # Copy the entire src directory for complete isolation
        src_source = self.root_dir / "src"
        src_dest = project_dir / "src"
        if src_source.exists():
            shutil.copytree(src_source, src_dest, dirs_exist_ok=True)
            print(f"📁 Copied src directory for complete project isolation")
        
        # Copy requirements.txt and other essential files
        essential_files = ["requirements.txt", ".env.example"]
        for file_name in essential_files:
            source_file = self.root_dir / file_name
            if source_file.exists():
                shutil.copy2(source_file, project_dir / file_name)
                print(f"📄 Copied {file_name}")
    
    def list_projects(self) -> None:
        """List all available projects."""
        if not self.projects:
            print("📋 No projects found. Create your first project with:")
            print("   python project_manager.py create <project_name>")
            return
        
        print("📋 Available AutoTube Projects:")
        print("=" * 50)
        
        for name, info in self.projects.items():
            status = "🟢 ACTIVE" if info.get("active", False) else "⚪ INACTIVE"
            print(f"{status} {name}")
            print(f"   📝 {info.get('description', 'No description')}")
            print(f"   🎨 Theme: {info.get('theme', 'historical')}")
            print(f"   📁 Directory: {info.get('directory', 'Unknown')}")
            print()
    
    def activate_project(self, project_name: str) -> bool:
        """Activate a project (set as current working project)."""
        if project_name not in self.projects:
            print(f"❌ Project '{project_name}' not found!")
            return False
        
        # Deactivate all projects
        for name in self.projects:
            self.projects[name]["active"] = False
        
        # Activate the specified project
        self.projects[project_name]["active"] = True
        self._save_projects()
        
        print(f"✅ Project '{project_name}' activated!")
        print(f"📁 Working directory: {self.projects[project_name]['directory']}")
        print(f"🚀 You can now run the pipeline from the project directory")
        
        return True
    
    def get_active_project(self) -> Optional[str]:
        """Get the currently active project."""
        for name, info in self.projects.items():
            if info.get("active", False):
                return name
        return None
    
    def delete_project(self, project_name: str, force: bool = False) -> bool:
        """Delete a project and all its files."""
        if project_name not in self.projects:
            print(f"❌ Project '{project_name}' not found!")
            return False
        
        if not force:
            confirm = input(f"⚠️  Are you sure you want to delete project '{project_name}' and ALL its files? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Project deletion cancelled.")
                return False
        
        try:
            project_dir = Path(self.projects[project_name]["directory"])
            if project_dir.exists():
                shutil.rmtree(project_dir)
                print(f"🗑️  Deleted project directory: {project_dir}")
            
            del self.projects[project_name]
            self._save_projects()
            
            print(f"✅ Project '{project_name}' deleted successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete project: {e}")
            return False

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="AutoTube Project Manager")
    parser.add_argument("command", choices=["create", "list", "activate", "delete", "status"], 
                       help="Command to execute")
    parser.add_argument("project_name", nargs="?", help="Project name for create/activate/delete commands")
    parser.add_argument("--description", "-d", help="Project description (for create command)")
    parser.add_argument("--theme", "-t", default="historical", help="Project theme (for create command)")
    parser.add_argument("--force", "-f", action="store_true", help="Force deletion without confirmation")
    
    args = parser.parse_args()
    
    manager = AutoTubeProjectManager()
    
    if args.command == "create":
        if not args.project_name:
            print("❌ Project name required for create command!")
            sys.exit(1)
        success = manager.create_project(args.project_name, args.description or "", args.theme)
        sys.exit(0 if success else 1)
    
    elif args.command == "list":
        manager.list_projects()
    
    elif args.command == "activate":
        if not args.project_name:
            print("❌ Project name required for activate command!")
            sys.exit(1)
        success = manager.activate_project(args.project_name)
        sys.exit(0 if success else 1)
    
    elif args.command == "delete":
        if not args.project_name:
            print("❌ Project name required for delete command!")
            sys.exit(1)
        success = manager.delete_project(args.project_name, args.force)
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        active_project = manager.get_active_project()
        if active_project:
            print(f"🟢 Active project: {active_project}")
            print(f"📁 Directory: {manager.projects[active_project]['directory']}")
        else:
            print("⚪ No active project")
            print("💡 Use 'python project_manager.py activate <project_name>' to activate a project")

if __name__ == "__main__":
    main() 