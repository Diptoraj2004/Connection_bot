const User = require('../models/User');

exports.getAll = async (req, res) => {
  // Filter by role from query param (e.g. /api/users?role=counselor or therapist)
  const filter = {};
  if (req.query.role) {
    filter.role = req.query.role;
  }
  // Return all users matching the role (or all if none specified), hiding password
  const users = await User.find(filter).select('-password');
  res.json({ success: true, users });
};

exports.updateProfile = async (req, res) => {
  const user = await User.findById(req.user.id);
  if (!user) return res.status(404).json({ message: 'Not found' });
  const fields = ['name', 'phone', 'university', 'year', 'specialization', 'experience'];
  fields.forEach(f => { if (req.body[f] !== undefined) user[f] = req.body[f]; });
  await user.save();
  res.json({ success: true, user });
};