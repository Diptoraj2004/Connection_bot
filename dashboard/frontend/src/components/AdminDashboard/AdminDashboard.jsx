import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AdminDashboard.css';

// Import images
import campusHeatmapImg from '../../assets/images/heatmap.jpg'; // 10.jpg
import counselorSchedulingImg from '../../assets/images/counselorscheduling.jpg'; // 1000001510.jpg
import seasonalPatternsImg from '../../assets/images/seasonalpatterns.jpg'; // 1000001508.jpg
import predictiveAnalysisImg from '../../assets/images/predictiveanalysis.jpg'; // 1000001505.jpg
import resourcesImg from '../../assets/images/resources.jpg'; // 1000001439.jpg

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [selectedTimeframe, setSelectedTimeframe] = useState('current');

  // Sample data
  const campusHeatmapData = [
    { dept: 'Engineering', students: 245, level: 'low', color: 'green' },
    { dept: 'Sciences', students: 189, level: 'moderate', color: 'yellow' },
    { dept: 'Business', students: 167, level: 'high', color: 'orange' },
    { dept: 'Arts', students: 134, level: 'critical', color: 'red' },
    { dept: 'Medicine', students: 98, level: 'low', color: 'green' },
    { dept: 'Law', students: 76, level: 'moderate', color: 'yellow' }
  ];

  const priorityStudents = [
    { id: 'ST001', name: 'Lisa Nanda Goswami', score: 24, risk: 'critical', dept: 'Engineering' },
    { id: 'ST002', name: 'Bhumika Das', score: 21, risk: 'high', dept: 'Business' },
    { id: 'ST003', name: 'Anwesha Banerjee', score: 19, risk: 'high', dept: 'Sciences' },
    { id: 'ST004', name: 'Thirtharaj Banerjee', score: 18, risk: 'moderate', dept: 'Arts' },
    { id: 'ST005', name: 'Snehasish Dutta', score: 17, risk: 'moderate', dept: 'Medicine' }
  ];

  const counselorScheduling = [
    { counselor: 'Dr. Sarah Brown', availability: 85, sessions: 12, pending: 3 },
    { counselor: 'Dr. Therapist', availability: 70, sessions: 8, pending: 5 },
    { counselor: 'Dr. Lisa ', availability: 60, sessions: 15, pending: 2 },
    { counselor: 'Dr. Tirtha', availability: 45, sessions: 10, pending: 7 }
  ];

  const handleHeatmapClick = () => {
    navigate('/admin/heatmap');
  };

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="title-section">
            <h1>Administrative Mental Health Dashboard</h1>
            <p>Real-time monitoring and management system</p>
          </div>
          <div className="header-actions">
            <button className="export-btn">📊 Export Report</button>
            <button className="settings-btn">⚙️ Settings</button>
          </div>
        </div>
      </header>

      {/* Dashboard Grid */}
      <main className="dashboard-grid">

        {/* 1. Active Students */}
        <div className="card active-students-card">
          <div className="card-header">
            <h3>Active Students</h3>
            <span className="update-indicator">🟢 Live</span>
          </div>
          <div className="active-students-content">
            <div className="main-metric">
              <div className="metric-number">2,847</div>
              <div className="metric-change">+127 today</div>
            </div>
            <div className="breakdown">
              <div className="breakdown-item">
                <span className="dot online"></span>
                <span>Online Now: 1,234</span>
              </div>
              <div className="breakdown-item">
                <span className="dot recent"></span>
                <span>Active Today: 2,847</span>
              </div>
              <div className="breakdown-item">
                <span className="dot week"></span>
                <span>This Week: 4,156</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Priority List */}
        <div className="card priority-list-card">
          <div className="card-header">
            <h3>Priority Students</h3>
            <span className="ai-badge">🤖 AI Suggested</span>
          </div>
          <div className="priority-content">
            <div className="priority-stats">
              <div className="stat-item critical">
                <span className="count">3</span>
                <span className="label">Critical</span>
              </div>
              <div className="stat-item high">
                <span className="count">12</span>
                <span className="label">High Risk</span>
              </div>
              <div className="stat-item moderate">
                <span className="count">28</span>
                <span className="label">Moderate</span>
              </div>
            </div>
            <div className="priority-list">
              {priorityStudents.slice(0, 3).map((student, index) => (
                <div key={student.id} className={`priority-item ${student.risk}`}>
                  <div className="student-info">
                    <span className="student-name">{student.name}</span>
                    <span className="student-dept">{student.dept}</span>
                  </div>
                  <div className="risk-score">
                    <span className="score">{student.score}</span>
                    <span className="risk-label">{student.risk}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 3. Campus Heatmap (CLICKABLE) */}
        <div 
          className="card campus-heatmap-card clickable"
          onClick={handleHeatmapClick}
          tabIndex={0}
          style={{ cursor: 'pointer', position: 'relative' }}
        >
          <div className="card-header">
            <h3>Campus Mental Health Heatmap</h3>
            <div className="heatmap-actions">
              <select
                className="timeframe-select"
                onClick={e => e.stopPropagation()}
                value={selectedTimeframe}
                onChange={e => setSelectedTimeframe(e.target.value)}
              >
                <option value="current">This Week</option>
                <option value="month">This Month</option>
                <option value="semester">This Semester</option>
              </select>
              <span className="view-indicator" style={{ color: '#3B82F6' }}>
                👁️ Click to view heatmap details
              </span>
            </div>
          </div>
          <div className="heatmap-content">
            <div className="heatmap-visual">
              <img src={campusHeatmapImg} alt="Campus Heatmap" className="heatmap-bg" />
              <div className="heatmap-overlay">
                <div className="heatmap-legend">
                  <div className="legend-item"><span className="legend-color green"></span><span>Low Risk</span></div>
                  <div className="legend-item"><span className="legend-color yellow"></span><span>Moderate</span></div>
                  <div className="legend-item"><span className="legend-color orange"></span><span>High Risk</span></div>
                  <div className="legend-item"><span className="legend-color red"></span><span>Critical</span></div>
                </div>
              </div>
            </div>
            <div className="heatmap-grid">
              {campusHeatmapData.map((dept, index) => (
                <div key={index} className={`heatmap-department ${dept.color}`}>
                  <div className="dept-name">{dept.dept}</div>
                  <div className="dept-count">{dept.students}</div>
                  <div className="dept-level">{dept.level}</div>
                </div>
              ))}
            </div>
            <div className="heatmap-click-hint" style={{
              position: 'absolute',
              top: '16px',
              right: '20px',
              background: 'rgba(59,130,246,0.07)',
              borderRadius: '18px',
              padding: '0.3rem 1rem',
              color: '#3B82F6',
              fontWeight: '600',
              fontSize: '0.92rem',
              pointerEvents: 'none'
            }}>
              <span role="img" aria-label="Click">👆</span> Click for analytics
            </div>
          </div>
        </div>

        {/* 4. Counselor Scheduling */}
        <div className="card counselor-scheduling-card">
          <div className="card-header">
            <h3>Counselor Scheduling</h3>
            <button className="add-session-btn">+ New Session</button>
          </div>
          <div className="scheduling-content">
            <div className="scheduling-visual">
              <img src={counselorSchedulingImg} alt="Counselor Scheduling" className="scheduling-bg" />
              <div className="scheduling-overlay">
                <div className="overview-item">
                  <span className="number">47</span>
                  <span className="label">Pending Bookings</span>
                </div>
                <div className="overview-item">
                  <span className="number">23</span>
                  <span className="label">Today's Sessions</span>
                </div>
              </div>
            </div>
            <div className="counselor-list">
              {counselorScheduling.map((counselor, index) => (
                <div key={index} className="counselor-item">
                  <div className="counselor-info">
                    <span className="counselor-name">{counselor.counselor}</span>
                    <div className="availability-bar">
                      <div className="availability-fill" 
                           style={{ width: `${counselor.availability}% `}}></div>
                    </div>
                  </div>
                  <div className="counselor-stats">
                    <span className="sessions">{counselor.sessions} sessions</span>
                    <span className="pending">{counselor.pending} pending</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

         {/* 5. Seasonal Patterns */}
        <div className="card seasonal-patterns-card">
          <div className="card-header">
            <h3>Seasonal Mental Health Patterns</h3>
            <div className="pattern-controls">
              <button className="active">2024</button>
              <button>2023</button>
              <button>Compare</button>
            </div>
          </div>
          <div className="patterns-content">
            <div className="patterns-visual">
              <img src={seasonalPatternsImg} alt="Seasonal Patterns" className="patterns-bg" />
              <div className="patterns-overlay">
                <div className="seasonal-chart">
                  <svg width="100%" height="120" viewBox="0 0 400 120">
                    <defs>
                      <linearGradient id="seasonalGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
                        <stop offset="100%" stopColor="rgba(59, 130, 246, 0.05)" />
                      </linearGradient>
                    </defs>
                    
                    <polyline
                      points="20,80 120,40 220,90 320,30 380,50"
                      fill="none"
                      stroke="#3B82F6"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                    
                    <polyline
                      points="20,80 120,40 220,90 320,30 380,50 380,100 20,100"
                      fill="url(#seasonalGradient)"
                      stroke="none"
                    />
                    
                    <circle cx="20" cy="80" r="4" fill="#3B82F6" />
                    <circle cx="120" cy="40" r="4" fill="#3B82F6" />
                    <circle cx="220" cy="90" r="4" fill="#3B82F6" />
                    <circle cx="320" cy="30" r="4" fill="#3B82F6" />
                    <circle cx="380" cy="50" r="4" fill="#3B82F6" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="seasonal-labels">
              <span>Winter</span>
              <span>Spring</span>
              <span>Summer</span>
              <span>Fall</span>
            </div>
            <div className="seasonal-insights">
              <div className="insight-item">
                <span className="insight-icon">📈</span>
                <span>Peak stress during Finals (Winter)</span>
              </div>
              <div className="insight-item">
                <span className="insight-icon">🌸</span>
                <span>Improved mood in Spring</span>
              </div>
            </div>
          </div>
        </div>

        {/* 6. Predictive Analysis */}
        <div className="card predictive-analysis-card">
          <div className="card-header">
            <h3>Predictive Analysis</h3>
            <span className="prediction-badge">🔮 AI Forecast</span>
          </div>
          <div className="prediction-content">
            <div className="prediction-visual">
              <img src={predictiveAnalysisImg} alt="Predictive Analysis" className="prediction-bg" />
              <div className="prediction-overlay">
                <div className="prediction-chart">
                  <svg width="100%" height="100" viewBox="0 0 400 100">
                    <polyline
                      points="20,70 80,50 140,75 200,45"
                      fill="none"
                      stroke="#10B981"
                      strokeWidth="2"
                    />
                    
                    <polyline
                      points="200,45 260,35 320,60 380,40"
                      fill="none"
                      stroke="#F59E0B"
                      strokeWidth="2"
                      strokeDasharray="5,5"
                    />
                    
                    <polyline
                      points="200,35 260,25 320,45 380,30 380,55 320,75 260,50 200,60"
                      fill="rgba(245, 158, 11, 0.1)"
                      stroke="none"
                    />
                  </svg>
                </div>
              </div>
            </div>
            <div className="prediction-insights">
              <div className="prediction-item">
                <span className="prediction-label">Next Month</span>
                <span className="prediction-trend up">↗ 15% increase expected</span>
              </div>
              <div className="prediction-item">
                <span className="prediction-label">Risk Factors</span>
                <span className="prediction-factor">Exam period, Weather change</span>
              </div>
              <div className="prediction-item">
                <span className="prediction-label">Confidence</span>
                <span className="prediction-confidence">87%</span>
              </div>
            </div>
          </div>
        </div>

        {/* 7. Resources */}
        <div className="card resources-card">
          <div className="card-header">
            <h3>Resource Management</h3>
            <button className="manage-btn">Manage</button>
          </div>
          <div className="resources-content">
            <div className="resources-visual">
              <img src={resourcesImg} alt="Resources" className="resources-bg" />
              <div className="resources-overlay">
                <div className="resource-metric">
                  <div className="metric-icon">👨‍⚕️</div>
                  <div className="metric-details">
                    <span className="metric-number">12</span>
                    <span className="metric-label">Active Counselors</span>
                  </div>
                </div>
                <div className="resource-metric">
                  <div className="metric-icon">💰</div>
                  <div className="metric-details">
                    <span className="metric-number">$24,500</span>
                    <span className="metric-label">Monthly Budget</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="resource-requirements">
              <div className="requirement-item">
                <span className="requirement-label">Additional Counselors Needed</span>
                <div className="requirement-value">
                  <span className="number">3</span>
                  <span className="urgency high">High Priority</span>
                </div>
              </div>
              
              <div className="payment-integration">
                <div className="payment-status">
                  <span className="status-icon">✅</span>
                  <span>Payment Integration: Active</span>
                </div>
                <div className="payment-methods">
                  <span className="method">💳 Credit/Debit</span>
                  <span className="method">🏦 Bank Transfer</span>
                  <span className="method">📱 Digital Wallet</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
};

export default AdminDashboard;
