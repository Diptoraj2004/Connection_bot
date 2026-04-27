// models/Booking.js
const mongoose = require('mongoose');

const bookingSchema = new mongoose.Schema({
  patientId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  therapistId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  sessionType: {
    type: String,
    enum: ['individual', 'group', 'emergency', 'follow-up'],
    required: true
  },
  appointmentDate: {
    type: Date,
    required: true
  },
  appointmentTime: {
    type: String,
    required: true
  },
  duration: {
    type: Number,
    default: 50, // minutes
    required: true
  },
  // Extra booking fields for this flow:
status: {
  type: String,
  enum: ['pending', 'accepted', 'rejected', 'rescheduled', 'confirmed', 'scheduled', 'completed', 'cancelled'],
  default: 'pending'
},


  meetingLink: {
    type: String,
    default: null
  },
  notes: {
    type: String,
    default: ''
  },
  symptoms: [{
    type: String
  }],
  priority: {
    type: String,
    enum: ['low', 'medium', 'high', 'urgent'],
    default: 'medium'
  },
  price: {
    type: Number,
    required: true
  },
  paymentStatus: {
    type: String,
    enum: ['pending', 'paid', 'failed', 'refunded'],
    default: 'pending'
  },
  reminderSent: {
    type: Boolean,
    default: false
  },
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// Indexes
bookingSchema.index({ patientId: 1, therapistId: 1, appointmentDate: 1 });
bookingSchema.index({ status: 1 });

bookingSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

module.exports = mongoose.model('Booking', bookingSchema);
