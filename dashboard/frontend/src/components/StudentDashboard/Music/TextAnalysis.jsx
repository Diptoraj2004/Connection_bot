import React, { useState } from 'react';
import GeminiService from '../../../services/geminiService';

const TextAnalysis = ({ platform, onComplete, isAnalyzing, setIsAnalyzing }) => {
  const [text, setText] = useState('');
  const [wordCount, setWordCount] = useState(0);

  const handleTextChange = (e) => {
    const value = e.target.value;
    setText(value);
    setWordCount(value.trim().split(' ').filter(word => word.length > 0).length);
  };

  const analyzeText = async () => {
    if (text.trim().length < 10) {
      alert('Please write at least a few words about how you\'re feeling');
      return;
    }
    
    setIsAnalyzing(true);
    try {
      const moodAnalysis = await GeminiService.analyzeTextEmotion(text);
      const songs = await GeminiService.getSongRecommendations(moodAnalysis, platform);
      
      onComplete(moodAnalysis, songs);
    } catch (error) {
      console.error('Text analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const promptSuggestions = [
    "I'm feeling stressed about upcoming exams...",
    "Today has been really overwhelming...",
    "I'm excited about the weekend plans...",
    "Feeling a bit lonely and need some comfort...",
    "Had a great day and want to celebrate...",
    "Going through some anxiety right now..."
  ];

  return (
    <div className="text-analysis">
      <div className="text-input-container">
        <h3>📝 Tell Us How You're Feeling</h3>
        <p>Describe your current mood, emotions, or what's on your mind</p>
        
        <textarea
          value={text}
          onChange={handleTextChange}
          placeholder="Write about your feelings, mood, or current situation..."
          className="mood-textarea"
          rows={6}
        />
        
        <div className="text-stats">
          <span className="word-count">Words: {wordCount}</span>
          <span className="min-words">(Minimum 5 words recommended)</span>
        </div>

        <div className="prompt-suggestions">
          <p>Need inspiration? Try one of these prompts:</p>
          <div className="suggestions-grid">
            {promptSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setText(suggestion)}
                className="suggestion-btn"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        <div className="text-actions">
          <button 
            onClick={analyzeText} 
            className="analyze-btn"
            disabled={isAnalyzing || text.trim().length < 5}
          >
            {isAnalyzing ? '🔄 Analyzing...' : '🧠 Get Music Recommendations'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TextAnalysis;
