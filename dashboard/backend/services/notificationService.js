// services/notificationService.js
const nodemailer = require('nodemailer');
const { getIO } = require('../utils/socketManager');

const transporter = nodemailer.createTransport({
  service: process.env.EMAIL_SERVICE || 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});

class NotificationService {
  static async sendBookingConfirmation(booking, patient, therapist) {
    if (!patient || !patient.email) return;
    const mailOptions = {
      from: process.env.EMAIL_USER,
      to: patient.email,
      subject: 'Booking Confirmation - MindCare',
      html: `
        <h2>Booking Confirmation</h2>
        <p>Dear ${patient.name},</p>
        <p>Your booking has been confirmed with the following details:</p>
        <ul>
          <li><strong>Therapist:</strong> ${therapist.name}</li>
          <li><strong>Date:</strong> ${new Date(booking.appointmentDate).toDateString()}</li>
          <li><strong>Time:</strong> ${booking.appointmentTime}</li>
          <li><strong>Session Type:</strong> ${booking.sessionType}</li>
          <li><strong>Duration:</strong> ${booking.duration} minutes</li>
        </ul>
        <p>Meeting Link: <a href="${booking.meetingLink}">${booking.meetingLink}</a></p>
        <p>Thank you for choosing MindCare!</p>
      `
    };

    try {
      await transporter.sendMail(mailOptions);
      console.log('Booking confirmation email sent to', patient.email);
    } catch (error) {
      console.error('Error sending booking confirmation email:', error);
    }
  }

  static async sendRealtimeNotification(userId, type, message, data = {}) {
    try {
      const io = getIO();
      io.to(`user_${userId}`).emit('notification', {
        type,
        message,
        data,
        timestamp: new Date()
      });
    } catch (error) {
      console.error('Error sending real-time notification:', error);
    }
  }

  static async sendBookingReminder(booking, patient, therapist) {
    if (!patient || !patient.email) return;
    const mailOptions = {
      from: process.env.EMAIL_USER,
      to: patient.email,
      subject: 'Appointment Reminder - MindCare',
      html: `
        <h2>Appointment Reminder</h2>
        <p>Dear ${patient.name},</p>
        <p>This is a reminder of your upcoming appointment:</p>
        <ul>
          <li><strong>Therapist:</strong> ${therapist.name}</li>
          <li><strong>Date:</strong> ${new Date(booking.appointmentDate).toDateString()}</li>
          <li><strong>Time:</strong> ${booking.appointmentTime}</li>
        </ul>
        <p>Meeting Link: <a href="${booking.meetingLink}">Join Session</a></p>
        <p>Please arrive 5 minutes early.</p>
      `
    };

    try {
      await transporter.sendMail(mailOptions);
      console.log('Reminder email sent to', patient.email);
    } catch (error) {
      console.error('Error sending reminder email:', error);
    }

    // realtime
    try {
      this.sendRealtimeNotification(
        patient._id,
        'booking_reminder',
        `Reminder: You have an appointment with ${therapist.name} in ~1 hour`,
        { bookingId: booking._id }
      );
    } catch (error) {
      console.error('Realtime reminder failed:', error);
    }
  }
}

module.exports = NotificationService;
