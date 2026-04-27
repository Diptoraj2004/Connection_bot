// middleware/bookingMiddleware.js
const Booking = require('../models/Booking');

exports.checkBookingOwnership = async (req, res, next) => {
  try {
    const { bookingId } = req.params;
    const userId = req.user.id;
    const userRole = req.user.role;

    const booking = await Booking.findById(bookingId);
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const isOwner = booking.patientId.toString() === userId ||
                    booking.therapistId.toString() === userId ||
                    userRole === 'admin';

    if (!isOwner) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    req.booking = booking;
    next();
  } catch (error) {
    console.error('checkBookingOwnership error:', error);
    res.status(500).json({ success: false, message: 'Server error', error: error.message });
  }
};

exports.validateBookingTime = (req, res, next) => {
  const { appointmentDate, appointmentTime } = req.body;
  if (!appointmentDate || !appointmentTime) return next();

  const bookingDateTime = new Date(`${appointmentDate}T${appointmentTime}`);
  const now = new Date();

  const oneHourFromNow = new Date(now.getTime() + 60 * 60 * 1000);
  if (bookingDateTime < oneHourFromNow) {
    return res.status(400).json({ success: false, message: 'Booking must be at least 1 hour in the future' });
  }

  const hour = parseInt(appointmentTime.split(':')[0], 10);
  if (hour < 9 || hour >= 17) {
    return res.status(400).json({ success: false, message: 'Bookings are only available between 9 AM and 5 PM' });
  }

  next();
};
