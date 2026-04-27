import React, { useState, useEffect } from 'react';
import BookingForm from './BookingForm';
import BookingStatus from './BookingStatus';
import './BookingModal.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const BookingModal = ({ onClose, onBookingCreate }) => {
  const [bookingStep, setBookingStep] = useState('form'); // 'form', 'pending', 'confirmed'
  const [bookingData, setBookingData] = useState(null);
  const [therapists, setTherapists] = useState([]);
  const [loadingTherapists, setLoadingTherapists] = useState(true);

  useEffect(() => {
    // Fetch actual therapists from backend
    const fetchTherapists = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/api/users?role=counselor`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization':` Bearer ${localStorage.getItem('token')}`
            }
          }
        );
        if (!response.ok) throw new Error('Failed to load therapists');
        const data = await response.json();
        setTherapists(data.users); // or data.results, adjust for your actual response!
      } catch (error) {
        console.error('Error fetching therapists:', error);
      } finally {
        setLoadingTherapists(false);
      }
    };
    fetchTherapists();
  }, []);

  const handleBookingSubmit = async (formData) => {
    try {
      const response = await fetch(`${API_BASE}/api/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const booking = await response.json();
        setBookingData(booking.booking);
        setBookingStep('pending');
        onBookingCreate && onBookingCreate(booking.booking);
      } else {
        throw new Error('Failed to create booking');
      }
    } catch (error) {
      console.error('Booking error:', error);
      alert('Failed to create booking. Please try again.');
    }
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <div className="booking-modal-overlay" onClick={handleClose}>
      <div className="booking-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            {bookingStep === 'form' && 'Book Therapy Session'}
            {bookingStep === 'pending' && 'Booking Submitted'}
            {bookingStep === 'confirmed' && 'Booking Confirmed'}
          </h2>
          <button className="close-btn" onClick={handleClose}>×</button>
        </div>
        <div className="modal-content">
          {bookingStep === 'form' && (
            loadingTherapists ? (
              <div style={{ padding: '2em', textAlign: 'center' }}>Loading therapists...</div>
            ) : (
              <BookingForm
                therapists={therapists}
                onSubmit={handleBookingSubmit}
              />
            )
          )}
          {(bookingStep === 'pending' || bookingStep === 'confirmed') && (
            <BookingStatus
              booking={bookingData}
              status={bookingStep}
              onStatusChange={setBookingStep}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default BookingModal;