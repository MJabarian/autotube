"""
AutoTube Project Runner
Simple script to run AutoTube projects from their directories
"""

import os
import sys
import subprocess
from pathlib import Path

def run_project(project_name: str, pipeline: str = "content"):
    """
    Run an AutoTube project pipeline.
    
    Args:
        project_name: Name of the project directory
        pipeline: Which pipeline to run ("content" or "video")
    """
    project_dir = Path(project_name)
    
    if not project_dir.exists():
        print(f"❌ Project directory '{project_name}' not found!")
        print("💡 Available projects:")
        for item in Path(".").iterdir():
            if item.is_dir() and (item / "config.py").exists():
                print(f"   📁 {item.name}")
        return False
    
    if not (project_dir / "config.py").exists():
        print(f"❌ Project '{project_name}' is not a valid AutoTube project!")
        return False
    
    # Change to project directory
    os.chdir(project_dir)
    
    # Run the appropriate pipeline
    if pipeline == "content":
        script = "content_generation_pipeline.py"
    elif pipeline == "video":
        script = "audio_video_processor_pipeline.py"
    else:
        print(f"❌ Unknown pipeline: {pipeline}")
        print("💡 Available pipelines: content, video")
        return False
    
    if not Path(script).exists():
        print(f"❌ Pipeline script '{script}' not found in project '{project_name}'!")
        return False
    
    print(f"🚀 Running {pipeline} pipeline for project: {project_name}")
    print(f"📁 Working directory: {project_dir.absolute()}")
    print(f"📄 Script: {script}")
    print("=" * 50)
    
    try:
        # Run the script
        result = subprocess.run([sys.executable, script], check=True)
        print("✅ Pipeline completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline failed with exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        return False

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("AutoTube Project Runner")
        print("Usage:")
        print("  python run_project.py <project_name> [pipeline]")
        print("")
        print("Pipelines:")
        print("  content  - Generate story, audio, and images (default)")
        print("  video    - Process audio and create final video")
        print("")
        print("Examples:")
        print("  python run_project.py ThroughTheLensofHistory")
        print("  python run_project.py ThroughTheLensofHistory content")
        print("  python run_project.py ThroughTheLensofHistory video")
        return
    
    project_name = sys.argv[1]
    pipeline = sys.argv[2] if len(sys.argv) > 2 else "content"
    
    success = run_project(project_name, pipeline)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 