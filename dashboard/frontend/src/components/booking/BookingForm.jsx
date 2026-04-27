import React, { useState } from 'react';
import './BookingForm.css';

const BookingForm = ({ therapists = [], onSubmit }) => {
  const [formData, setFormData] = useState({
    therapistId: '',
    sessionType: 'individual',
    appointmentDate: '',
    appointmentTime: '',
    duration: 50,
    notes: '',
    symptoms: [],
    priority: 'medium'
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const sessionTypes = [
    { value: 'individual', label: 'Individual Therapy', description: '1-on-1 session' },
    { value: 'group', label: 'Group Therapy', description: 'Small group session' },
    { value: 'emergency', label: 'Emergency Session', description: 'Urgent consultation' },
    { value: 'follow-up', label: 'Follow-up', description: 'Continue previous session' }
  ];

  const timeSlots = [
    '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'
  ];

  const commonSymptoms = [
    'Anxiety', 'Depression', 'Stress', 'Sleep Issues', 'Academic Pressure',
    'Relationship Issues', 'Social Anxiety', 'Panic Attacks', 'Low Mood'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSymptomToggle = (symptom) => {
    setFormData(prev => ({
      ...prev,
      symptoms: prev.symptoms.includes(symptom)
        ? prev.symptoms.filter(s => s !== symptom)
        : [...prev.symptoms, symptom]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.therapistId || !formData.appointmentDate || !formData.appointmentTime) {
      alert('Please fill in all required fields');
      return;
    }
    setIsSubmitting(true);
    try {
      await onSubmit(formData);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="booking-form" onSubmit={handleSubmit}>
      {/* Therapist Selection */}
      <div className="form-section">
        <label className="form-label">Select Therapist *</label>
        <div className="therapist-grid">
          {(therapists || []).map(therapist => (
            <div
              key={therapist._id}
              className={`therapist-card ${formData.therapistId === therapist._id ? 'selected' : ''}`}
              onClick={() => setFormData(prev => ({ ...prev, therapistId: therapist._id }))}
            >
              {therapist.avatar && <div className="therapist-avatar">{therapist.avatar}</div>}
              <div className="therapist-info">
                <h4>{therapist.name}</h4>
                <p className="therapist-specialization">
                  {Array.isArray(therapist.specialization)
                    ? therapist.specialization.join(', ')
                    : therapist.specialization}
                </p>
                <div className="therapist-meta">
                  <span className="experience">{therapist.experience} years</span>
                  {therapist.rating && <span className="rating">⭐ {therapist.rating}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Session Type */}
      <div className="form-section">
        <label className="form-label">Session Type *</label>
        <div className="session-type-grid">
          {sessionTypes.map(type => (
            <label key={type.value} className="session-type-option">
              <input
                type="radio"
                name="sessionType"
                value={type.value}
                checked={formData.sessionType === type.value}
                onChange={handleInputChange}
              />
              <div className="session-type-content">
                <span className="session-type-label">{type.label}</span>
                <span className="session-type-description">{type.description}</span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Date and Time */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Date *</label>
          <input
            type="date"
            name="appointmentDate"
            value={formData.appointmentDate}
            onChange={handleInputChange}
            min={new Date().toISOString().split('T')[0]}
            className="form-input"
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Time *</label>
          <select
            name="appointmentTime"
            value={formData.appointmentTime}
            onChange={handleInputChange}
            className="form-select"
            required
          >
            <option value="">Select time</option>
            {timeSlots.map(time => (
              <option key={time} value={time}>{time}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Duration and Priority */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Duration (minutes)</label>
          <select
            name="duration"
            value={formData.duration}
            onChange={handleInputChange}
            className="form-select"
          >
            <option value={30}>30 minutes</option>
            <option value={50}>50 minutes</option>
            <option value={90}>90 minutes</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Priority</label>
          <select
            name="priority"
            value={formData.priority}
            onChange={handleInputChange}
            className="form-select"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
      </div>

      {/* Symptoms */}
      <div className="form-section">
        <label className="form-label">Current Concerns (Optional)</label>
        <div className="symptoms-grid">
          {commonSymptoms.map(symptom => (
            <button
              key={symptom}
              type="button"
              className={`symptom-tag ${formData.symptoms.includes(symptom) ? 'selected' : ''}`}
              onClick={() => handleSymptomToggle(symptom)}
            >
              {symptom}
            </button>
          ))}
        </div>
      </div>

      {/* Notes */}
      <div className="form-section">
        <label className="form-label">Additional Notes (Optional)</label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleInputChange}
          className="form-textarea"
          rows={3}
          placeholder="Please share any additional information that might help your therapist..."
        />
      </div>

      {/* Submit Button */}
      <div className="form-actions">
        <button
          type="submit"
          className="submit-btn"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Booking...' : 'Book Session'}
        </button>
      </div>
    </form>
  );
};

export default BookingForm;