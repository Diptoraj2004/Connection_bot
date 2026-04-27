import React, { useState } from 'react';
import './BookingStatus.css';

const BookingStatus = ({ booking, onStatusChange, userRole = 'student' }) => {
  const [isResponding, setIsResponding] = useState(false);
  const [responseData, setResponseData] = useState({
    action: '',
    newDate: '',
    newTime: '',
    message: ''
  });

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  const getStatusInfo = () => {
    switch (booking.status) {
      case 'pending':
        return {
          icon: '⏳',
          title: 'Booking Submitted',
          message: 'Waiting for counselor approval',
          color: '#f59e0b'
        };
      case 'accepted':
        return {
          icon: '✅',
          title: 'Booking Accepted',
          message: 'Your session has been confirmed',
          color: '#10b981'
        };
      case 'rejected':
        return {
          icon: '❌',
          title: 'Booking Declined',
          message: booking.rejectionMessage || 'Counselor is not available at this time',
          color: '#ef4444'
        };
      case 'rescheduled':
        return {
          icon: '🔄',
          title: 'New Time Proposed',
          message: `Counselor suggested: ${booking.proposedDate} at ${booking.proposedTime}`,
          color: '#6366f1'
        };
      case 'confirmed':
        return {
          icon: '✅',
          title: 'Session Confirmed',
          message: 'Your rescheduled session has been confirmed',
          color: '#10b981'
        };
      default:
        return {
          icon: '📋',
          title: 'Booking Status',
          message: 'Status unknown',
          color: '#6b7280'
        };
    }
  };

  // Counselor responds to booking
  const handleCounselorResponse = async (action) => {
    setIsResponding(true);
    try {
      const response = await fetch(`${API_BASE}/api/bookings/${booking._id}/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          action,
          proposedDate: responseData.newDate,
          proposedTime: responseData.newTime,
          message: responseData.message
        })
      });

      if (response.ok) {
        const updatedBooking = await response.json();
        onStatusChange(updatedBooking.booking);
        alert(`Booking ${action} successfully`);
      }
    } catch (error) {
      alert('Failed to respond to booking');
    } finally {
      setIsResponding(false);
    }
  };

  // Student accepts rescheduled time
  const handleStudentAcceptReschedule = async () => {
    setIsResponding(true);
    try {
      const response = await fetch(`${API_BASE}/api/bookings/${booking._id}/accept-reschedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const updatedBooking = await response.json();
        onStatusChange(updatedBooking.booking);
        alert('Rescheduled session accepted!');
      }
    } catch (error) {
      alert('Failed to accept rescheduled session');
    } finally {
      setIsResponding(false);
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="booking-status">
      <div className="status-header" style={{ borderColor: statusInfo.color }}>
        <div className="status-icon" style={{ backgroundColor: statusInfo.color }}>
          {statusInfo.icon}
        </div>
        <div className="status-content">
          <h3 style={{ color: statusInfo.color }}>{statusInfo.title}</h3>
          <p>{statusInfo.message}</p>
        </div>
      </div>

      <div className="booking-details">
        <div className="detail-row">
          <span className="label">Session:</span>
          <span className="value">{booking.sessionType}</span>
        </div>
        <div className="detail-row">
          <span className="label">Date:</span>
          <span className="value">{new Date(booking.appointmentDate).toLocaleDateString()}</span>
        </div>
        <div className="detail-row">
          <span className="label">Time:</span>
          <span className="value">{booking.appointmentTime}</span>
        </div>
        <div className="detail-row">
          <span className="label">Duration:</span>
          <span className="value">{booking.duration} minutes</span>
        </div>
      </div>

      {/* Counselor Actions */}
      {userRole === 'counselor' && booking.status === 'pending' && (
        <div className="counselor-actions">
          <h4>Respond to Booking Request</h4>
          
          <div className="response-options">
            <button
              onClick={() => handleCounselorResponse('accept')}
              className="accept-btn"
              disabled={isResponding}
            >
              ✅ Accept
            </button>
            
            <div className="reschedule-section">
              <h5>Or propose new time:</h5>
              <div className="reschedule-inputs">
                <input
                  type="date"
                  value={responseData.newDate}
                  onChange={(e) => setResponseData(prev => ({ ...prev, newDate: e.target.value }))}
                  min={new Date().toISOString().split('T')[0]}
                />
                <select
                  value={responseData.newTime}
                  onChange={(e) => setResponseData(prev => ({ ...prev, newTime: e.target.value }))}
                >
                  <option value="">Select time</option>
                  <option value="09:00">09:00</option>
                  <option value="10:00">10:00</option>
                  <option value="11:00">11:00</option>
                  <option value="14:00">14:00</option>
                  <option value="15:00">15:00</option>
                  <option value="16:00">16:00</option>
                </select>
              </div>
              <textarea
                placeholder="Message to student (optional)"
                value={responseData.message}
                onChange={(e) => setResponseData(prev => ({ ...prev, message: e.target.value }))}
                rows={2}
              />
              <button
                onClick={() => handleCounselorResponse('reschedule')}
                className="reschedule-btn"
                disabled={isResponding || !responseData.newDate || !responseData.newTime}
              >
                🔄 Propose New Time
              </button>
            </div>
            
            <button
              onClick={() => handleCounselorResponse('reject')}
              className="reject-btn"
              disabled={isResponding}
            >
              ❌ Decline
            </button>
          </div>
        </div>
      )}

      {/* Student Actions for Rescheduled Bookings */}
      {userRole === 'student' && booking.status === 'rescheduled' && (
        <div className="student-actions">
          <div className="proposed-time">
            <h4>Proposed New Time:</h4>
            <p><strong>{new Date(booking.proposedDate).toLocaleDateString()} at {booking.proposedTime}</strong></p>
            {booking.counselorMessage && <p className="counselor-message">"{booking.counselorMessage}"</p>}
          </div>
          
          <div className="action-buttons">
            <button
              onClick={handleStudentAcceptReschedule}
              className="accept-reschedule-btn"
              disabled={isResponding}
            >
              ✅ Accept New Time
            </button>
            <button
              onClick={() => alert('Request a different time (feature coming soon)')}
              className="decline-reschedule-btn"
            >
              ❌ Decline
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookingStatus;
