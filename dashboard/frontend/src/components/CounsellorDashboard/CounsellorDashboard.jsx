import React, { useState, useEffect } from 'react';
import './CounsellorDashboard.css';
import {useAuth} from '../../context/AuthContext';
import todaysScheduleImg from '../../assets/images/scheduletoday.jpg';
import clinicalToolsImg from '../../assets/images/notes.jpg';
import wellnessReportsImg from '../../assets/images/wellnessreports.jpg';
import therapyEffectivenessImg from '../../assets/images/predictiveanalysis.jpg';

import TodaysSchedule from './TodaysSchedule';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Enhanced Patient Details Component with proper styling
const PatientDetails = ({ patient, onBack }) => {
  const [activeTab, setActiveTab] = useState('treatment-history');
  // ... rest of PatientDetails is unchanged ...
  // [Keep your PatientDetails code as-is]
};

const CounselorDashboard = () => {
  const {user}=useAuth();
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedTab, setSelectedTab] = useState('dashboard');

  const [todaysBookings, setTodaysBookings] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [patientQueue, setPatientQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      // Fetch accepted, confirmed, and pending bookings
      const [acceptedRes, confirmedRes, pendingRes] = await Promise.all([
        fetch(`${API_BASE}/api/bookings?status=accepted`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`${API_BASE}/api/bookings?status=confirmed`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`${API_BASE}/api/bookings?status=pending`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
      ]);
      const acceptedData = await acceptedRes.json();
      const confirmedData = await confirmedRes.json();
      const pendingData = await pendingRes.json();

      // Filter only today's date bookings
      const todayISO = new Date().toISOString().split('T')[0];
      const isToday = (d) => new Date(d).toISOString().split('T')[0] === todayISO;
      const todayBookings = [
        ...(acceptedData.bookings || []),
        ...(confirmedData.bookings || [])
      ].filter(b => isToday(b.appointmentDate));
      const todayPendingRequests = (pendingData.bookings || []).filter(b => isToday(b.appointmentDate));

      setTodaysBookings(todayBookings);
      setPendingRequests(todayPendingRequests);
      buildPatientQueue(todayBookings);
    } catch (err) {
      console.error('Error fetching bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const buildPatientQueue = (confirmedBookings) => {
    const patientMap = new Map();
    confirmedBookings.forEach(booking => {
      const p = booking.patientId;
      if (p && !patientMap.has(p._id)) {
        let risk = 'low';
        if (booking.priority === 'urgent' || booking.sessionType === 'emergency') risk = 'critical';
        else if (booking.priority === 'high') risk = 'high';
        else if (booking.priority === 'medium') risk = 'medium';

        const phq9 = (typeof p.phq9 === 'number') ? p.phq9 : (risk === 'critical' ? 22 : risk === 'high' ? 17 : risk === 'medium' ? 12 : 7);
        const gad7 = (typeof p.gad7 === 'number') ? p.gad7 : (risk === 'critical' ? 18 : risk === 'high' ? 13 : risk === 'medium' ? 9 : 5);

        patientMap.set(p._id, {
          ...p,
          phq9,
          gad7,
          risk,
          trend: risk === 'critical' ? 'critical' : risk === 'high' ? 'declining' : risk === 'medium' ? 'stable' : 'improving',
          lastSession: new Date(booking.appointmentDate).toLocaleDateString()
        });
      }
    });
    const sorted = Array.from(patientMap.values()).sort((a, b) => {
      const order = { critical: 4, high: 3, medium: 2, low: 1 };
      return order[b.risk] - order[a.risk];
    });
    setPatientQueue(sorted);
  };

  const formatTime = (timeString) => {
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    setSelectedTab('patient-details');
  };

  const aiSuggestions = [
    {
      type: 'treatment',
      patient: 'John Doe',
      suggestion: 'Consider increasing CBT sessions to twice weekly based on declining mood patterns'
    },
    {
      type: 'crisis',
      patient: 'Emily Chen',
      suggestion: 'High risk indicators detected. Recommend immediate safety assessment'
    },
    {
      type: 'medication',
      patient: 'Sarah Brown', 
      suggestion: 'Mood stabilization observed. Consider discussing medication adjustment with psychiatrist'
    }
  ];

  if (selectedTab === 'patient-details' && selectedPatient) {
    return <PatientDetails patient={selectedPatient} onBack={() => setSelectedTab('dashboard')} />;
  }

  if (selectedTab === 'schedule') {
    return (
      <div className="counselor-dashboard">
        <header className="dashboard-header">
          <div className="header-content">
            <button onClick={() => setSelectedTab('dashboard')} className="back-btn">
              ← Back to Dashboard
            </button>
            <h1>Today's Schedule & Requests</h1>
          </div>
        </header>
        <TodaysSchedule onBookingUpdate={fetchBookings} />
      </div>
    );
  }

  return (
    <div className="counselor-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="counselor-info">
            <h1>{user?.name || 'Counselor'}</h1>
            <p>
              {user?.designation || user?.role === 'counselor'
              ? 'Licensed Professional Counselor'
              : user?.role || ''}
            </p>
            <p>Licensed Professional Counselor</p>
            <div className="status-indicator">
              <span className="status-dot online"></span>
              <span>Available</span>
            </div>
          </div>
          <div className="header-stats">
            <div className="stat-item">
              <span className="stat-number">{todaysBookings.length}</span>
              <span className="stat-label">Today's Appointments</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{pendingRequests.length}</span>
              <span className="stat-label">Pending Requests</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{patientQueue.length}</span>
              <span className="stat-label">Active Patients</span>
            </div>
            <div className="crisis-hotline">
              <button className="hotline-btn">🚨 Crisis Hotline: 1800-CRISIS</button>
            </div>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Today's Schedule */}
        <section className="card schedule-card">
          <div className="card-header">
            <h3>Today's Schedule</h3>
            <div className="card-actions">
              <span className="schedule-date">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </span>
              <button onClick={() => setSelectedTab('schedule')} className="view-all-btn">
                View All
              </button>
            </div>
          </div>
          
          <div className="schedule-visual">
            <img src={todaysScheduleImg} alt="Today's Schedule" className="schedule-bg" />
            <div className="schedule-overlay">
              <div className="schedule-summary">
                <div className="summary-item">
                  <span className="summary-number">{todaysBookings.length}</span>
                  <span className="summary-label">Confirmed</span>
                </div>
                <div className="summary-item">
                  <span className="summary-number">{pendingRequests.length}</span>
                  <span className="summary-label">Pending</span>
                </div>
              </div>
            </div>
          </div>

          <div className="schedule-list">
            {loading ? (
              <div className="loading-state">Loading schedule...</div>
            ) : (
              <>
                {pendingRequests.slice(0, 2).map((booking) => (
                  <div key={booking._id} className="appointment-item pending">
                    <div className="appointment-time">
                      {formatTime(booking.appointmentTime)}
                    </div>
                    <div className="appointment-details">
                      <span className="appointment-patient">
                        {booking.patientId?.name || 'Student'}
                      </span>
                      <span className="appointment-type">{booking.sessionType}</span>
                    </div>
                    <div className="appointment-status pending">
                      Needs Approval
                    </div>
                  </div>
                ))}
                
                {todaysBookings.slice(0, 4 - Math.min(pendingRequests.length, 2)).map((booking) => (
                  <div key={booking._id} className="appointment-item confirmed">
                    <div className="appointment-time">
                      {formatTime(booking.appointmentTime)}
                    </div>
                    <div className="appointment-details">
                      <span className="appointment-patient">
                        {booking.patientId?.name || 'Student'}
                      </span>
                      <span className="appointment-type">{booking.sessionType}</span>
                    </div>
                    <div className="appointment-status confirmed">
                      Confirmed
                    </div>
                  </div>
                ))}
                
                {(todaysBookings.length === 0 && pendingRequests.length === 0) && (
                  <div className="empty-schedule-mini">
                    <p>No appointments scheduled for today</p>
                  </div>
                )}
              </>
            )}
          </div>
        </section>

        {/* Patient Priority Queue */}
        <section className="card priority-card">
          <div className="card-header">
            <h3>Patient Priority Queue ({patientQueue.length})</h3>
            <span className="ai-badge">🤖 AI Sorted</span>
          </div>
          <div className="priority-list">
            {loading ? (
              <div className="loading-state">Loading patients...</div>
            ) : patientQueue.length === 0 ? (
              <div className="empty-queue">
                <p>No active patients at the moment</p>
                <span>Approved bookings will appear here</span>
              </div>
            ) : (
              patientQueue.map((patient, index) => (
                <div
                  key={patient._id || index}
                  className={`priority-item ${patient.risk} clickable`}
                  onClick={() => handlePatientSelect(patient)}
                >
                  <div className="priority-main">
                    <div className="patient-info">
                      <span className="patient-name">{patient.name}</span>
                      <span className="patient-id">{patient.studentId || patient.id}</span>
                    </div>
                    <div className="risk-indicator">
                      <span className={`risk-badge ${patient.risk}`}>{patient.risk}</span>
                      <span className={`trend-arrow ${patient.trend}`}>
                        {patient.trend === 'improving' ? '↗️' : 
                        patient.trend === 'declining' ? '↘️' : 
                        patient.trend === 'critical' ? '🚨' : '→'}
                      </span>
                    </div>
                  </div>
                  <div className="patient-scores">
                    <div className="score-item">
                      <span className="score-label">PHQ-9:</span>
                      <span className="score-value">{patient.phq9}</span>
                    </div>
                    <div className="score-item">
                      <span className="score-label">GAD-7:</span>
                      <span className="score-value">{patient.gad7}</span>
                    </div>
                  </div>
                  <div className="last-session">Last: {patient.lastSession}</div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* AI Clinical Support */}
        <section className="card ai-support-card">
          <div className="card-header">
            <h3>🤖 AI Clinical Support</h3>
            <button className="refresh-btn">🔄 Refresh</button>
          </div>
          <div className="ai-suggestions">
            {aiSuggestions.map((suggestion, index) => (
              <div key={index} className={`suggestion-item ${suggestion.type}`}>
                <div className="suggestion-header">
                  <span className={`suggestion-type ${suggestion.type}`}>
                    {suggestion.type === 'treatment' ? '📋' : 
                     suggestion.type === 'crisis' ? '🚨' : '💊'}
                    {suggestion.type.toUpperCase()}
                  </span>
                  <span className="suggestion-patient">{suggestion.patient}</span>
                </div>
                <p className="suggestion-text">{suggestion.suggestion}</p>
                <div className="suggestion-actions">
                  <button className="action-btn primary">Apply</button>
                  <button className="action-btn secondary">Review</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Clinical Tools */}
        <section className="card tools-card">
          <div className="card-header">
            <h3>Clinical Tools</h3>
            <button className="tools-menu-btn">⋯</button>
          </div>
          <div className="tools-visual">
            <img src={clinicalToolsImg} alt="Clinical Tools" className="tools-bg" />
            <div className="tools-overlay">
              <div className="tools-grid">
                <div className="tool-item">
                  <div className="tool-icon">📝</div>
                  <span>Session Notes</span>
                </div>
                <div className="tool-item">
                  <div className="tool-icon">📊</div>
                  <span>Assessment Forms</span>
                </div>
                <div className="tool-item">
                  <div className="tool-icon">📋</div>
                  <span>Treatment Plans</span>
                </div>
                <div className="tool-item">
                  <div className="tool-icon">📄</div>
                  <span>Reports</span>
                </div>
              </div>
            </div>
          </div>
          <div className="tools-actions">
            <button className="tool-action-btn">
              <span className="tool-action-icon">📝</span>
              <span>New Session Note</span>
            </button>
            <button className="tool-action-btn">
              <span className="tool-action-icon">📊</span>
              <span>Generate Report</span>
            </button>
            <button className="tool-action-btn">
              <span className="tool-action-icon">🔒</span>
              <span>Secure Archive</span>
            </button>
          </div>
        </section>

        {/* Quick Analytics */}
        <section className="card analytics-card">
          <div className="card-header">
            <h3>Performance Analytics</h3>
            <select className="period-select">
              <option>This Week</option>
              <option>This Month</option>
              <option>This Quarter</option>
            </select>
          </div>
          <div className="analytics-grid">
            <div className="analytics-item">
              <div className="analytics-icon">📈</div>
              <div className="analytics-data">
                <span className="analytics-value">78%</span>
                <span className="analytics-label">Improvement Rate</span>
              </div>
            </div>
            <div className="analytics-item">
              <div className="analytics-icon">🛡️</div>
              <div className="analytics-data">
                <span className="analytics-value">94%</span>
                <span className="analytics-label">Crisis Prevention</span>
              </div>
            </div>
            <div className="analytics-item">
              <div className="analytics-icon">⭐</div>
              <div className="analytics-data">
                <span className="analytics-value">4.8</span>
                <span className="analytics-label">Patient Satisfaction</span>
              </div>
            </div>
            <div className="analytics-item">
              <div className="analytics-icon">📅</div>
              <div className="analytics-data">
                <span className="analytics-value">{todaysBookings.length}</span>
                <span className="analytics-label">Sessions Today</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default CounselorDashboard;
