import { GoogleGenerativeAI } from '@google/generative-ai';

const API_KEY = process.env.REACT_APP_GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(API_KEY);

class GeminiService {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
  }

  async analyzeFaceEmotion(imageData) {
    const prompt = `
    Analyze the facial expression in this image. Look at the eyes, eyebrows, mouth, and overall expression.
    
    Return ONLY a JSON object (no other text) with this exact format:
    {
      "mood": "one of: happy, sad, anxious, angry, neutral, stressed, excited, calm, tired, frustrated, romantic, nostalgic, dancing",
      "intensity": "one of: low, medium, high",
      "musicGenres": ["3 specific genres that would help this mood"],
      "description": "detailed description of what you see in the face"
    }
    `;

    try {
      const result = await this.model.generateContent([prompt, imageData]);
      const response = await result.response;
      const text = response.text().trim();
      
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      
      throw new Error('Invalid JSON response');
    } catch (error) {
      console.error('Face analysis error:', error);
      return this.generateRandomMoodResponse();
    }
  }

  async analyzeVoiceEmotion(audioTranscript, audioFeatures) {
    const prompt = `
    Analyze this text for emotional content. The text is: "${audioTranscript}"
    
    Look for keywords, tone indicators, and emotional expressions.
    
    Return ONLY a JSON object (no other text) with this exact format:
    {
      "mood": "one of: happy, sad, anxious, angry, neutral, stressed, excited, calm, tired, frustrated, romantic, nostalgic, dancing",
      "intensity": "one of: low, medium, high",
      "musicGenres": ["3 specific genres that would help this mood"],
      "description": "what emotions you detected and why"
    }
    `;

    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      const text = response.text().trim();
      
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      
      throw new Error('Invalid JSON response');
    } catch (error) {
      console.error('Voice analysis error:', error);
      return this.generateRandomMoodResponse();
    }
  }

  async analyzeTextEmotion(text) {
    const prompt = `
    Analyze this text for emotional content and mood: "${text}"
    
    Look for:
    - Emotional words (sad, happy, stressed, excited, etc.)
    - Context clues (exams, relationships, work, memories, dancing, etc.)
    - Intensity of language
    - Overall sentiment
    
    Return ONLY a JSON object (no other text) with this exact format:
    {
      "mood": "one of: happy, sad, anxious, angry, neutral, stressed, excited, calm, tired, frustrated, romantic, nostalgic, dancing",
      "intensity": "one of: low, medium, high",
      "musicGenres": ["3 specific genres that would help this mood"],
      "description": "what emotions you detected from the text and why"
    }
    `;

    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      const text = response.text().trim();
      
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      
      throw new Error('Invalid JSON response');
    } catch (error) {
      console.error('Text analysis error:', error);
      return this.generateRandomMoodResponse();
    }
  }

  async getSongRecommendations(moodAnalysis, platform = 'youtube') {
    const prompt = `
    Based on this mood: ${moodAnalysis.mood} (${moodAnalysis.intensity} intensity)
    Preferred genres: ${moodAnalysis.musicGenres.join(', ')}
    
    Student prefers mix of Hindi/Bengali and international modern songs.
    
    Recommend 8-10 diverse songs that would help improve or complement this emotional state.
    Include both regional Indian songs and international hits from 2015-2024.
    
    Return ONLY a JSON array (no other text) with this format:
    [
      {
        "title": "Exact song title",
        "artist": "Exact artist name", 
        "reason": "Why this song helps with ${moodAnalysis.mood}",
        "searchQuery": "Song Title Artist Name"
      }
    ]
    `;

    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      const text = response.text().trim();
      
      const jsonMatch = text.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        const songs = JSON.parse(jsonMatch[0]);
        return songs.length > 0 ? songs : this.getMoodSpecificSongs(moodAnalysis.mood);
      }
      
      throw new Error('Invalid JSON response');
    } catch (error) {
      console.error('Song recommendation error:', error);
      return this.getMoodSpecificSongs(moodAnalysis.mood);
    }
  }

  generateRandomMoodResponse() {
    const moods = ['happy', 'sad', 'anxious', 'calm', 'excited', 'stressed', 'neutral', 'tired', 'romantic', 'nostalgic', 'dancing'];
    const intensities = ['low', 'medium', 'high'];
    const genres = [
      ['pop', 'indie', 'acoustic'],
      ['bollywood', 'bengali', 'folk'],
      ['rock', 'electronic', 'jazz'],
      ['r&b', 'soul', 'alternative']
    ];
    
    const randomMood = moods[Math.floor(Math.random() * moods.length)];
    const randomIntensity = intensities[Math.floor(Math.random() * intensities.length)];
    const randomGenres = genres[Math.floor(Math.random() * genres.length)];
    
    return {
      mood: randomMood,
      intensity: randomIntensity,
      musicGenres: randomGenres,
      description: `Detected ${randomMood} mood with ${randomIntensity} intensity`
    };
  }

  getMoodSpecificSongs(mood) {
    const songDatabase = {
      happy: [
        // Your curated songs
        { title: "Dugga Elo", artist: "Monali Thakur", reason: "Festive Bengali celebration", searchQuery: "Dugga Elo Monali Thakur" },
        { title: "Love You Zindagi", artist: "Amit Trivedi", reason: "Uplifting life celebration", searchQuery: "Love You Zindagi Amit Trivedi" },
        // Modern additions
        { title: "Good 4 U", artist: "Olivia Rodrigo", reason: "High energy pop anthem", searchQuery: "Good 4 U Olivia Rodrigo" },
        { title: "Anti-Hero", artist: "Taylor Swift", reason: "Catchy upbeat vibes", searchQuery: "Anti Hero Taylor Swift" },
        { title: "As It Was", artist: "Harry Styles", reason: "Feel-good modern pop", searchQuery: "As It Was Harry Styles" },
        { title: "Levitating", artist: "Dua Lipa", reason: "Dance-pop energy", searchQuery: "Levitating Dua Lipa" }
      ],
      
      excited: [
        // Same as happy + extras
        { title: "Dugga Elo", artist: "Monali Thakur", reason: "Festive celebration energy", searchQuery: "Dugga Elo Monali Thakur" },
        { title: "Love You Zindagi", artist: "Amit Trivedi", reason: "Celebratory vibes", searchQuery: "Love You Zindagi Amit Trivedi" },
        { title: "Watermelon Sugar", artist: "Harry Styles", reason: "Summer excitement", searchQuery: "Watermelon Sugar Harry Styles" },
        { title: "Blinding Lights", artist: "The Weeknd", reason: "High energy rush", searchQuery: "Blinding Lights The Weeknd" },
        { title: "Industry Baby", artist: "Lil Nas X", reason: "Confident energy", searchQuery: "Industry Baby Lil Nas X" }
      ],
      
      dancing: [
        // Your curated songs
        { title: "Ghagra", artist: "Pritam", reason: "Perfect Bollywood dance track", searchQuery: "Ghagra Yeh Jawaani Hai Deewani" },
        { title: "Saree Ke Fall Sa", artist: "Nakash Aziz", reason: "Groovy dance number", searchQuery: "Saree Ke Fall Sa R Rajkumar" },
        { title: "Balam Pichkari", artist: "Pritam", reason: "High energy dance celebration", searchQuery: "Balam Pichkari Yeh Jawaani Hai Deewani" },
        // Modern additions  
        { title: "Don't Start Now", artist: "Dua Lipa", reason: "Perfect dance floor track", searchQuery: "Don't Start Now Dua Lipa" },
        { title: "Shut Up and Dance", artist: "Walk the Moon", reason: "Energetic dance anthem", searchQuery: "Shut Up and Dance Walk the Moon" },
        { title: "Can't Stop the Feeling", artist: "Justin Timberlake", reason: "Irresistible dance vibes", searchQuery: "Can't Stop the Feeling Justin Timberlake" }
      ],
      
      romantic: [
        // Your curated songs
        { title: "Ei Bhalo Ei Kharap", artist: "Arijit Singh", reason: "Beautiful Bengali love song", searchQuery: "Ei Bhalo Ei Kharap Arijit Singh" },
        { title: "Jeno Tomari Kache", artist: "Ash King", reason: "Romantic Bengali melody", searchQuery: "Jeno Tomari Kache Ash King" },
        { title: "Ogochalo Mon", artist: "Talpatar Sepai", reason: "Soulful Bengali romance", searchQuery: "Ogochalo Mon Talpatar Sepai" },
        { title: "I Wanna Be Yours", artist: "Arctic Monkeys", reason: "Intimate love confession", searchQuery: "I Wanna Be Yours Arctic Monkeys" },
        // Modern additions
        { title: "Perfect", artist: "Ed Sheeran", reason: "Modern romantic ballad", searchQuery: "Perfect Ed Sheeran" },
        { title: "Adore You", artist: "Harry Styles", reason: "Sweet romantic feelings", searchQuery: "Adore You Harry Styles" },
        { title: "Golden", artist: "Harry Styles", reason: "Romantic golden hour vibes", searchQuery: "Golden Harry Styles" }
      ],
      
      nostalgic: [
        // Your curated songs
        { title: "Summer of 69", artist: "Bryan Adams", reason: "Classic nostalgic anthem", searchQuery: "Summer of 69 Bryan Adams" },
        { title: "Night Changes", artist: "One Direction", reason: "Bittersweet memories", searchQuery: "Night Changes One Direction" },
        { title: "Photograph", artist: "Ed Sheeran", reason: "Memory lane feelings", searchQuery: "Photograph Ed Sheeran" },
        { title: "See You Again", artist: "Charlie Puth", reason: "Emotional remembrance", searchQuery: "See You Again Charlie Puth Wiz Khalifa" },
        // Modern additions
        { title: "Drivers License", artist: "Olivia Rodrigo", reason: "Coming of age nostalgia", searchQuery: "Drivers License Olivia Rodrigo" },
        { title: "Before You Go", artist: "Lewis Capaldi", reason: "Emotional reflection", searchQuery: "Before You Go Lewis Capaldi" },
        { title: "Someone You Loved", artist: "Lewis Capaldi", reason: "Missing someone deeply", searchQuery: "Someone You Loved Lewis Capaldi" }
      ],
      
      sad: [
        { title: "Channa Mereya", artist: "Arijit Singh", reason: "Soulful Hindi heartbreak", searchQuery: "Channa Mereya Arijit Singh" },
        { title: "Someone Like You", artist: "Adele", reason: "Processing sadness", searchQuery: "Someone Like You Adele" },
        { title: "Mad World", artist: "Gary Jules", reason: "Melancholic comfort", searchQuery: "Mad World Gary Jules" },
        { title: "Hurt", artist: "Johnny Cash", reason: "Deep emotional processing", searchQuery: "Hurt Johnny Cash" },
        { title: "When the Party's Over", artist: "Billie Eilish", reason: "Quiet sadness", searchQuery: "When the Party's Over Billie Eilish" },
        { title: "Therefore I Am", artist: "Billie Eilish", reason: "Moody introspection", searchQuery: "Therefore I Am Billie Eilish" }
      ],
      
      anxious: [
        { title: "Breathe Me", artist: "Sia", reason: "Calming for anxiety", searchQuery: "Breathe Me Sia" },
        { title: "Weightless", artist: "Marconi Union", reason: "Scientifically proven anxiety relief", searchQuery: "Weightless Marconi Union" },
        { title: "Heavy", artist: "Linkin Park ft. Kiiara", reason: "Addresses anxiety feelings", searchQuery: "Heavy Linkin Park Kiiara" },
        { title: "Easy On Me", artist: "Adele", reason: "Self-compassion for anxiety", searchQuery: "Easy On Me Adele" },
        { title: "Lovely", artist: "Billie Eilish & Khalid", reason: "Gentle anxiety comfort", searchQuery: "Lovely Billie Eilish Khalid" }
      ],
      
      stressed: [
        { title: "Clair de Lune", artist: "Claude Debussy", reason: "Classical stress relief", searchQuery: "Clair de Lune Debussy" },
        { title: "Holocene", artist: "Bon Iver", reason: "Peaceful and meditative", searchQuery: "Holocene Bon Iver" },
        { title: "Mad About You", artist: "Sting", reason: "Gentle and soothing", searchQuery: "Mad About You Sting" },
        { title: "Budapest", artist: "George Ezra", reason: "Calming folk vibes", searchQuery: "Budapest George Ezra" },
        { title: "Lost in the Light", artist: "Bahamas", reason: "Relaxing indie comfort", searchQuery: "Lost in the Light Bahamas" }
      ],
      
      calm: [
        { title: "Skinny Love", artist: "Bon Iver", reason: "Peaceful introspection", searchQuery: "Skinny Love Bon Iver" },
        { title: "Flightless Bird", artist: "Iron & Wine", reason: "Gentle acoustic calm", searchQuery: "Flightless Bird Iron Wine" },
        { title: "Holocene", artist: "Bon Iver", reason: "Meditative serenity", searchQuery: "Holocene Bon Iver" },
        { title: "River", artist: "Leon Bridges", reason: "Soulful peace", searchQuery: "River Leon Bridges" },
        { title: "Cherry Wine", artist: "Hozier", reason: "Warm acoustic comfort", searchQuery: "Cherry Wine Hozier" }
      ],
      
      neutral: [
        { title: "Sunflower", artist: "Post Malone & Swae Lee", reason: "Easy listening vibes", searchQuery: "Sunflower Post Malone Swae Lee" },
        { title: "Shape of You", artist: "Ed Sheeran", reason: "Popular feel-good track", searchQuery: "Shape of You Ed Sheeran" },
        { title: "Stay", artist: "The Kid LAROI & Justin Bieber", reason: "Modern pop comfort", searchQuery: "Stay Kid LAROI Justin Bieber" },
        { title: "Heat Waves", artist: "Glass Animals", reason: "Chill indie vibes", searchQuery: "Heat Waves Glass Animals" }
      ]
    };

    return songDatabase[mood] || songDatabase.happy || [];
  }
}

export default new GeminiService();