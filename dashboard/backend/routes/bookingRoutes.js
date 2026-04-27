// routes/bookingRoutes.js
const express = require('express');
const { body } = require('express-validator');
const bookingController = require('../controllers/bookingController');
const { protect, authorize } = require('../middleware/auth');

const router = express.Router();

const bookingValidation = [
  body('therapistId').isMongoId().withMessage('Invalid therapist ID'),
  body('sessionType')
    .isIn(['individual', 'group', 'emergency', 'follow-up'])
    .withMessage('Invalid session type'),
  body('appointmentDate')
    .isISO8601()
    .withMessage('Invalid appointment date'),
  body('appointmentTime')
    .matches(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/)
    .withMessage('Invalid appointment time format (HH:MM)'),
  body('duration')
    .optional()
    .isInt({ min: 15, max: 120 })
    .withMessage('Duration must be between 15 and 120 minutes'),
  body('priority')
    .optional()
    .isIn(['low', 'medium', 'high', 'urgent'])
    .withMessage('Invalid priority level')
];

// Create booking (students only)
router.post(
  '/',
  protect,
  authorize('student','counselor'),
  bookingValidation,
  bookingController.createBooking
);

// Therapist availability
router.get(
  '/therapist/:therapistId/availability',
  protect,
  bookingController.getTherapistAvailability
);

// Booking stats (therapist or admin only)
router.get(
  '/stats/overview',
  protect,
  authorize('therapist', 'admin'),
  bookingController.getBookingStats
);

// Get all bookings for logged-in user
router.get('/', protect, bookingController.getUserBookings);

// Get booking by ID
router.get('/:bookingId', protect, bookingController.getBookingById);

// Update booking status (for standard update only)
router.put(
  '/:bookingId/status',
  protect,
  [
    body('status').isIn([
      'scheduled',
      'confirmed',
      'completed',
      'cancelled',
      'rescheduled',
      'pending',
      'accepted',
      'rejected'
    ])
  ],
  bookingController.updateBookingStatus
);

// Cancel booking
router.put('/:bookingId/cancel', protect, bookingController.cancelBooking);

// Reschedule booking (old flow, can keep if needed)
router.put(
  '/:bookingId/reschedule',
  protect,
  [
    body('appointmentDate')
      .isISO8601()
      .withMessage('Invalid appointment date'),
    body('appointmentTime')
      .matches(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/)
      .withMessage('Invalid appointment time format (HH:MM)')
  ],
  bookingController.rescheduleBooking
);

// Counselor respond (accept/reject/reschedule)
router.post(
  '/:bookingId/respond',
  protect,
  authorize('therapist', 'counselor'),
  bookingController.counselorRespondBooking
);

// Student accept reschedule
router.post(
  '/:bookingId/accept-reschedule',
  protect,
  authorize('student'),
  bookingController.studentAcceptReschedule
);

module.exports = router;
