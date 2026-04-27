const express = require('express');
const { getAll, updateProfile } = require('../controllers/userController');
const { protect } = require('../middleware/auth');
const router = express.Router();

// Allow all authenticated users to fetch user lists (with role filter)
router.get('/', protect, getAll);
router.put('/profile', protect, updateProfile);

module.exports = router;