const mongoose = require('mongoose');
const { validationResult } = require('express-validator');
const Booking = require('../models/Booking');
const User = require('../models/User');
const NotificationService = require('../services/notificationService');
const { getIO } = require('../utils/socketManager');

/**
 * Create a new booking (students only)
 */
exports.createBooking = async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res
        .status(400)
        .json({ success: false, message: 'Validation errors', errors: errors.array() });
    }

    const {
      therapistId,
      sessionType,
      appointmentDate,
      appointmentTime,
      duration,
      notes,
      symptoms,
      priority
    } = req.body;
    const patientId = req.user.id;

    const therapist = await User.findById(therapistId);
    if (!therapist || !['therapist', 'counselor'].includes(therapist.role)) {
      return res.status(404).json({ success: false, message: 'Therapist not found' });
    }

    const conflict = await Booking.findOne({
      therapistId,
      appointmentDate: new Date(appointmentDate),
      appointmentTime,
      status: { $in: ['scheduled', 'confirmed'] }
    });
    if (conflict) {
      return res.status(409).json({ success: false, message: 'Time slot not available' });
    }

    let price = 100;
    if (sessionType === 'emergency') price = 150;
    if (sessionType === 'group') price = 75;
    if (therapist.experience > 5) price += 50;

    const booking = new Booking({
      patientId,
      therapistId,
      sessionType,
      appointmentDate: new Date(appointmentDate),
      appointmentTime,
      duration: duration || 50,
      notes: notes || '',
      symptoms: symptoms || [],
      priority: priority || 'medium',
      price,
      status: 'pending'
    });

    booking.meetingLink = `https://meet.mindcare.com/session/${new mongoose.Types.ObjectId()}`;
    await booking.save();

    const populated = await Booking.findById(booking._id)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience');

    try {
      await NotificationService.sendBookingConfirmation(
        populated,
        populated.patientId,
        populated.therapistId
      );
    } catch (e) {
      console.error('Notification failure:', e);
    }

    try {
      const io = getIO();
      io.to(`user_${populated.patientId._id}`).emit('booking_notification', populated);
      io.to(`user_${populated.therapistId._id}`).emit('booking_notification', populated);
    } catch (e) {
      console.warn('Socket emit failed:', e.message);
    }

    res
      .status(201)
      .json({ success: true, message: 'Booking created successfully', booking: populated });
  } catch (error) {
    console.error('Error creating booking:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Get bookings for current user
 */
exports.getUserBookings = async (req, res) => {
  try {
    const userId = req.user.id;
    const { status, page = 1, limit = 10 } = req.query;

    const query = {};
    if (req.user.role === 'student') query.patientId = userId;
    else if (['therapist', 'counselor'].includes(req.user.role)) query.therapistId = userId;
    if (status) query.status = status;

    const bookings = await Booking.find(query)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience')
      .sort({ appointmentDate: -1 })
      .skip((page - 1) * limit)
      .limit(parseInt(limit));

    const total = await Booking.countDocuments(query);

    res.status(200).json({
      success: true,
      bookings,
      totalPages: Math.ceil(total / limit),
      currentPage: parseInt(page),
      totalBookings: total
    });
  } catch (error) {
    console.error('Error fetching bookings:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Get a single booking by ID
 */
exports.getBookingById = async (req, res) => {
  try {
    const { bookingId } = req.params;
    const booking = await Booking.findById(bookingId)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience');
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const userId = req.user.id;
    const access =
      booking.patientId._id.toString() === userId ||
      booking.therapistId._id.toString() === userId ||
      req.user.role === 'admin';
    if (!access) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    res.status(200).json({ success: true, booking });
  } catch (error) {
    console.error('Error fetching booking:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Update booking status
 */
exports.updateBookingStatus = async (req, res) => {
  try {
    const { bookingId } = req.params;
    const { status, notes } = req.body;
    const booking = await Booking.findById(bookingId);
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const userId = req.user.id;
    const canUpdate =
      booking.therapistId.toString() === userId ||
      booking.patientId.toString() === userId ||
      ['admin', 'counselor', 'therapist'].includes(req.user.role);
    if (!canUpdate) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    booking.status = status;
    if (notes) booking.notes = notes;
    await booking.save();

    const updated = await Booking.findById(bookingId)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience');

    try {
      const io = getIO();
      io.to(`user_${updated.patientId._id}`).emit('booking_notification', updated);
      io.to(`user_${updated.therapistId._id}`).emit('booking_notification', updated);
    } catch (e) {}

    res.status(200).json({ success: true, message: 'Booking updated', booking: updated });
  } catch (error) {
    console.error('Error updating booking:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Cancel booking
 */
exports.cancelBooking = async (req, res) => {
  try {
    const { bookingId } = req.params;
    const { reason } = req.body;
    const booking = await Booking.findById(bookingId);
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const userId = req.user.id;
    const canCancel =
      booking.patientId.toString() === userId ||
      booking.therapistId.toString() === userId ||
      ['admin', 'counselor'].includes(req.user.role);
    if (!canCancel) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    if (booking.status === 'completed') {
      return res.status(400).json({ success: false, message: 'Cannot cancel completed booking' });
    }

    booking.status = 'cancelled';
    booking.notes = reason || 'Cancelled';
    await booking.save();

    try {
      const io = getIO();
      io.to(`user_${booking.patientId}`).emit('booking_notification', booking);
      io.to(`user_${booking.therapistId}`).emit('booking_notification', booking);
    } catch (e) {}

    res.status(200).json({ success: true, message: 'Booking cancelled' });
  } catch (error) {
    console.error('Error cancelling booking:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Counselor respond (accept / reschedule / reject)
 */
exports.counselorRespondBooking = async (req, res) => {
  try {
    const { bookingId } = req.params;
    const { action, proposedDate, proposedTime, message } = req.body;
    const booking = await Booking.findById(bookingId);
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const userId = req.user.id;
    if (booking.therapistId.toString() !== userId) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    if (action === 'accept') {
      booking.status = 'accepted';
    } else if (action === 'reschedule') {
      booking.status = 'rescheduled';
      booking.proposedDate = proposedDate;
      booking.proposedTime = proposedTime;
      booking.counselorMessage = message || '';
    } else if (action === 'reject') {
      booking.status = 'rejected';
      booking.rejectionMessage = message || 'Counselor unavailable';
    }
    await booking.save();

    const updated = await Booking.findById(bookingId)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience');

    try {
      const io = getIO();
      io.to(`user_${updated.patientId._id}`).emit('booking_notification', updated);
      io.to(`user_${updated.therapistId._id}`).emit('booking_notification', updated);
    } catch (e) {}

    res.json({ success: true, booking: updated });
  } catch (error) {
    console.error('Error responding to booking:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Student accept reschedule
 */
exports.studentAcceptReschedule = async (req, res) => {
  try {
    const { bookingId } = req.params;
    const booking = await Booking.findById(bookingId);
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const userId = req.user.id;
    if (booking.patientId.toString() !== userId) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    booking.status = 'confirmed';
    booking.appointmentDate = booking.proposedDate;
    booking.appointmentTime = booking.proposedTime;
    booking.proposedDate = null;
    booking.proposedTime = null;
    booking.counselorMessage = '';
    await booking.save();

    const updated = await Booking.findById(bookingId)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience');

    try {
      const io = getIO();
      io.to(`user_${updated.patientId._id}`).emit('booking_notification', updated);
      io.to(`user_${updated.therapistId._id}`).emit('booking_notification', updated);
    } catch (e) {}

    res.json({ success: true, booking: updated });
  } catch (error) {
    console.error('Error accepting reschedule:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Direct reschedule booking (NEW)
 */
exports.rescheduleBooking = async (req, res) => {
  try {
    const { bookingId } = req.params;
    const { appointmentDate, appointmentTime } = req.body;

    const booking = await Booking.findById(bookingId);
    if (!booking) {
      return res.status(404).json({ success: false, message: 'Booking not found' });
    }

    const userId = req.user.id;
    if (
      booking.patientId.toString() !== userId &&
      booking.therapistId.toString() !== userId &&
      !['admin', 'counselor'].includes(req.user.role)
    ) {
      return res.status(403).json({ success: false, message: 'Access denied' });
    }

    booking.status = 'rescheduled';
    booking.appointmentDate = new Date(appointmentDate);
    booking.appointmentTime = appointmentTime;
    await booking.save();

    const updated = await Booking.findById(bookingId)
      .populate('patientId', 'name email phone')
      .populate('therapistId', 'name email specialization experience');

    try {
      const io = getIO();
      io.to(`user_${updated.patientId._id}`).emit('booking_notification', updated);
      io.to(`user_${updated.therapistId._id}`).emit('booking_notification', updated);
    } catch (e) {}

    res.status(200).json({
      success: true,
      message: 'Booking rescheduled successfully',
      booking: updated
    });
  } catch (error) {
    console.error('Error rescheduling booking:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Get therapist availability
 */
exports.getTherapistAvailability = async (req, res) => {
  try {
    const { therapistId } = req.params;
    const { date } = req.query;

    const therapist = await User.findById(therapistId);
    if (!therapist || !['therapist', 'counselor'].includes(therapist.role)) {
      return res.status(404).json({ success: false, message: 'Therapist not found' });
    }

    const queryDate = date ? new Date(date) : new Date();
    const start = new Date(queryDate.setHours(0, 0, 0, 0));
    const end = new Date(queryDate.setHours(23, 59, 59, 999));

    const booked = await Booking.find({
      therapistId,
      appointmentDate: { $gte: start, $lt: end },
      status: { $in: ['scheduled', 'confirmed'] }
    }).select('appointmentTime duration');

    const slots = [];
    for (let hour = 9; hour < 17; hour++) {
      const time = `${hour.toString().padStart(2, '0')}:00`;
      const available = !booked.some(b => b.appointmentTime === time);
      slots.push({ time, available });
    }

    res.status(200).json({
      success: true,
      therapist: { id: therapist._id, name: therapist.name },
      date: start.toISOString().split('T')[0],
      timeSlots: slots
    });
  } catch (error) {
    console.error('Error fetching availability:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};

/**
 * Booking stats
 */
exports.getBookingStats = async (req, res) => {
  try {
    const userId = req.user.id;
    const { startDate, endDate } = req.query;

    const match = {};
    if (req.user.role === 'student') match.patientId = mongoose.Types.ObjectId(userId);
    else if (['therapist', 'counselor'].includes(req.user.role))
      match.therapistId = mongoose.Types.ObjectId(userId);
    if (startDate && endDate) {
      match.appointmentDate = {
        $gte: new Date(startDate),
        $lte: new Date(endDate)
      };
    }

    const stats = await Booking.aggregate([
      { $match: match },
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 },
          totalRevenue: { $sum: '$price' }
        }
      }
    ]);

    const total = await Booking.countDocuments(match);

    res.status(200).json({
      success: true,
      stats: {
        totalBookings: total,
        statusBreakdown: stats,
        totalRevenue: stats.reduce((sum, s) => sum + (s.totalRevenue || 0), 0)
      }
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ success: false, message: 'Internal server error', error: error.message });
  }
};
