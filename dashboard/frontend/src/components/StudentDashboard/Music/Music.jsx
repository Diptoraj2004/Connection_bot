import React, { useState } from 'react';
import PlatformSelector from './PlatformSelector';
import FaceAnalysis from './FaceAnalysis';
import VoiceAnalysis from './VoiceAnalysis';
import TextAnalysis from './TextAnalysis';
import MusicPlayer from './MusicPlayer';
import singers from '../../../assets/images/singers.jpg';
import './Music.css';

const Music = () => {
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [analysisType, setAnalysisType] = useState(null);
  const [moodAnalysis, setMoodAnalysis] = useState(null);
  const [songRecommendations, setSongRecommendations] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handlePlatformSelect = (platform) => {
    setSelectedPlatform(platform);
  };

  const handleAnalysisTypeSelect = (type) => {
    setAnalysisType(type);
  };

  const handleAnalysisComplete = (analysis, songs) => {
    setMoodAnalysis(analysis);
    setSongRecommendations(songs);
  };

  const handleStartOver = () => {
    setSelectedPlatform(null);
    setAnalysisType(null);
    setMoodAnalysis(null);
    setSongRecommendations([]);
    setIsAnalyzing(false);
  };

  if (!selectedPlatform) {
    return (
      <div className="music-container">
        <div className="music-header">
          <h2>🎵 AI Music Therapy</h2>
          <p>Let AI analyze your mood and suggest therapeutic music</p>
        </div>
        <PlatformSelector onSelect={handlePlatformSelect} />
      </div>
    );
  }

  if (!analysisType) {
    return (
      
      <div className="music-container" style={{backgroundImage:`url(${singers})`}}>
        <div className="music-header">
          <h2>🎵 AI Music Therapy</h2>
          <p>Choose your preferred analysis method</p>
          <div className="platform-selected">
            Selected Platform: <strong>{selectedPlatform.toUpperCase()}</strong>
            <button onClick={handleStartOver} className="change-btn">Change</button>
          </div>
        </div>
        
        <div className="analysis-options">
          <div 
            className="analysis-option"
            onClick={() => handleAnalysisTypeSelect('face')}
          >
            <div className="analysis-icon">📸</div>
            <h3>Face Analysis</h3>
            <p>AI analyzes your facial expressions to detect emotional state</p>
          </div>
          
          <div 
            className="analysis-option"
            onClick={() => handleAnalysisTypeSelect('voice')}
          >
            <div className="analysis-icon">🎤</div>
            <h3>Voice Analysis</h3>
            <p>Speak for 10-15 seconds to analyze tone and emotion</p>
          </div>
          
          <div 
            className="analysis-option"
            onClick={() => handleAnalysisTypeSelect('text')}
          >
            <div className="analysis-icon">📝</div>
            <h3>Text Analysis</h3>
            <p>Describe how you're feeling in your own words</p>
          </div>
        </div>
      </div>
    );
  }

  if (songRecommendations.length > 0) {
    return (
      <div className="music-container">
        <MusicPlayer
          moodAnalysis={moodAnalysis}
          songs={songRecommendations}
          platform={selectedPlatform}
          onStartOver={handleStartOver}
        />
      </div>
    );
  }

  return (
    <div className="music-container">
      <div className="music-header">
        <h2>🎵 AI Music Therapy</h2>
        <div className="analysis-info">
          <span>Platform: <strong>{selectedPlatform.toUpperCase()}</strong></span>
          <span>Analysis: <strong>{analysisType.toUpperCase()}</strong></span>
          <button onClick={handleStartOver} className="change-btn">Start Over</button>
        </div>
      </div>

      <div className="analysis-container">
        {analysisType === 'face' && (
          <FaceAnalysis 
            platform={selectedPlatform}
            onComplete={handleAnalysisComplete}
            isAnalyzing={isAnalyzing}
            setIsAnalyzing={setIsAnalyzing}
          />
        )}
        {analysisType === 'voice' && (
          <VoiceAnalysis 
            platform={selectedPlatform}
            onComplete={handleAnalysisComplete}
            isAnalyzing={isAnalyzing}
            setIsAnalyzing={setIsAnalyzing}
          />
        )}
        {analysisType === 'text' && (
          <TextAnalysis 
            platform={selectedPlatform}
            onComplete={handleAnalysisComplete}
            isAnalyzing={isAnalyzing}
            setIsAnalyzing={setIsAnalyzing}
          />
        )}
      </div>
    </div>
  );
};

export default Music;
