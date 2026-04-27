import React, { useState } from 'react';
import MusicPlatformService from '../../../services/musicPlatformService';

const MusicPlayer = ({ moodAnalysis, songs, platform, onStartOver }) => {
  const [selectedSong, setSelectedSong] = useState(null);

  const playOnPlatform = (song) => {
    MusicPlatformService.openInPlatform(song, platform);
    setSelectedSong(song);
  };

  const getMoodEmoji = (mood) => {
    const moodEmojis = {
      happy: '😊',
      sad: '😢',
      anxious: '😰',
      angry: '😠',
      neutral: '😐',
      stressed: '😫',
      excited: '🤩',
      calm: '😌'
    };
    return moodEmojis[mood] || '🎵';
  };

  const getIntensityColor = (intensity) => {
    const colors = {
      low: '#4CAF50',
      medium: '#FF9800',
      high: '#F44336'
    };
    return colors[intensity] || '#2196F3';
  };

  return (
    <div className="music-player">
      <div className="analysis-results">
        <div className="mood-summary">
          <h3>🧠 Your Mood Analysis</h3>
          <div className="mood-card">
            <div className="mood-emoji">{getMoodEmoji(moodAnalysis.mood)}</div>
            <div className="mood-details">
              <h4>{moodAnalysis.mood.charAt(0).toUpperCase() + moodAnalysis.mood.slice(1)}</h4>
              <p className="mood-description">{moodAnalysis.description}</p>
              <div className="mood-meta">
                <span 
                  className="intensity-badge"
                  style={{ backgroundColor: getIntensityColor(moodAnalysis.intensity) }}
                >
                  {moodAnalysis.intensity} intensity
                </span>
                <span className="genres">
                  Genres: {moodAnalysis.musicGenres.join(', ')}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="recommended-songs">
          <h3>🎵 Recommended for You</h3>
          <p>AI-curated songs to match and improve your mood</p>
          
          <div className="songs-grid">
            {songs.map((song, index) => (
              <div key={index} className="song-card">
                <div className="song-info">
                  <h4 className="song-title">{song.title}</h4>
                  <p className="song-artist">{song.artist}</p>
                  <p className="song-reason">{song.reason}</p>
                </div>
                <div className="song-actions">
                  <button 
                    onClick={() => playOnPlatform(song)}
                    className="play-btn"
                  >
                    ▶️ Play on {platform.charAt(0).toUpperCase() + platform.slice(1)}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="session-actions">
          <button onClick={onStartOver} className="new-analysis-btn">
            🔄 New Analysis
          </button>
          <button 
            onClick={() => window.location.reload()} 
            className="save-session-btn"
          >
            💾 Save Session
          </button>
        </div>
      </div>
    </div>
  );
};

export default MusicPlayer;
