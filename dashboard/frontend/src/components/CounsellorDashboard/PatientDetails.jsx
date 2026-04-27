import React, { useState } from 'react';
import './PatientDetails.css';

// Import images
import wellnessReportsImg from '../../assets/images/wellnessreports.jpg';
import therapyEffectivenessImg from '../../assets/images/predictiveanalysis.jpg';

const PatientDetails = ({ patient, onBack }) => {
  const [activeTab, setActiveTab] = useState('treatment-history');

  const treatmentHistory = [
    {
      date: '2024-09-08',
      type: 'Individual Therapy',
      duration: '50 min',
      therapist: 'Dr. Emma Smith',
      notes: 'Patient showed improvement in anxiety management. CBT techniques discussed.',
      outcome: 'Positive'
    },
    {
      date: '2024-09-01',
      type: 'Assessment Session',
      duration: '90 min',
      therapist: 'Dr. Emma Smith',
      notes: 'Initial assessment completed. PHQ-9: 18, GAD-7: 15. High anxiety and moderate depression identified.',
      outcome: 'Assessment'
    },
    {
      date: '2024-08-25',
      type: 'Intake Session',
      duration: '60 min',
      therapist: 'Dr. Emma Smith',
      notes: 'First session. Patient expressed concerns about academic stress and social anxiety.',
      outcome: 'Initial'
    }
  ];

  const wellnessReports = [
    {
      date: '2024-09-10',
      moodScore: 6.5,
      stressLevel: 'Moderate',
      sleepQuality: 'Good',
      activities: ['Meditation', 'Exercise'],
      aiRecommendations: 'Continue mindfulness practices. Consider increasing physical activity.'
    },
    {
      date: '2024-09-09',
      moodScore: 5.8,
      stressLevel: 'High',
      sleepQuality: 'Poor',
      activities: ['Journaling'],
      aiRecommendations: 'Focus on sleep hygiene. Schedule relaxation time before bed.'
    },
    {
      date: '2024-09-08',
      moodScore: 7.2,
      stressLevel: 'Low',
      sleepQuality: 'Excellent',
      activities: ['Meditation', 'Social time', 'Exercise'],
      aiRecommendations: 'Excellent progress. Maintain current routine.'
    }
  ];

  const scoreHistory = [
    { date: '2024-09-10', phq9: 16, gad7: 13, severity: 'Moderate', trend: 'improving' },
    { date: '2024-09-03', phq9: 18, gad7: 15, severity: 'Moderate-High', trend: 'stable' },
    { date: '2024-08-27', phq9: 20, gad7: 17, severity: 'High', trend: 'declining' },
    { date: '2024-08-20', phq9: 18, gad7: 16, severity: 'Moderate-High', trend: 'stable' }
  ];

  return (
    <div className="patient-details">
      {/* Header */}
      <header className="patient-header">
        <div className="patient-header-content">
          <div className="patient-info">
            <button className="back-btn" onClick={onBack}>
              ← Back to Dashboard
            </button>
            <div className="patient-main-info">
              <h1>{patient.name}</h1>
              <div className="patient-meta">
                <span className="patient-id">ID: {patient.id}</span>
                <span className={`current-risk ${patient.risk}`}>
                  Risk Level: {patient.risk.toUpperCase()}
                </span>
                <span className="last-session">Last Session: {patient.lastSession}</span>
              </div>
            </div>
          </div>
          <div className="patient-stats">
            <div className="stat-card">
              <span className="stat-label">Current PHQ-9</span>
              <span className="stat-value phq9">{patient.phq9}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Current GAD-7</span>
              <span className="stat-value gad7">{patient.gad7}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Sessions</span>
              <span className="stat-value sessions">12</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="patient-nav">
        <button 
          className={`nav-tab ${activeTab === 'treatment-history' ? 'active' : ''}`}
          onClick={() => setActiveTab('treatment-history')}
        >
          📋 Treatment History
        </button>
        <button 
          className={`nav-tab ${activeTab === 'wellness-reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('wellness-reports')}
        >
          📊 Wellness Reports
        </button>
        <button 
          className={`nav-tab ${activeTab === 'therapy-effectiveness' ? 'active' : ''}`}
          onClick={() => setActiveTab('therapy-effectiveness')}
        >
          📈 Therapy Effectiveness
        </button>
        <button 
          className={`nav-tab ${activeTab === 'scores' ? 'active' : ''}`}
          onClick={() => setActiveTab('scores')}
        >
          🎯 Scores
        </button>
      </nav>

      {/* Content Sections */}
      <main className="patient-content">
        {activeTab === 'treatment-history' && (
          <section className="treatment-history">
            <h2>Treatment History</h2>
            <div className="history-timeline">
              {treatmentHistory.map((session, index) => (
                <div key={index} className="timeline-item">
                  <div className="timeline-date">
                    <span className="date">{new Date(session.date).toLocaleDateString()}</span>
                    <span className="duration">{session.duration}</span>
                  </div>
                  <div className="timeline-content">
                    <div className="session-header">
                      <h3>{session.type}</h3>
                      <span className={`outcome-badge ${session.outcome.toLowerCase()}`}>
                        {session.outcome}
                      </span>
                    </div>
                    <p className="session-therapist">Therapist: {session.therapist}</p>
                    <p className="session-notes">{session.notes}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'wellness-reports' && (
          <section className="wellness-reports">
            <div className="section-header">
              <h2>Daily Wellness Reports</h2>
              <p>AI-powered wellness tracking from student dashboard sessions</p>
            </div>
            
            <div className="wellness-visual">
              <img src={wellnessReportsImg} alt="Wellness Reports" className="wellness-bg" />
              <div className="wellness-overlay">
                <div className="wellness-summary">
                  <div className="summary-metric">
                    <span className="metric-value">7.2</span>
                    <span className="metric-label">Avg Mood</span>
                  </div>
                  <div className="summary-metric">
                    <span className="metric-value">68%</span>
                    <span className="metric-label">Improvement</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="wellness-grid">
              {wellnessReports.map((report, index) => (
                <div key={index} className="wellness-card">
                  <div className="wellness-card-header">
                    <span className="report-date">{new Date(report.date).toLocaleDateString()}</span>
                    <span className={`mood-indicator mood-${Math.floor(report.moodScore)}`}>
                      {report.moodScore}/10
                    </span>
                  </div>
                  <div className="wellness-metrics">
                    <div className="metric-item">
                      <span className="metric-label">Stress Level:</span>
                      <span className={`metric-value stress-${report.stressLevel.toLowerCase()}`}>
                        {report.stressLevel}
                      </span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">Sleep Quality:</span>
                      <span className={`metric-value sleep-${report.sleepQuality.toLowerCase()}`}>
                        {report.sleepQuality}
                      </span>
                    </div>
                  </div>
                  <div className="activities-section">
                    <span className="activities-label">Activities:</span>
                    <div className="activities-list">
                      {report.activities.map((activity, idx) => (
                        <span key={idx} className="activity-tag">{activity}</span>
                      ))}
                    </div>
                  </div>
                  <div className="ai-recommendations">
                    <span className="ai-label">🤖 AI Recommendations:</span>
                    <p className="ai-text">{report.aiRecommendations}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'therapy-effectiveness' && (
          <section className="therapy-effectiveness">
            <div className="section-header">
              <h2>Therapy Effectiveness</h2>
              <p>Progress tracking and treatment outcome analysis</p>
            </div>

            <div className="effectiveness-visual">
              <img src={therapyEffectivenessImg} alt="Therapy Effectiveness" className="effectiveness-bg" />
              <div className="effectiveness-overlay">
                <div className="progress-chart">
                  <svg width="100%" height="200" viewBox="0 0 500 200">
                    {/* Background grid */}
                    <defs>
                      <pattern id="grid" width="50" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 50 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1"/>
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" />
                    
                    {/* Progress lines */}
                    <polyline
                      points="50,160 150,140 250,120 350,90 450,70"
                      fill="none"
                      stroke="#10B981"
                      strokeWidth="3"
                      strokeDasharray="5,5"
                    />
                    <polyline
                      points="50,150 150,130 250,115 350,85 450,65"
                      fill="none"
                      stroke="#3B82F6"
                      strokeWidth="3"
                    />
                    
                    {/* Data points */}
                    <circle cx="50" cy="150" r="4" fill="#3B82F6" />
                    <circle cx="150" cy="130" r="4" fill="#3B82F6" />
                    <circle cx="250" cy="115" r="4" fill="#3B82F6" />
                    <circle cx="350" cy="85" r="4" fill="#3B82F6" />
                    <circle cx="450" cy="65" r="4" fill="#3B82F6" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="effectiveness-metrics">
              <div className="metric-section">
                <h3>Progress Overview</h3>
                <div className="progress-stats">
                  <div className="progress-item">
                    <span className="progress-label">Overall Improvement</span>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{width: '78%'}}></div>
                    </div>
                    <span className="progress-percentage">78%</span>
                  </div>
                  <div className="progress-item">
                    <span className="progress-label">Session Attendance</span>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{width: '92%'}}></div>
                    </div>
                    <span className="progress-percentage">92%</span>
                  </div>
                  <div className="progress-item">
                    <span className="progress-label">Goal Achievement</span>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{width: '65%'}}></div>
                    </div>
                    <span className="progress-percentage">65%</span>
                  </div>
                </div>
              </div>

              <div className="metric-section">
                <h3>Treatment Milestones</h3>
                <div className="milestones-list">
                  <div className="milestone achieved">
                    <span className="milestone-icon">✅</span>
                    <div className="milestone-content">
                      <span className="milestone-title">Anxiety Management Techniques</span>
                      <span className="milestone-date">Achieved: Aug 30, 2024</span>
                    </div>
                  </div>
                  <div className="milestone achieved">
                    <span className="milestone-icon">✅</span>
                    <div className="milestone-content">
                      <span className="milestone-title">Sleep Hygiene Improvement</span>
                      <span className="milestone-date">Achieved: Sep 05, 2024</span>
                    </div>
                  </div>
                  <div className="milestone in-progress">
                    <span className="milestone-icon">🔄</span>
                    <div className="milestone-content">
                      <span className="milestone-title">Social Anxiety Reduction</span>
                      <span className="milestone-date">In Progress</span>
                    </div>
                  </div>
                  <div className="milestone pending">
                    <span className="milestone-icon">⏳</span>
                    <div className="milestone-content">
                      <span className="milestone-title">Academic Stress Management</span>
                      <span className="milestone-date">Planned</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'scores' && (
          <section className="scores-section">
            <div className="section-header">
              <h2>Assessment Scores</h2>
              <p>PHQ-9 and GAD-7 score tracking over time</p>
            </div>

            <div className="scores-chart">
              <h3>Score Progression</h3>
              <svg width="100%" height="250" viewBox="0 0 600 250">
                {/* Chart background */}
                <defs>
                  <linearGradient id="phq9Gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
                    <stop offset="100%" stopColor="rgba(59, 130, 246, 0.05)" />
                  </linearGradient>
                  <linearGradient id="gad7Gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="rgba(245, 158, 11, 0.3)" />
                    <stop offset="100%" stopColor="rgba(245, 158, 11, 0.05)" />
                  </linearGradient>
                </defs>
                
                {/* Grid lines */}
                <g stroke="#E5E7EB" strokeWidth="1">
                  <line x1="50" y1="50" x2="550" y2="50" />
                  <line x1="50" y1="100" x2="550" y2="100" />
                  <line x1="50" y1="150" x2="550" y2="150" />
                  <line x1="50" y1="200" x2="550" y2="200" />
                </g>
                
                {/* PHQ-9 line */}
                <polyline
                  points="100,180 200,170 300,160 400,150 500,140"
                  fill="none"
                  stroke="#3B82F6"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                
                {/* GAD-7 line */}
                <polyline
                  points="100,170 200,165 300,155 400,145 500,135"
                  fill="none"
                  stroke="#F59E0B"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                
                {/* Data points */}
                <g>
                  <circle cx="100" cy="180" r="5" fill="#3B82F6" />
                  <circle cx="200" cy="170" r="5" fill="#3B82F6" />
                  <circle cx="300" cy="160" r="5" fill="#3B82F6" />
                  <circle cx="400" cy="150" r="5" fill="#3B82F6" />
                  <circle cx="500" cy="140" r="5" fill="#3B82F6" />
                  
                  <circle cx="100" cy="170" r="5" fill="#F59E0B" />
                  <circle cx="200" cy="165" r="5" fill="#F59E0B" />
                  <circle cx="300" cy="155" r="5" fill="#F59E0B" />
                  <circle cx="400" cy="145" r="5" fill="#F59E0B" />
                  <circle cx="500" cy="135" r="5" fill="#F59E0B" />
                </g>
                
                {/* Labels */}
                <g fill="#6B7280" fontSize="12" textAnchor="middle">
                  <text x="100" y="235">Aug 20</text>
                  <text x="200" y="235">Aug 27</text>
                  <text x="300" y="235">Sep 03</text>
                  <text x="400" y="235">Sep 10</text>
                  <text x="500" y="235">Current</text>
                </g>
                
                {/* Y-axis labels */}
                <g fill="#6B7280" fontSize="12" textAnchor="end">
                  <text x="45" y="55">25</text>
                  <text x="45" y="105">20</text>
                  <text x="45" y="155">15</text>
                  <text x="45" y="205">10</text>
                </g>
              </svg>
              
              <div className="chart-legend">
                <div className="legend-item">
                  <span className="legend-color phq9"></span>
                  <span>PHQ-9 (Depression)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-color gad7"></span>
                  <span>GAD-7 (Anxiety)</span>
                </div>
              </div>
            </div>

            <div className="scores-table">
              <h3>Score History</h3>
              <table className="scores-data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>PHQ-9</th>
                    <th>GAD-7</th>
                    <th>Severity</th>
                    <th>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {scoreHistory.map((score, index) => (
                    <tr key={index}>
                      <td>{new Date(score.date).toLocaleDateString()}</td>
                      <td className="score-cell phq9">{score.phq9}</td>
                      <td className="score-cell gad7">{score.gad7}</td>
                      <td>
                        <span className={`severity-badge ${score.severity.toLowerCase().replace('-', '')}`}>
                          {score.severity}
                        </span>
                      </td>
                      <td>
                        <span className={`trend-indicator ${score.trend}`}>
                          {score.trend === 'improving' ? '↗️' : 
                           score.trend === 'declining' ? '↘️' : '→'} 
                          {score.trend}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default PatientDetails;