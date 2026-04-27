import React, { useState, useEffect } from 'react';
import QuickActions from '../StudentDashboard/QuickActions';
import Music from './Music/Music'; // Import the new Music component
import './StudentDashboard.css';
import {useAuth} from '../../context/AuthContext';
// Import images
import music from '../../assets/images/music.jpg';
import aichatimage from '../../assets/images/aichatimage.jpg';
import alertimage from '../../assets/images/alertimage.jpg';
import groupimage from '../../assets/images/groupimage.jpg';
import wellness from '../../assets/images/wellness.jpg';

const StudentDashboard = () => {
  const {user}=useAuth();
  const [selectedMood, setSelectedMood] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [bookings, setBookings] = useState([]);
  const [selectedResource, setSelectedResource] = useState(null); // New state for resource selection
  const [activeSection, setActiveSection] = useState('dashboard'); // New state for navigation

  const moodEmojis = [
    { emoji: '😢', label: 'Very Sad', color: '#EF4444' },
    { emoji: '😟', label: 'Sad', color: '#F59E0B' },
    { emoji: '😐', label: 'Neutral', color: '#6B7280' },
    { emoji: '🙂', label: 'Happy', color: '#10B981' },
    { emoji: '😊', label: 'Very Happy', color: '#059669' }
  ];

  const quotes = [
    "Every day is a new beginning. Take a deep breath, smile and start again.",
    "You are stronger than you think and more loved than you know.",
    "Progress, not perfection, is what matters."
  ];

  const [todayQuote] = useState(quotes[Math.floor(Math.random() * quotes.length)]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleMoodSelect = (index) => setSelectedMood(index);

  const handleBookingCreate = (newBooking) => {
    setBookings(prev => [...prev, newBooking]);
    alert('Booking request submitted successfully!');
  };

  // New function to handle resource selection
  const handleResourceSelect = (resourceType) => {
    setSelectedResource(resourceType);
    setActiveSection('resources');
  };

  // New function to handle navigation
  const handleNavigation = (section) => {
    setActiveSection(section);
    if (section !== 'resources') {
      setSelectedResource(null);
    }
  };

  const formatTime = date =>
    date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  const formatDate = date =>
    date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  // Render different sections based on activeSection
  const renderMainContent = () => {
    if (activeSection === 'resources' && selectedResource === 'Music') {
      return <Music />;
    }

    if (activeSection === 'resources') {
      return (
        <div className="resources-section">
          <div className="resources-header">
            <h2>🎯 Personalized Resources</h2>
            <p>AI-powered recommendations tailored to your needs</p>
          </div>
          <div className="resources-grid">
            <div 
              className="resource-option music-option"
              onClick={() => setSelectedResource('Music')}
            >
              <div className="resource-icon">🎵</div>
              <h3>AI Music Therapy</h3>
              <p>Get personalized music recommendations based on your mood through face, voice, or text analysis</p>
              <div className="resource-features">
                <span>📸 Face Analysis</span>
                <span>🎤 Voice Analysis</span>
                <span>📝 Text Analysis</span>
              </div>
              <button className="resource-btn">Start Music Therapy</button>
            </div>
            
            <div className="resource-option meditation-option">
              <div className="resource-icon">🧘‍♀️</div>
              <h3>Guided Meditation</h3>
              <p>Personalized meditation sessions based on your stress patterns</p>
              <div className="resource-features">
                <span>🌱 Beginner Friendly</span>
                <span>⏰ 5-30 min Sessions</span>
                <span>🎯 Targeted Relief</span>
              </div>
              <button className="resource-btn">Coming Soon</button>
            </div>

            <div className="resource-option articles-option">
              <div className="resource-icon">📚</div>
              <h3>Self-Help Articles</h3>
              <p>Curated articles and resources for mental wellness</p>
              <div className="resource-features">
                <span>📖 Expert Written</span>
                <span>🎯 Personalized</span>
                <span>📱 Mobile Friendly</span>
              </div>
              <button className="resource-btn">Coming Soon</button>
            </div>

            <div className="resource-option exercises-option">
              <div className="resource-icon">💪</div>
              <h3>Wellness Exercises</h3>
              <p>Physical and mental exercises for better wellbeing</p>
              <div className="resource-features">
                <span>🏃‍♀️ Physical</span>
                <span>🧠 Mental</span>
                <span>📊 Track Progress</span>
              </div>
              <button className="resource-btn">Coming Soon</button>
            </div>
          </div>
        </div>
      );
    }

    // Default dashboard content
    return (
      <>
        {/* Header */}
        <header className="dashboard-header">
          <div className="welcome-section">
            <h1>{user?.name || 'Counselor'}</h1>
            <p>
              {user?.designation || user?.role === 'counselor'
              ? 'Licensed Professional Counselor'
              : user?.role || ''}
            </p>
            <p>Let's take care of your mental wellness today</p>
          </div>
          <div className="header-stats">
            <div className="time-widget">
              <div className="time">{formatTime(currentTime)}</div>
              <div className="date">{formatDate(currentTime)}</div>
            </div>
            <div className="weather-widget">
              <span>☀️</span>
              <div>
                <div>24°C</div>
                <div>Sunny</div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="dashboard-grid">
          {/* Row 1 */}
          <div className="card wellness-card">
            <div className="card-header">
              <h3>Wellness Sessions</h3>
              <span className="badge">Daily</span>
            </div>
            <div className="wellness-content">
              <div className="wellness-image">
                <img src={wellness} alt="Wellness" />
                <div className="overlay">
                  <h4>Mental Health Assessment</h4>
                  <p>PHQ-9 & GAD-7 Available</p>
                </div>
              </div>
              <div className="wellness-actions">
                <button className="btn-primary">Start PHQ-9</button>
                <button className="btn-secondary">Take GAD-7</button>
              </div>
              <div className="wellness-stats">
                <div><span>7</span>Days Streak</div>
                <div><span>85%</span>Complete</div>
              </div>
            </div>
          </div>

          <div className="card mood-card">
            <div className="card-header">
              <h3>Mood Tracker</h3>
              <span className="streak">🔥 7 days</span>
            </div>
            <div className="mood-content">
              <p>How are you feeling?</p>
              <div className="mood-selector">
                {moodEmojis.map((mood, index) => (
                  <button
                    type="button"
                    key={index}
                    className={`mood-btn ${selectedMood === index ? 'selected' : ''}`}
                    onClick={() => handleMoodSelect(index)}
                    style={{ '--color': mood.color }}
                  >
                    {mood.emoji}
                  </button>
                ))}
              </div>
              {selectedMood !== null && (
                <div className="mood-result">
                  <p>You feel: <strong>{moodEmojis[selectedMood].label}</strong></p>
                  <button className="save-btn">Save Mood</button>
                </div>
              )}
            </div>
          </div>

          <div className="card peers-card">
            <div className="card-header">
              <h3>Talk with Peers</h3>
              <span className="online">🟢 24 online</span>
            </div>
            <div className="peers-content">
              <div className="peers-preview">
                <img src={groupimage} alt="Peers" />
                <div className="message">
                  <p>"Feeling better after our talk! 💚"</p>
                  <span>- Sarah M.</span>
                </div>
              </div>
              <div className="peers-actions">
                <button className="btn-chat">💬 Join Chat</button>
                <button className="btn-buddy">👥 Find Buddy</button>
              </div>
            </div>
          </div>

          {/* Row 2: Quick Actions */}
          <div className="card actions-card">
            <div className="card-header">
              <h3>Quick Actions</h3>
              <img src={alertimage} alt="Alert" className="alert-icon" />
            </div>
            <QuickActions onBookingCreate={handleBookingCreate} />
          </div>

          <div className="card ai-card">
            <div className="card-header">
              <h3>AI Listener</h3>
              <span className="status">🟢 24/7</span>
            </div>
            <div className="ai-content">
              <div className="ai-preview">
                <img src={aichatimage} alt="AI" />
                <div className="ai-avatar">
                  <div className="robot">🤖</div>
                  <div className="pulse"></div>
                </div>
              </div>
              <div className="ai-levels">
                <div className="level active">Easy</div>
                <div className="level">Medium</div>
                <div className="level">Hard</div>
              </div>
              <div className="ai-actions">
                <button className="ai-voice">🎤 Voice</button>
                <button className="ai-video">📹 Video</button>
              </div>
            </div>
          </div>

          <div className="card quote-card">
            <div className="card-header">
              <h3>Today's Inspiration</h3>
              <span>✨</span>
            </div>
            <div className="quote-content">
              <blockquote>{todayQuote}</blockquote>
              <div className="quote-actions">
                <button>📤 Share</button>
                <button>❤️ Save</button>
              </div>
            </div>
          </div>

          {/* Updated Resource Card with Click Handler */}
          <div className="card resource-card" onClick={() => handleResourceSelect('Music')}>
            <div className="card-header">
              <h3>AI-Powered Resources</h3>
              <span className="badge personalized">Personalized</span>
            </div>
            <div className="resource-content">
              <div className="resource-preview">
                <img src={music} alt="Resources" />
                <div className="analysis">
                  <p>Click to start AI Music Therapy</p>
                  <div className="music-features">
                    <span>📸 Face</span>
                    <span>🎤 Voice</span>
                    <span>📝 Text</span>
                  </div>
                </div>
              </div>
              <div className="resource-categories">
                <div className="category active">
                  <span>🎵</span>
                  <div>
                    <h4>Music Therapy</h4>
                    <p>AI-powered mood analysis</p>
                  </div>
                </div>
                <div className="category">
                  <span>🧘‍♀️</span>
                  <div>
                    <h4>Meditation</h4>
                    <p>Coming soon</p>
                  </div>
                </div>
              </div>
              <div className="suggestions">
                <div className="suggestion">
                  <span>🎼</span>
                  <span>Start Music Analysis</span>
                  <button>▶️</button>
                </div>
                <div className="suggestion">
                  <span>🎵</span>
                  <span>Mood-based Recommendations</span>
                  <button>🎯</button>
                </div>
              </div>
            </div>
          </div>

          {/* Booking list if any */}
          {bookings.length > 0 && (
            <div className="card bookings-card">
              <div className="card-header">
                <h3>Your Bookings</h3>
                <span className="badge">{bookings.length}</span>
              </div>
              <div className="bookings-list">
                {bookings.map(booking => (
                  <div key={booking._id || booking.appointmentDate} className="booking-item">
                    <div className="booking-info">
                      <h4>{booking.sessionType} Session</h4>
                      <p>with {booking.therapistId?.name || 'Therapist'}</p>
                      <span className="booking-date">
                        {new Date(booking.appointmentDate).toLocaleDateString()}
                      </span>
                    </div>
                    <div className={`booking-status ${booking.status}`}>
                      {booking.status === 'scheduled' ? 'Pending' : booking.status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </>
    );
  };

  return (
    <div className="student-dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-icon">🧠</div>
            <div className="brand-text">MindCare</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          <a 
            href="#" 
            className={`nav-item ${activeSection === 'dashboard' ? 'active' : ''}`}
            onClick={() => handleNavigation('dashboard')}
          >
            <span className="nav-icon">📊</span>
            <span>Dashboard</span>
          </a>
          <a href="#" className="nav-item">
            <span className="nav-icon">💚</span>
            <span>Wellness</span>
          </a>
          <a href="#" className="nav-item">
            <span className="nav-icon">💬</span>
            <span>Messages</span>
          </a>
          <a 
            href="#" 
            className={`nav-item ${activeSection === 'resources' ? 'active' : ''}`}
            onClick={() => handleNavigation('resources')}
          >
            <span className="nav-icon">📚</span>
            <span>Resources</span>
          </a>
        </nav>
        <div className="sidebar-footer">
          <div className="mindful-note">
            <span>🪷</span>
            <p>Stay mindful</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {renderMainContent()}
      </main>
    </div>
  );
};

export default StudentDashboard;
