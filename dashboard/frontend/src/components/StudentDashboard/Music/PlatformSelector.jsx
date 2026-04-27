import React from 'react';

const PlatformSelector = ({ onSelect }) => {
  return (
    <div className="platform-selector">
      <h3>Choose Your Music Platform</h3>
      <div className="platform-options">
        <div 
          className="platform-option spotify"
          onClick={() => onSelect('spotify')}
        >
          <div className="platform-icon">🎵</div>
          <h4>Spotify</h4>
          <p>Listen on Spotify Premium</p>
        </div>
        
        <div 
          className="platform-option youtube"
          onClick={() => onSelect('youtube')}
        >
          <div className="platform-icon">📺</div>
          <h4>YouTube</h4>
          <p>Free music videos and audio</p>
        </div>
      </div>
    </div>
  );
};

export default PlatformSelector;
