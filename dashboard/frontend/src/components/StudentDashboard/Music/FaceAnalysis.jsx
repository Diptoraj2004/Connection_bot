import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import GeminiService from '../../../services/geminiService';

const FaceAnalysis = ({ platform, onComplete, isAnalyzing, setIsAnalyzing }) => {
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
  }, [webcamRef]);

  const analyzeFace = async () => {
    if (!capturedImage) return;
    
    setIsAnalyzing(true);
    try {
      // Convert base64 to blob for Gemini
      const response = await fetch(capturedImage);
      const blob = await response.blob();
      
      const moodAnalysis = await GeminiService.analyzeFaceEmotion(blob);
      const songs = await GeminiService.getSongRecommendations(moodAnalysis, platform);
      
      onComplete(moodAnalysis, songs);
    } catch (error) {
      console.error('Face analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const retake = () => {
    setCapturedImage(null);
  };

  return (
    <div className="face-analysis">
      <div className="webcam-container">
        {!capturedImage ? (
          <>
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              className="webcam"
            />
            <div className="capture-instructions">
              <p>📸 Look at the camera and capture your current expression</p>
              <button onClick={capture} className="capture-btn">
                Capture Photo
              </button>
            </div>
          </>
        ) : (
          <div className="captured-image-container">
            <img src={capturedImage} alt="Captured" className="captured-image" />
            <div className="image-actions">
              <button onClick={retake} className="retake-btn">
                📸 Retake
              </button>
              <button 
                onClick={analyzeFace} 
                className="analyze-btn"
                disabled={isAnalyzing}
              >
                {isAnalyzing ? '🔄 Analyzing...' : '🧠 Analyze Mood'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FaceAnalysis;
