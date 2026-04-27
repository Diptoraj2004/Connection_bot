import React, { useState } from 'react';
import './BookingRequestCard.css';

const BookingRequestCard = ({ booking, onApprove, onDecline }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAction = async (action) => {
    setIsProcessing(true);
    try {
      if (action === 'approve') {
        await onApprove();
      } else {
        await onDecline();
      }
    } finally {
      setIsProcessing(false);
    }
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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const getUrgencyLevel = () => {
    if (booking.priority === 'urgent') return 'urgent';
    if (booking.sessionType === 'emergency') return 'emergency';
    return 'normal';
  };

  const urgencyLevel = getUrgencyLevel();

  return (
    <div className={`booking-request-card ${urgencyLevel}`}>
      <div className="request-header">
        <div className="student-info">
          <div className="student-avatar">
            👤
          </div>
          <div className="student-details">
            <h4 className="student-name">{booking.patientId?.name || 'Student'}</h4>
            <span className="student-id">ID: {booking.patientId?.studentId || 'N/A'}</span>
          </div>
        </div>
        
        <div className="request-meta">
          <span className={`priority-badge priority-${booking.priority}`}>
            {booking.priority === 'urgent' && '🚨'} {booking.priority}
          </span>
          <span className="request-time">
            {new Date(booking.createdAt).toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit'
            })}
          </span>
        </div>
      </div>

      <div className="appointment-details">
        <div className="detail-row">
          <span className="detail-icon">📅</span>
          <span className="detail-label">Date & Time:</span>
          <span className="detail-value">
            {formatDate(booking.appointmentDate)} at {formatTime(booking.appointmentTime)}
          </span>
        </div>
        
        <div className="detail-row">
          <span className="detail-icon">🕒</span>
          <span className="detail-label">Duration:</span>
          <span className="detail-value">{booking.duration} minutes</span>
        </div>
        
        <div className="detail-row">
          <span className="detail-icon">💬</span>
          <span className="detail-label">Session Type:</span>
          <span className="detail-value session-type-badge">
            {booking.sessionType}
          </span>
        </div>
      </div>

      {booking.symptoms && booking.symptoms.length > 0 && (
        <div className="concerns-section">
          <span className="concerns-label">
            <span className="detail-icon">🎯</span>
            Concerns:
          </span>
          <div className="concerns-list">
            {booking.symptoms.map((symptom, index) => (
              <span key={index} className="concern-tag">{symptom}</span>
            ))}
          </div>
        </div>
      )}

      {booking.notes && (
        <div className="notes-section">
          <span className="notes-label">
            <span className="detail-icon">📝</span>
            Additional Notes:
          </span>
          <p className="notes-text">{booking.notes}</p>
        </div>
      )}

      <div className="request-actions">
        <button
          className="action-btn decline-btn"
          onClick={() => handleAction('decline')}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : '❌ Decline'}
        </button>
        
        <button
          className="action-btn approve-btn"
          onClick={() => handleAction('approve')}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : '✅ Approve & Schedule'}
        </button>
      </div>
    </div>
  );
};

export default BookingRequestCard;
