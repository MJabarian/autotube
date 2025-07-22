# 🚨 Content Sensitivity Guide for TrendingByMJ

## 🎯 **Overview**

The TrendingByMJ pipeline now includes robust content sensitivity detection and handling to ensure appropriate treatment of sensitive topics.

## ⚠️ **Sensitive Content Detection**

### **Current Sensitive Topics:**
1. **Dog the Bounty Hunter** - Tragic family incident (accidental shooting)
2. **Malcolm-Jamal Warner** - Death of beloved actor
3. **Future topics** - Automatically detected based on keywords

### **Sensitivity Levels:**
- **`high`** - Tragic events, deaths, accidents, family tragedies
- **`medium`** - Controversial topics, scandals, legal issues
- **`low`** - Standard news, entertainment, sports

## 🛡️ **Protection Mechanisms**

### **1. Automatic Detection**
```python
# Topics are tagged with sensitivity information
{
    "topic": "dog the bounty hunter",
    "sensitivity_level": "high",
    "content_approach": "skip_or_respectful_tribute_only",
    "trending_reason": "Tragic family incident involving accidental shooting"
}
```

### **2. User Prompt System**
When sensitive content is detected:
```
================================================================================
⚠️  SENSITIVE CONTENT DETECTED: DOG THE BOUNTY HUNTER
================================================================================
📰 This topic involves sensitive content: Tragic family incident involving accidental shooting of grandson by wife's son
🎯 Recommended approach: skip_or_respectful_tribute_only

❓ Do you want to skip this sensitive topic? (y/n): 
```

### **3. Content Approach Options**
- **`skip`** - Automatically skip the topic
- **`skip_or_respectful_tribute_only`** - Skip or create respectful tribute
- **`factual_reporting_only`** - Stick to facts, avoid sensationalism
- **`proceed_with_caution`** - Proceed but with extra care

## 📝 **Content Guidelines**

### **✅ APPROPRIATE for Sensitive Topics:**
- Factual reporting of events
- Respectful tributes and condolences
- Focus on impact and community response
- Professional, dignified tone
- Emphasis on family privacy and respect

### **❌ INAPPROPRIATE for Sensitive Topics:**
- Sensationalist language
- Graphic details of tragic events
- Speculation about personal matters
- Disrespectful or mocking tone
- Exploitation of tragedy for entertainment

## 🔄 **Pipeline Integration**

### **Step 1: Topic Detection**
- Trending fetcher identifies sensitive topics
- Tags with appropriate sensitivity level
- Provides context about why it's sensitive

### **Step 2: User Decision**
- Pipeline shows sensitivity warning
- User chooses to proceed or skip
- Clear explanation of recommended approach

### **Step 3: Content Generation**
- If proceeding, uses respectful prompts
- Focuses on factual reporting
- Avoids sensationalist language

### **Step 4: Final Review**
- User reviews generated content
- Can reject if not appropriate
- Ensures respectful treatment

## 📊 **Example: Dog the Bounty Hunter**

### **❌ WRONG Approach:**
```
"Dog the Bounty Hunter's Family Drama Explodes!"
"Shocking details about the tragic incident..."
"Reality TV star's family in chaos..."
```

### **✅ RIGHT Approach:**
```
"Tragic Incident: Dog the Bounty Hunter Family Faces Heartbreak"
"TMZ reports tragic family incident involving accidental shooting, family requests privacy during difficult time"
"Fans express condolences for the Chapman family during this difficult time"
```

## 🎯 **Implementation Details**

### **Sensitivity Keywords:**
- death, died, passed away, tragedy, tragic
- shooting, accident, incident, killed
- family, privacy, condolences, mourning
- sensitive, controversial, scandal

### **Respectful Language Patterns:**
- "Family requests privacy"
- "During this difficult time"
- "Thoughts and prayers"
- "Respect for the family"
- "Tragic incident"

## 🚀 **Future Enhancements**

### **Planned Features:**
1. **Real-time news API integration** - Get current context
2. **AI content analysis** - Automatic sensitivity detection
3. **Community guidelines** - User-defined sensitivity rules
4. **Content moderation** - Pre-approval system for sensitive topics

### **Machine Learning Integration:**
- Train models on appropriate vs inappropriate content
- Automatic flagging of potentially problematic topics
- Sentiment analysis for respectful tone detection

## 📋 **Best Practices**

### **For Content Creators:**
1. **Always verify context** - Check why a topic is trending
2. **Consider timing** - Be extra sensitive during immediate aftermath
3. **Respect privacy** - Don't exploit personal tragedies
4. **Focus on facts** - Avoid speculation and rumors
5. **Show empathy** - Use respectful, compassionate language

### **For Pipeline Users:**
1. **Review sensitivity warnings** - Don't ignore them
2. **Consider family impact** - Think about those affected
3. **Choose appropriate approach** - Skip if unsure
4. **Review final content** - Ensure it's respectful
5. **Report issues** - Flag inappropriate content

## 🎯 **Summary**

The TrendingByMJ pipeline now provides:
- ✅ **Automatic sensitivity detection**
- ✅ **User choice and control**
- ✅ **Respectful content guidelines**
- ✅ **Protection against inappropriate content**
- ✅ **Clear decision-making process**

This ensures that trending topics are handled with appropriate care and respect, especially for sensitive or tragic events. 