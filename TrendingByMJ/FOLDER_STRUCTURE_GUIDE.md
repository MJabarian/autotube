# 📁 TrendingByMJ Folder Structure & Naming Guide

## 🎯 **Complete Pipeline Overview**

When you run `trending_full_pipeline.py`, here's exactly what gets created:

## 📂 **Root Directory Structure**
```
TrendingByMJ/
├── data/
│   └── trending_history.json          # Tracks used topics (7-day avoidance)
├── output/
│   ├── logs/                          # Pipeline logs with timestamps
│   ├── stories/                       # Story data for each topic
│   ├── audio/                         # TTS audio files
│   ├── images/                        # Generated images (6 per topic)
│   ├── videos/                        # Final videos with subtitles
│   ├── summaries/                     # Generated summaries
│   ├── music_selections/              # Music selection data
│   └── audio_sync_data/               # Whisper synchronization data
└── trending_full_pipeline.py          # Main pipeline script
```

## 🎬 **For Malcolm-Jamal Warner Example**

When you run the pipeline for "malcolm jamal warner", here's what gets created:

### **1. Story Data**
```
output/stories/malcolm_jamal_warner/
└── story.json                         # Complete story data with title, summary, image prompt
```

### **2. Audio Files**
```
output/audio/malcolm_jamal_warner/
├── story_audio.mp3                    # TTS audio from story
└── mixed_audio.mp3                    # TTS + background music
```

### **3. Images (6 total)**
```
output/images/malcolm_jamal_warner/
├── image_1.png                        # Whisper-synchronized image 1
├── image_2.png                        # Whisper-synchronized image 2
├── image_3.png                        # Whisper-synchronized image 3
├── image_4.png                        # Whisper-synchronized image 4
├── image_5.png                        # Whisper-synchronized image 5
└── image_6.png                        # Whisper-synchronized image 6
```

### **4. Final Video**
```
output/videos/
└── malcolm_jamal_warner_kenburns.mp4  # Final video with subtitles
```

### **5. Supporting Data**
```
output/summaries/
└── malcolm_jamal_warner_summary.json  # Generated summary package

output/music_selections/malcolm_jamal_warner/
└── music_selection.json               # Music selection data

output/audio_sync_data/
└── malcolm_jamal_warner_whisper_sync.json  # Whisper timing data
```

## 🔄 **History Tracking**

### **History File Location**
```
data/trending_history.json
```

### **History Structure**
```json
{
  "topics": [
    {
      "topic": "malcolm jamal warner",
      "used_date": "2024-01-15T10:30:00",
      "search_volume": 95,
      "video_created": true
    }
  ],
  "last_updated": "2024-01-15T10:30:00"
}
```

### **History Rules**
- ✅ **Avoids topics from last 7 days** (configurable)
- ✅ **Tracks search volume and usage date**
- ✅ **Prevents duplicate content**
- ✅ **Auto-updates when videos are created**

## 🎯 **Interactive Approval Process**

When you run the pipeline, you'll see:

```
================================================================================
📰 STORY #1: MALCOLM JAMAL WARNER
================================================================================
📊 Search Volume: 95
⏱️ Estimated Duration: 34.8s
🎵 Music Category: Somber

📝 TITLE: Heartbroken Fans Mourn Malcolm-Jamal Warner's Sudden Loss

📰 STORY CONTENT:
BREAKING: Malcolm-Jamal Warner, the beloved star known for his role as Theo Huxtable...

🎨 IMAGE PROMPT:
A poignant, cinematic scene capturing the essence of remembrance and legacy...
================================================================================

❓ Do you approve this story for 'malcolm jamal warner'? (y/n/skip): 
```

### **Approval Options**
- **`y` or `yes`**: ✅ Approve and create video
- **`n` or `no`**: ❌ Reject and move to next topic
- **`s` or `skip`**: ⏭️ Skip and move to next topic

## 📊 **Pipeline Flow Summary**

1. **🔍 Fetch Trending Topics** → Gets 5 topics, filters out recent ones
2. **📝 Generate Summaries** → Creates stories, shows for approval
3. **✅ User Approval** → You approve/reject each story
4. **🎬 Create Videos** → Only for approved stories
5. **📝 Update History** → Marks topics as used

## 🎯 **Key Benefits**

### **✅ Perfect Organization**
- Each topic gets its own folder
- Clear naming conventions
- No file conflicts

### **✅ History Management**
- Never repeats recent topics
- Tracks what's been created
- 7-day avoidance period

### **✅ User Control**
- Approve stories before creation
- Skip topics you don't want
- Full control over content

### **✅ Complete Pipeline**
- 6 images per video
- Perfect audio synchronization
- Subtitled final videos

## 🚀 **Ready to Run!**

The pipeline is now ready with:
- ✅ Interactive story approval
- ✅ History tracking
- ✅ Perfect folder organization
- ✅ 6-image alignment
- ✅ Complete video generation

Run: `python trending_full_pipeline.py` 