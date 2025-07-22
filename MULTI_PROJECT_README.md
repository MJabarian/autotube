# AutoTube Multi-Project Architecture

## Overview

AutoTube now supports multiple isolated projects, each with its own configuration, output directories, and settings. This allows you to work on different video series or themes without conflicts.

## Project Structure

```
autotube/
├── project_manager.py          # Manage multiple projects
├── run_project.py             # Run projects easily
├── config/                    # Global configuration
├── src/                       # Shared source code
├── ThroughTheLensofHistory/   # Project 1
│   ├── config.py             # Project-specific config
│   ├── content_generation_pipeline.py
│   ├── audio_video_processor_pipeline.py
│   ├── output/               # Project-specific outputs
│   │   ├── stories/
│   │   ├── images/
│   │   ├── audio/
│   │   ├── videos/
│   │   └── ...
│   ├── data/                 # Project-specific data
│   └── prompts/              # Project-specific prompts
├── Project2/                 # Project 2
│   ├── config.py
│   ├── output/
│   └── ...
└── Project3/                 # Project 3
    ├── config.py
    ├── output/
    └── ...
```

## Key Benefits

1. **Isolated Workspaces**: Each project has its own output directories
2. **Project-Specific Configs**: Custom settings per project
3. **No Conflicts**: Projects don't interfere with each other
4. **Easy Management**: Simple commands to create, switch, and run projects
5. **Shared Code**: Core functionality is shared across projects

## Getting Started

### 1. Create a New Project

```bash
# Create a new project
python project_manager.py create "MyNewProject" --description "My awesome video series" --theme "modern"

# Example
python project_manager.py create "ThroughTheLensofHistory" --description "Historical events through modern lens" --theme "historical"
```

### 2. List All Projects

```bash
python project_manager.py list
```

### 3. Activate a Project

```bash
python project_manager.py activate "ThroughTheLensofHistory"
```

### 4. Run a Project

```bash
# Run content generation pipeline (story, audio, images)
python run_project.py ThroughTheLensofHistory content

# Run video processing pipeline (final video creation)
python run_project.py ThroughTheLensofHistory video

# Or run from the project directory
cd ThroughTheLensofHistory
python content_generation_pipeline.py
```

## Project Configuration

Each project has its own `config.py` file that overrides the global configuration:

```python
# ThroughTheLensofHistory/config.py
class ProjectConfig:
    PROJECT_NAME = "ThroughTheLensofHistory"
    OUTPUT_DIR = PROJECT_ROOT / "output"  # Isolated output directory
    
    class Project:
        THEME = "historical"
        STYLE_DESCRIPTION = "Historical documentary style"
        CONTENT_FOCUS = "Historical events through modern lens"
```

## Output Directory Structure

Each project creates its own isolated output structure:

```
ThroughTheLensofHistory/output/
├── stories/                    # Generated story files
├── images/                     # Generated images
├── audio/                      # TTS audio files
├── videos/                     # Video files
├── music_selections/           # Music selection data
├── mixed_audio/               # Mixed audio files
├── subtitles_processed_video/ # Final videos with subtitles
├── audio_sync_data/           # Whisper sync data
└── logs/                      # Project-specific logs
```

## Project Management Commands

### Create a Project
```bash
python project_manager.py create <project_name> [--description "description"] [--theme "theme"]
```

### List Projects
```bash
python project_manager.py list
```

### Activate a Project
```bash
python project_manager.py activate <project_name>
```

### Check Status
```bash
python project_manager.py status
```

### Delete a Project
```bash
python project_manager.py delete <project_name> [--force]
```

## Running Projects

### Method 1: Using run_project.py (Recommended)
```bash
# From the root directory
python run_project.py ThroughTheLensofHistory content
python run_project.py ThroughTheLensofHistory video
```

### Method 2: Direct Execution
```bash
# Navigate to project directory
cd ThroughTheLensofHistory

# Run pipelines
python content_generation_pipeline.py
python audio_video_processor_pipeline.py
```

## Project-Specific Customization

### Custom Prompts
Each project can have its own prompt templates in `prompts/prompts.yaml`:

```yaml
story_generation:
  system: |
    You are a YouTube Shorts creator specializing in historical content.
    Focus on 'Through The Lens of History' - how historical events shaped our present.
```

### Custom Themes
Projects can have different themes and styles:

- **Historical**: Focus on historical events and figures
- **Modern**: Contemporary topics and trends
- **Scientific**: Science and technology content
- **Mystery**: Unsolved mysteries and conspiracy theories

### Custom Output Naming
Each project can have its own output naming conventions:

```python
class Project:
    OUTPUT_PREFIX = "ThroughTheLens"  # Custom prefix for outputs
```

## Best Practices

1. **Use Descriptive Project Names**: Choose names that clearly identify the project's theme
2. **Keep Projects Focused**: Each project should have a clear, specific theme
3. **Use Project Manager**: Always use the project manager for creating and switching projects
4. **Backup Important Projects**: Consider backing up successful project configurations
5. **Document Project Settings**: Keep notes on what works well for each project

## Migration from Single Project

If you have existing content in the old structure:

1. **Create a new project** for your existing content
2. **Copy relevant files** from the old output directories
3. **Update any hardcoded paths** in your scripts
4. **Test the new project** to ensure everything works

## Troubleshooting

### Project Not Found
```bash
# Check available projects
python project_manager.py list

# Create the project if it doesn't exist
python project_manager.py create <project_name>
```

### Pipeline Scripts Missing
```bash
# Navigate to project directory
cd <project_name>

# Check if pipeline files exist
ls *.py

# If missing, recreate the project
python ../project_manager.py delete <project_name>
python ../project_manager.py create <project_name>
```

### Output Directory Issues
```bash
# Check project config
cat <project_name>/config.py

# Ensure output directories exist
ls <project_name>/output/
```

## Example Workflow

Here's a complete example of creating and running a project:

```bash
# 1. Create a new project
python project_manager.py create "AncientMysteries" --description "Unsolved ancient mysteries" --theme "mystery"

# 2. List projects to confirm
python project_manager.py list

# 3. Activate the project
python project_manager.py activate AncientMysteries

# 4. Run content generation
python run_project.py AncientMysteries content

# 5. Run video processing
python run_project.py AncientMysteries video

# 6. Check outputs
ls AncientMysteries/output/videos/
```

This multi-project architecture gives you the flexibility to work on multiple video series simultaneously while keeping everything organized and isolated! 