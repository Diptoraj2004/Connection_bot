// services/bookingScheduler.js
const cron = require('node-cron');
const Booking = require('../models/Booking');
const NotificationService = require('./notificationService');

class BookingScheduler {
  static init() {
    // Every 15 minutes: check for bookings that start ~1 hour from now (and haven't been reminded)
    cron.schedule('*/15 * * * *', async () => {
      try {
        const now = new Date();
        const oneHourFromNow = new Date(now.getTime() + 60 * 60 * 1000);
        const fifteenMinutesAfterOneHour = new Date(now.getTime() + 75 * 60 * 1000);

        const upcomingBookings = await Booking.find({
          status: { $in: ['scheduled', 'confirmed'] },
          reminderSent: false,
          appointmentDate: {
            $gte: oneHourFromNow,
            $lte: fifteenMinutesAfterOneHour
          }
        }).populate('patientId', 'name email').populate('therapistId', 'name email');

        for (const booking of upcomingBookings) {
          try {
            await NotificationService.sendBookingReminder(booking, booking.patientId, booking.therapistId);
            booking.reminderSent = true;
            await booking.save();
          } catch (e) {
            console.error('Error sending reminder for booking', booking._id, e);
          }
        }

        if (upcomingBookings.length > 0) {
          console.log(`Sent ${upcomingBookings.length} booking reminders`);
        }
      } catch (error) {
        console.error('Error in booking reminder scheduler:', error);
      }
    });

    // Every hour at :00 - auto-complete sessions whose appointmentDate is more than 1 hour ago
    cron.schedule('0 * * * *', async () => {
      try {
        const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
        const expiredBookings = await Booking.find({
          status: 'confirmed',
          appointmentDate: { $lt: oneHourAgo }
        });

        for (const booking of expiredBookings) {
          booking.status = 'completed';
          await booking.save();
        }

        if (expiredBookings.length > 0) {
          console.log(`Auto-completed ${expiredBookings.length} expired bookings`);
        }
      } catch (error) {
        console.error('Error in booking completion scheduler:', error);
      }
    });
  }
}

module.exports = BookingScheduler;
