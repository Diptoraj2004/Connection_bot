import React, { useState } from 'react';
import { ReactMic } from 'react-mic';
import GeminiService from '../../../services/geminiService';

const VoiceAnalysis = ({ platform, onComplete, isAnalyzing, setIsAnalyzing }) => {
  const [audioBlob, setAudioBlob] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const handleAudioStop = (recordedData) => {
    setAudioBlob(recordedData.blob);
    setIsRecording(false);

    // (Optional) Transcribe with external service, else placeholder:
    setTranscript('Audio recorded - analyzing tone and emotional content...');
  };

  const analyzeVoice = async () => {
    if (!audioBlob) return;
    setIsAnalyzing(true);
    try {
      const moodAnalysis = await GeminiService.analyzeVoiceEmotion(transcript, {
        hasAudio: true,
        duration: audioBlob.size
      });
      const songs = await GeminiService.getSongRecommendations(moodAnalysis, platform);
      onComplete(moodAnalysis, songs);
    } catch (error) {
      console.error('Voice analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const startNewRecording = () => {
    setAudioBlob(null);
    setTranscript('');
    setIsRecording(false);
  };

  return (
    <div className="voice-analysis">
      <div className="recording-container">
        <div className="recording-instructions">
          <h3>🎤 Voice Emotion Analysis</h3>
          <p>Speak for 10-15 seconds about how you're feeling</p>
        </div>

        {!audioBlob ? (
          <div className="recorder-container">
            <button
              onClick={() => setIsRecording(prev => !prev)}
              className="record-toggle-btn"
              style={{ marginBottom: 16 }}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            <ReactMic
              record={isRecording}
              className="audio-wave"
              onStop={handleAudioStop}
              strokeColor="#ff4444"
              backgroundColor="#fff"
              mimeType="audio/webm"
            />
            {isRecording && (
              <div className="recording-indicator">
                <div className="pulse-ring"></div>
                <div className="pulse-dot"></div>
                <p>Recording... Speak naturally about your feelings</p>
              </div>
            )}
          </div>
        ) : (
          <div className="recorded-audio-container">
            <div className="audio-preview">
              <p>✅ Audio recorded successfully</p>
              <p>Transcript: {transcript}</p>
              <audio controls src={URL.createObjectURL(audioBlob)} />
            </div>
            <div className="audio-actions">
              <button onClick={startNewRecording} className="record-again-btn">
                🎤 Record Again
              </button>
              <button
                onClick={analyzeVoice}
                className="analyze-btn"
                disabled={isAnalyzing}
              >
                {isAnalyzing ? '🔄 Analyzing...' : '🧠 Analyze Voice'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceAnalysis;