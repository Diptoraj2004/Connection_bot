import React, { useState, useEffect } from 'react';
import BookingForm from '../booking/BookingForm';
import './BookingTherapySessionsPage.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const BookingTherapySessionsPage = () => {
  const [therapists, setTherapists] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTherapists = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/users?role=counselor`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}` // NO leading space
          }
        });
        const data = await res.json();
        setTherapists(data.users || []);
      } catch (err) {
        console.error('Failed to load therapists', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTherapists();
  }, []);

  const handleBookingSubmit = async (formData) => {
    try {
      const res = await fetch(`${API_BASE}/api/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      if (!res.ok) {
        const errInfo = await res.json();
        throw new Error(errInfo.message || 'Booking failed');
      }
      const result = await res.json();
      alert('Booking successful!');
      console.log('New booking:', result.booking);
    } catch (err) {
      console.error(err);
      alert('Failed to create booking: ' + err.message);
    }
  };

  if (loading) {
    return <div className="therapy-session-page"><p>Loading therapists...</p></div>;
  }

  return (
    <div className="therapy-session-page">
      <BookingForm
        therapists={therapists}
        onSubmit={handleBookingSubmit}
      />
    </div>
  );
};

export default BookingTherapySessionsPage;
