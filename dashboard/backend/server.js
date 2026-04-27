// server.js
require('dotenv').config();
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const http = require('http');

const connectDB = require('./config/db');
const errorHandler = require('./middleware/errorHandler');

const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const bookingRoutes = require('./routes/bookingRoutes');

const { initializeSocket } = require('./utils/socketManager');
const BookingScheduler = require('./services/bookingScheduler');

const app = express();
const server = http.createServer(app);

// --- Middleware ---
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:3000",
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}));
app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 1000,
  message: { error: 'Too many requests from this IP', retryAfter: '15 minutes' },
  standardHeaders: true,
  legacyHeaders: false
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// --- Database ---
connectDB();

// --- Routes ---
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/bookings', bookingRoutes);

// --- Health check ---
app.get('/', (req, res) => {
  res.json({
    message: 'API Running 🟢',
    timestamp: new Date().toISOString(),
    env: process.env.NODE_ENV || 'development'
  });
});

// --- Socket.IO ---
initializeSocket(server);

// --- Booking Scheduler ---
BookingScheduler.init();

// --- Error Handler (last) ---
app.use(errorHandler);

// --- Start Server ---
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
});

module.exports = { app, server };
