import React, { useState, useEffect } from 'react';
import BookingRequestCard from './BookingRequestCard';
import './TodaysSchedule.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const TodaysSchedule = ({ onBookingUpdate }) => {
  const [bookings, setBookings] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  // Refetch all data (pending + confirmed) every time this view is opened or updated
  useEffect(() => {
    fetchAll();
    // eslint-disable-next-line
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    await Promise.all([fetchTodaysSchedule(), fetchPendingRequests()]);
    setLoading(false);
  };

  const isToday = dateString =>
    new Date(dateString).toISOString().split('T')[0] === new Date().toISOString().split('T')[0];

  const fetchTodaysSchedule = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/bookings?status=confirmed`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setBookings((data.bookings || []).filter(b => isToday(b.appointmentDate)));
    } catch (error) {
      console.error('Error fetching schedule:', error);
    }
  };

  const fetchPendingRequests = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/bookings?status=pending`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setPendingRequests((data.bookings || []).filter(b => isToday(b.appointmentDate)));
    } catch (error) {
      console.error('Error fetching pending requests:', error);
    }
  };

  const handleBookingAction = async (bookingId, action) => {
    try {
      const res = await fetch(`${API_BASE}/api/bookings/${bookingId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          status: action === 'approve' ? 'confirmed' : 'cancelled',
          notes: action === 'approve' ? 'Approved by counselor' : 'Declined by counselor'
        })
      });
      if (!res.ok) throw new Error();
      await fetchAll();
      if (onBookingUpdate) onBookingUpdate();
      alert(`Booking ${action === 'approve' ? 'approved' : 'declined'} successfully!`);
    } catch {
      alert('Failed to update booking. Please try again.');
    }
  };

  const formatTime = t => {
    const [h, m] = t.split(':');
    const d = new Date(); d.setHours(+h, +m);
    return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  };

  if (loading) {
    return (
      <div className="schedule-loading">
        <div className="loading-spinner"></div>
        <p>Loading schedule...</p>
      </div>
    );
  }

  return (
    <div className="todays-schedule">
      {pendingRequests.length > 0 && (
        <div className="schedule-section">
          <div className="section-header">
            <h3>
              <span className="pending-indicator">🔔</span>
              Pending Approval ({pendingRequests.length})
            </h3>
            <p className="section-subtitle">
              New booking requests awaiting your approval
            </p>
          </div>
          <div className="booking-requests-list">
            {pendingRequests.map(b => (
              <BookingRequestCard
                key={b._id}
                booking={b}
                onApprove={() => handleBookingAction(b._id, 'approve')}
                onDecline={() => handleBookingAction(b._id, 'decline')}
              />
            ))}
          </div>
        </div>
      )}

      <div className="schedule-section">
        <div className="section-header">
          <h3>
            <span className="schedule-indicator">📅</span>
            Today's Schedule ({bookings.length})
          </h3>
          <p className="section-subtitle">
            Your confirmed appointments for today
          </p>
        </div>
        {bookings.length === 0 ? (
          <div className="empty-schedule">
            <div className="empty-icon">📋</div>
            <p>No confirmed appointments for today</p>
            <span className="empty-subtitle">
              {pendingRequests.length > 0
                ? "Review pending requests above to add to your schedule"
                : "Take some time to rest or catch up on other tasks"}
            </span>
          </div>
        ) : (
          <div className="schedule-timeline">
            {bookings
              .sort((a, b) => a.appointmentTime.localeCompare(b.appointmentTime))
              .map(b => (
                <div key={b._id} className="timeline-appointment">
                  <div className="appointment-time">
                    <span className="time">{formatTime(b.appointmentTime)}</span>
                    <span className="duration">{b.duration}min</span>
                  </div>
                  <div className="appointment-card">
                    <div className="appointment-header">
                      <div className="patient-info">
                        <h4>{b.patientId?.name || 'Student'}</h4>
                        <span className="session-type">{b.sessionType}</span>
                      </div>
                      <div className="appointment-actions">
                        <button className="action-btn join-btn">📹 Join Session</button>
                        <button className="action-btn more-btn">⋮</button>
                      </div>
                    </div>
                    {b.symptoms?.length > 0 && (
                      <div className="symptoms-list">
                        <span className="symptoms-label">Concerns:</span>
                        {b.symptoms.map((s, i) => (
                          <span key={i} className="symptom-tag">{s}</span>
                        ))}
                      </div>
                    )}
                    {b.notes && (
                      <div className="appointment-notes">
                        <span className="notes-label">Notes:</span>
                        <p className="notes-text">{b.notes}</p>
                      </div>
                    )}
                    <div className="appointment-meta">
                      <span className={`priority-indicator priority-${b.priority}`}>
                        {b.priority} priority
                      </span>
                      <span className="booking-id">#{b._id.slice(-6)}</span>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TodaysSchedule;
