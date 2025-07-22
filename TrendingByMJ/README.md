# TrendingByMJ 🚀

**Automated Trending Topics Video Generator for YouTube Shorts**

TrendingByMJ automatically fetches trending topics from Google Trends, generates engaging summaries, and creates professional 20-30 second YouTube Shorts with 6 images and Ken Burns effects.

## 🎯 Features

- **🔍 Google Trends Integration**: Fetches top 5 trending topics in the US
- **📝 AI Summary Generation**: Creates engaging 20-30 second summaries using GPT
- **🎬 Video Generation**: Produces professional videos with 6 images and Ken Burns effects
- **📊 History Tracking**: Avoids repeating topics from the last 7 days
- **🎵 Audio Processing**: TTS generation with background music mixing
- **📱 YouTube Shorts Optimized**: 768x1344 vertical format, perfect for mobile

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd TrendingByMJ

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key"
export REPLICATE_API_KEY="your_replicate_api_key"
```

### 2. Configuration

Edit `config.py` to customize:
- Number of trending topics (default: 5)
- Video duration (default: 20-30 seconds)
- Number of images (default: 6)
- TTS voice and other settings

### 3. Run the Pipeline

```bash
# Run the complete pipeline
python trending_full_pipeline.py

# Or test individual components
python test_trending_components.py
```

## 📁 Project Structure

```
TrendingByMJ/
├── config.py                          # Configuration settings
├── trending_full_pipeline.py          # Main pipeline
├── test_trending_components.py        # Component tests
├── requirements.txt                   # Dependencies
├── src/
│   ├── trending_fetcher.py           # Google Trends integration
│   ├── trending_summary_generator.py # AI summary generation
│   ├── video_composition/            # Video processing
│   ├── llm/                          # Language model integration
│   └── utils/                        # Utility functions
├── partial_pipelines/                # Pipeline components
├── prompts/
│   └── trending_prompts.yaml         # AI prompts
├── data/                             # Trending history
└── output/                           # Generated content
    ├── stories/                      # Generated summaries
    ├── audio/                        # TTS audio files
    ├── videos/                       # Final videos
    └── images/                       # Generated images
```

## 🔧 Configuration

### Trending Topics Settings

```python
# In config.py
TRENDING_CONFIG = {
    "country": "US",              # Country for trends
    "max_topics": 5,              # Number of topics to fetch
    "timeframe": "1d",            # Timeframe (1d = last 24 hours)
    "min_search_volume": 50,      # Minimum search volume
}
```

### Video Settings

```python
VIDEO_CONFIG = {
    "num_images": 6,              # Number of images per video
    "target_duration_min": 20,    # Minimum duration (seconds)
    "target_duration_max": 30,    # Maximum duration (seconds)
    "width": 768,                 # Video width
    "height": 1344,               # Video height (vertical)
    "fps": 30,                    # Frames per second
}
```

## 🎬 Pipeline Flow

1. **🔍 Fetch Trending Topics**
   - Connects to Google Trends API
   - Fetches top trending searches in the US
   - Filters out recently used topics
   - Gets search volume and context

2. **📝 Generate Story Data**
   - Uses GPT to create engaging summaries
   - Optimizes for 20-30 second duration
   - Generates compelling titles
   - Creates story data compatible with existing pipeline
   - Determines appropriate music category

3. **🎤 Whisper Audio Synchronization**
   - Generates TTS audio from story
   - Uses Whisper to get exact word timestamps
   - Creates 6 synchronized image prompts
   - Ensures perfect audio-image timing

4. **🎨 Generate Images**
   - Uses existing Replicate image generator
   - Generates 6 images based on Whisper-synchronized prompts
   - Optimized for YouTube Shorts format
   - Uses story-based image generation pipeline

5. **🎵 Audio Processing**
   - Converts story to speech using TTS
   - Mixes with background music (based on story category)
   - Ensures perfect timing with Whisper sync

6. **🎬 Create Videos**
   - Combines 6 images with Ken Burns effects
   - Adds synchronized audio and subtitles
   - Creates professional YouTube Shorts

7. **📊 Track History**
   - Saves used topics to avoid repetition
   - Maintains search volume data
   - Cleans up old entries

## 🧪 Testing

### Basic Component Tests

Run component tests to verify everything works:

```bash
python test_trending_components.py
```

This will test:
- ✅ Configuration loading
- ✅ Google Trends fetching
- ✅ Summary generation
- ✅ Video composer
- ✅ Pipeline integration

### Story Integration Tests

Test that trending topics work with the existing story-based pipeline:

```bash
python test_trending_story_integration.py
```

This will test:
- ✅ Trending fetcher integration
- ✅ Story data compatibility
- ✅ Content generation pipeline integration
- ✅ Image generation with 6 images
- ✅ Whisper audio synchronization
- ✅ Video composer with 6 images

## 📊 Output

### Generated Files

For each trending topic, the pipeline creates:

```
output/
├── stories/
│   └── [topic_name]/
│       ├── story.json              # Complete story data
│       └── summary.txt             # Human-readable summary
├── audio/
│   └── [topic_name]/
│       └── audio_[topic_name].mp3  # TTS audio
├── images/
│   └── [topic_name]/
│       ├── image_1.jpg             # Generated images
│       ├── image_2.jpg
│       └── ...
└── videos/
    └── [topic_name]_kenburns.mp4   # Final video
```

### Video Specifications

- **Format**: MP4 (H.264)
- **Resolution**: 768x1344 (vertical)
- **Duration**: 20-30 seconds
- **FPS**: 30
- **Audio**: AAC, 320kbps
- **Quality**: High (CRF 18)

## 🔑 API Keys Required

1. **OpenAI API Key**: For GPT summary generation
2. **Replicate API Key**: For AI image generation

Set these as environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export REPLICATE_API_KEY="r8_..."
```

## 🎯 Use Cases

- **Content Creators**: Automatically generate trending content
- **News Channels**: Create quick news summaries
- **Social Media**: Generate viral short-form content
- **Marketing**: Stay current with trending topics

## 🚨 Important Notes

- **Rate Limiting**: Google Trends has rate limits, so the pipeline includes delays
- **API Costs**: OpenAI and Replicate API calls incur costs
- **Content Quality**: Review generated content before publishing
- **Copyright**: Ensure compliance with platform guidelines

## 🔄 Running Regularly

To run the pipeline regularly:

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/TrendingByMJ && python trending_full_pipeline.py
```

## 🐛 Troubleshooting

### Common Issues

1. **No trending topics found**
   - Check internet connection
   - Verify Google Trends API access
   - Try different timeframes

2. **Summary generation fails**
   - Verify OpenAI API key
   - Check API quota
   - Review error logs

3. **Video creation fails**
   - Ensure Replicate API key is set
   - Check disk space
   - Verify image generation

### Logs

Check logs in `output/logs/` for detailed error information.

## 📈 Performance

Typical pipeline performance:
- **Trending fetch**: 30-60 seconds
- **Summary generation**: 2-3 minutes
- **Image generation**: 5-10 minutes
- **Video creation**: 3-5 minutes
- **Total time**: 10-20 minutes for 5 videos

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Open an issue on GitHub

---

**TrendingByMJ** - Making trending content creation effortless! 🚀 