// utils/socketManager.js
const socketIo = require('socket.io');

let io = null;

function initializeSocket(server) {
  if (io) return io; // already initialized
  io = socketIo(server, {
    cors: {
      origin: process.env.FRONTEND_URL || "http://localhost:3000",
      methods: ["GET", "POST"],
      credentials: true
    }
  });

  io.on('connection', (socket) => {
    console.log('Socket connected:', socket.id);

    socket.on('join', (userId) => {
      if (userId) {
        socket.join(`user_${userId}`);
      }
    });

    socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', socket.id, reason);
    });

    // generic booking_update from client -> broadcast to involved parties
    socket.on('booking_update', (data) => {
      if (data && data.patientId) {
        io.to(`user_${data.patientId}`).emit('booking_notification', data);
      }
      if (data && data.therapistId) {
        io.to(`user_${data.therapistId}`).emit('booking_notification', data);
      }
    });
  });

  return io;
}

function getIO() {
  if (!io) {
    throw new Error('Socket.io not initialized. Call initializeSocket(server) first.');
  }
  return io;
}

module.exports = { initializeSocket, getIO };
