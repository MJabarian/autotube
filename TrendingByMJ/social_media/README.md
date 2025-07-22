# YouTube Shorts Poster for AutoTube

A comprehensive YouTube Shorts posting system that supports multiple channels and automatic metadata extraction from your AutoTube content.

## 🚀 Features

- **Multi-Channel Support**: Post to multiple YouTube channels from one system
- **Automatic Metadata**: Extracts title, description, and tags from your story metadata
- **Flexible Posting**: Post to all channels or specific channels
- **Comprehensive Logging**: Track all uploads and errors
- **YouTube Shorts Optimized**: Configured for viral YouTube Shorts content

## 📁 File Structure

```
social_media/
├── youtube_shorts_poster.py     # Main posting script
├── setup_youtube.py             # Interactive setup script
├── youtube_config.json          # Channel configuration (created by setup)
├── youtube_config_template.json # Template configuration
├── requirements_youtube.txt     # Python dependencies
└── README.md                    # This file
```

## 🛠️ Setup

### 1. Install Dependencies

```bash
cd social_media
pip install -r requirements_youtube.txt
```

### 2. Run Setup Script

```bash
python setup_youtube.py
```

This will guide you through setting up your YouTube channels interactively.

### 3. Get YouTube API Credentials

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Create credentials:
   - **API Key** for basic operations
   - **OAuth 2.0 Client ID** for uploads (download as `client_secrets.json`)

### 4. Update Configuration

Edit `youtube_config.json` and add your actual credentials:

```json
{
  "channels": {
    "channel1": {
      "name": "Your Channel Name",
      "api_key": "YOUR_ACTUAL_API_KEY",
      "channel_id": "YOUR_CHANNEL_ID",
      "client_secrets_file": "client_secrets.json",
      "enabled": true
    }
  }
}
```

## 📋 Usage

### List Available Channels

```bash
python youtube_shorts_poster.py --list-channels
```

### Post to All Channels

```bash
python youtube_shorts_poster.py "TheDayBeesStoleaBaseballGame"
```

### Post to Specific Channel

```bash
python youtube_shorts_poster.py "TheDayBeesStoleaBaseballGame" --channel channel1
```

### Get Help

```bash
python youtube_shorts_poster.py --help
python setup_youtube.py --help
```

## 🔧 Configuration

### Channel Settings

Each channel in `youtube_config.json` supports:

- `name`: Display name for the channel
- `api_key`: YouTube API key
- `channel_id`: YouTube channel ID
- `enabled`: Enable/disable channel (true/false)
- `credentials_file`: OAuth2 credentials file path
- `client_secrets_file`: Client secrets file path

### Default Settings

```json
{
  "default_settings": {
    "made_for_kids": false,
    "privacy_status": "public",
    "category_id": "27",
    "tags": ["history", "shorts", "educational", "viral"],
    "language": "en",
    "location": "US"
  }
}
```

### Upload Settings

```json
{
  "upload_settings": {
    "max_retries": 3,
    "timeout_seconds": 300,
    "chunk_size_mb": 10,
    "resumable_upload": true
  }
}
```

## 📊 Metadata Integration

The system automatically extracts metadata from your AutoTube content:

- **Title**: From `output/stories/{topic}/metadata.json`
- **Description**: From `output/stories/{topic}/metadata.json`
- **Tags**: From metadata + default tags
- **Video**: From `output/subtitles_processed_video/{topic}_final.mp4`

## 📝 Logging

All uploads are logged to:
- `output/social_media_logs/youtube_posting_YYYYMMDD_HHMMSS.log`
- `output/social_media_logs/youtube_uploads_YYYYMMDD.json`

## 🔒 Security

- Store API keys securely
- Never commit credentials to version control
- Use environment variables for production
- Regularly rotate API keys

## 🚨 Troubleshooting

### Common Issues

1. **"API Key Invalid"**: Check your API key in the config
2. **"Channel Not Found"**: Verify channel ID in YouTube Studio
3. **"Quota Exceeded"**: YouTube API has daily limits
4. **"Video Not Found"**: Ensure video file exists in correct location

### Debug Mode

Add `--debug` flag for detailed logging:

```bash
python youtube_shorts_poster.py "TopicName" --debug
```

## 📈 Best Practices

1. **Test First**: Use a private video for testing
2. **Monitor Quotas**: YouTube API has daily limits
3. **Backup Config**: Keep backup of your configuration
4. **Regular Updates**: Keep dependencies updated
5. **Error Handling**: Check logs for failed uploads

## 🔄 Integration with AutoTube

This system integrates seamlessly with your AutoTube pipeline:

1. Generate content with `content_generation_pipeline.py`
2. Process video with `audio_video_processor_pipeline.py`
3. Post to YouTube with `youtube_shorts_poster.py`

## 📞 Support

For issues or questions:
1. Check the logs in `output/social_media_logs/`
2. Verify your API credentials
3. Ensure video files exist in the correct locations
4. Check YouTube API quotas and limits 