// middleware/auth.js
const jwt = require('jsonwebtoken');
const User = require('../models/User');

exports.protect = async (req,res,next) => {
  const authHeader = req.headers.authorization;
  let token = null;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    token = authHeader.split(' ')[1];
  }
  if (!token) return res.status(401).json({message:'Not authorized: no token'});
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = await User.findById(decoded.id).select('-password');
    if (!req.user) return res.status(401).json({message:'User not found'});
    next();
  } catch (err) {
    res.status(401).json({message:'Token invalid'});
  }
};

exports.authorize = (...roles) => (req,res,next) => {
  if (!req.user || !roles.includes(req.user.role)) {
    return res.status(403).json({message:`Role ${req.user?.role || 'unknown'} not allowed`});
  }
  next();
};
